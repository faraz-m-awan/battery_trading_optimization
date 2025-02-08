import streamlit as st
import pyomo.environ as pyo
from pyomo.environ import value
import pandas as pd
import matplotlib.pyplot as plt

class BatteryOptimizer:
    def __init__(self, data, day=38, power=100, capacity=100,
                 charging_efficiency=0.85, discharging_efficiency=1.0,
                 daily_cycles=2.0, initial_soc=25):
        """
        Initialize with a dataset (DataFrame or file path) and battery parameters.
        The dataset is assumed to have two columns: 'day-ahead' and 'intra-day',
        one row per half-hour settlement period.
        """
        if isinstance(data, pd.DataFrame):
            self.data_df = data
        else:
            self.data_df = pd.read_csv(data)
        self.day = day
        self.power = power
        self.capacity = capacity
        self.charging_efficiency = charging_efficiency
        self.discharging_efficiency = discharging_efficiency
        self.daily_cycles = daily_cycles
        self.initial_soc = initial_soc

        # Extract prices for the selected day (48 settlement periods)
        start_idx = day * 48
        end_idx = (day + 1) * 48
        self.da_prices = self.data_df["day-ahead"].values[start_idx:end_idx]
        self.id_prices = self.data_df["intra-day"].values[start_idx:end_idx]
        self.time_periods = list(range(len(self.da_prices)))  # 0, 1, ..., 47

    def optimize_day_ahead(self):
        """
        Build and solve the day-ahead model.
        The decision variable v_da is defined for each half-hour, but an additional
        constraint forces the value to be identical for both settlement periods in each hour.
        """
        model = pyo.ConcreteModel("DayAheadOptimiser")
        model.time = pyo.Set(initialize=self.time_periods)

        # Decision variables: flows (charge/discharge), net traded volume, and SOC
        model.flow_in_da = pyo.Var(model.time, within=pyo.NonNegativeReals)
        model.flow_out_da = pyo.Var(model.time, within=pyo.NonNegativeReals)
        model.v_da = pyo.Var(model.time)  # net volume traded in day-ahead market
        model.soc = pyo.Var(model.time, within=pyo.NonNegativeReals)

        # Link: net trade equals discharge minus charge.
        def energy_rule_da(model, t):
            return model.v_da[t] == model.flow_out_da[t] - model.flow_in_da[t]
        model.energy_eqn_da = pyo.Constraint(model.time, rule=energy_rule_da)

        # Power limits for day-ahead trades.
        model.up_bound_eqn_da = pyo.Constraint(model.time, rule=lambda m, t: m.flow_out_da[t] <= self.power)
        model.low_bound_eqn_da = pyo.Constraint(model.time, rule=lambda m, t: m.flow_in_da[t] <= self.power)

        # SOC limits.
        model.soc_bound_da = pyo.Constraint(model.time, rule=lambda m, t: m.soc[t] <= self.capacity)

        # Battery cycling limit (total discharge cannot exceed a multiple of capacity).
        def cycling_limit_da(model):
            return pyo.quicksum(model.flow_out_da[t] for t in model.time) <= self.daily_cycles * self.capacity
        model.cycling_limit_da = pyo.Constraint(rule=cycling_limit_da)

        # SOC dynamics: initial condition and update rule.
        def soc_rule_da(model, t):
            if t == 0:
                return model.soc[t] == self.initial_soc
            else:
                return model.soc[t] == model.soc[t-1] \
                    - model.flow_out_da[t-1] * self.discharging_efficiency \
                    + model.flow_in_da[t-1] * self.charging_efficiency
        model.soc_rule_da = pyo.Constraint(model.time, rule=soc_rule_da)

        # Final SOC must equal initial SOC.
        def final_soc_da(model):
            last = max(model.time)
            return model.soc[last] == self.initial_soc
        model.final_soc_da = pyo.Constraint(rule=final_soc_da)

        # Hourly consistency: For each hour, both half-hourly settlements have the same day-ahead trade.
        def hourly_consistency(model, h):
            t1 = 2 * h
            t2 = 2 * h + 1
            if t2 in model.time:
                return model.v_da[t1] == model.v_da[t2]
            else:
                return pyo.Constraint.Skip
        model.hourly_consistency = pyo.Constraint(range(len(self.da_prices) // 2), rule=hourly_consistency)

        # Objective: maximize day-ahead revenue.
        def objective_da(model):
            return pyo.quicksum(model.v_da[t] * self.da_prices[t] for t in model.time)
        model.obj_da = pyo.Objective(rule=objective_da, sense=pyo.maximize)

        # Solve the day-ahead model.
        solver = pyo.SolverFactory("appsi_highs")
        self.da_results = solver.solve(model)
        
        # Save the results.
        self.day_ahead_model = model
        self.v_da_sol = [pyo.value(model.v_da[t]) for t in model.time]
        self.flow_in_da_sol = [pyo.value(model.flow_in_da[t]) for t in model.time]
        self.flow_out_da_sol = [pyo.value(model.flow_out_da[t]) for t in model.time]
        self.soc_da_sol = [pyo.value(model.soc[t]) for t in model.time]
        self.da_obj_val = pyo.value(model.obj_da)
        return model

    def optimize_intra_day(self):
        """
        Build and solve the intra-day model.
        The day-ahead trades (and their corresponding flows) are fixed from the previous step.
        The decision variables in this stage (flow_in_id, flow_out_id, and v_id) represent additional
        intra-day trades which, when added to the day-ahead positions, affect the battery SOC.
        """
        # Ensure that day-ahead optimization has been completed.
        if not hasattr(self, 'v_da_sol'):
            raise Exception("Run day-ahead optimization before intra-day optimization.")

        model = pyo.ConcreteModel("IntraDayOptimiser")
        model.time = pyo.Set(initialize=self.time_periods)

        # Decision variables for intra-day trading.
        model.flow_in_id = pyo.Var(model.time, within=pyo.NonNegativeReals)
        model.flow_out_id = pyo.Var(model.time, within=pyo.NonNegativeReals)
        model.v_id = pyo.Var(model.time)  # net volume traded in the intra-day market
        model.soc_total = pyo.Var(model.time, within=pyo.NonNegativeReals)

        # Link: intra-day net trade equals discharge minus charge.
        def energy_rule_id(model, t):
            return model.v_id[t] == model.flow_out_id[t] - model.flow_in_id[t]
        model.energy_eqn_id = pyo.Constraint(model.time, rule=energy_rule_id)

        # Combined power limits: the sum of day-ahead and intra-day flows must not exceed the battery power.
        def upper_bound_total(model, t):
            return self.flow_out_da_sol[t] + model.flow_out_id[t] <= self.power
        def lower_bound_total(model, t):
            return self.flow_in_da_sol[t] + model.flow_in_id[t] <= self.power
        model.up_bound_total = pyo.Constraint(model.time, rule=upper_bound_total)
        model.low_bound_total = pyo.Constraint(model.time, rule=lower_bound_total)

        # SOC upper bound for the combined operation.
        model.soc_bound_total = pyo.Constraint(model.time, rule=lambda m, t: m.soc_total[t] <= self.capacity)

        # Cycling limit: the total discharge (day-ahead + intra-day) is bounded.
        def cycling_limit_total(model):
            return pyo.quicksum(self.flow_out_da_sol[t] + model.flow_out_id[t] for t in model.time) <= self.daily_cycles * self.capacity
        model.cycling_limit_total = pyo.Constraint(rule=cycling_limit_total)

        # SOC dynamics for the combined (day-ahead + intra-day) operation.
        def soc_rule_total(model, t):
            if t == 0:
                return model.soc_total[t] == self.initial_soc
            else:
                return model.soc_total[t] == model.soc_total[t-1] \
                    - (self.flow_out_da_sol[t-1] + model.flow_out_id[t-1]) * self.discharging_efficiency \
                    + (self.flow_in_da_sol[t-1] + model.flow_in_id[t-1]) * self.charging_efficiency
        model.soc_rule_total = pyo.Constraint(model.time, rule=soc_rule_total)

        # Final SOC must equal initial SOC.
        def final_soc_total(model):
            last = max(model.time)
            return model.soc_total[last] == self.initial_soc
        model.final_soc_total = pyo.Constraint(rule=final_soc_total)

        # Objective: maximize intra-day revenue.
        def objective_id(model):
            return pyo.quicksum(model.v_id[t] * self.id_prices[t] for t in model.time)
        model.obj_id = pyo.Objective(rule=objective_id, sense=pyo.maximize)

        # Solve the intra-day model.
        solver = pyo.SolverFactory("appsi_highs")
        self.id_results = solver.solve(model)
        
        # Save the intra-day solution.
        self.intraday_model = model
        self.v_id_sol = [pyo.value(model.v_id[t]) for t in model.time]
        self.flow_in_id_sol = [pyo.value(model.flow_in_id[t]) for t in model.time]
        self.flow_out_id_sol = [pyo.value(model.flow_out_id[t]) for t in model.time]
        self.soc_total_sol = [pyo.value(model.soc_total[t]) for t in model.time]
        self.id_obj_val = pyo.value(model.obj_id)
        return model

    def get_results(self):
        """
        Returns a DataFrame with the following columns for each settlement period:
         - DayAhead Trade (vol)
         - IntraDay Trade (vol)
         - Prices for each market
         - Cashflows (volume times price) for each market
         - Total cashflow (sum)
         - SOC from the day-ahead stage and the combined (total) SOC.
        """
        # Compute cashflows per settlement period.
        da_cashflows = [self.v_da_sol[t] * self.da_prices[t] for t in self.time_periods]
        id_cashflows = [self.v_id_sol[t] * self.id_prices[t] for t in self.time_periods]
        total_cashflows = [da_cashflows[t] + id_cashflows[t] for t in self.time_periods]

        results_df = pd.DataFrame({
            "Settlement Period": self.time_periods,
            "DayAhead Trade (vol)": self.v_da_sol,
            "IntraDay Trade (vol)": self.v_id_sol,
            "DayAhead Price": self.da_prices,
            "IntraDay Price": self.id_prices,
            "DayAhead Cashflow": da_cashflows,
            "IntraDay Cashflow": id_cashflows,
            "Total Cashflow": total_cashflows,
            "SOC after DayAhead": self.soc_da_sol,
            "SOC Total": self.soc_total_sol if hasattr(self, 'soc_total_sol') else None
        })
        return results_df, self.da_obj_val, self.id_obj_val

def main():
    st.title("Battery Revenue Optimization: Day-Ahead & Intra-Day Trading")
    
    st.sidebar.header("Optimization Parameters")
    day = st.sidebar.number_input("Day (0-indexed)", min_value=0, value=38, step=1)
    power = st.sidebar.number_input("Power [MW]", min_value=0.0, value=100.0, step=1.0)
    capacity = st.sidebar.number_input("Capacity [MWh]", min_value=0.0, value=100.0, step=1.0)
    charging_eff = st.sidebar.slider("Charging Efficiency", min_value=0.0, max_value=1.0, value=0.85)
    discharging_eff = st.sidebar.slider("Discharging Efficiency", min_value=0.0, max_value=1.0, value=1.0)
    daily_cycles = st.sidebar.number_input("Daily Cycles", min_value=0.0, value=2.0, step=0.1)
    initial_soc = st.sidebar.number_input("Initial SOC", min_value=0.0, value=25.0, step=1.0)
    
    st.sidebar.header("Dataset")
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        data_df = pd.read_csv(uploaded_file)
    else:
        try:
            data_df = pd.read_csv("dataset.csv")
        except Exception as e:
            st.error("No dataset provided and default 'dataset.csv' not found!")
            return

    # Create an instance of BatteryOptimizer.
    optimizer = BatteryOptimizer(
        data=data_df,
        day=day,
        power=power,
        capacity=capacity,
        charging_efficiency=charging_eff,
        discharging_efficiency=discharging_eff,
        daily_cycles=daily_cycles,
        initial_soc=initial_soc
    )
    
    st.write("**Step 1: Running Day-Ahead Optimization...**")
    optimizer.optimize_day_ahead()
    st.write("Day-Ahead optimization complete.")
    st.write("**Day-Ahead Total Revenue:**", optimizer.da_obj_val)
    
    st.write("**Step 2: Running Intra-Day Optimization...**")
    optimizer.optimize_intra_day()
    st.write("Intra-Day optimization complete.")
    st.write("**Intra-Day Additional Revenue:**", optimizer.id_obj_val)
    
    # Retrieve and display results.
    results_df, da_revenue, id_revenue = optimizer.get_results()
    st.subheader("Detailed Results per Settlement Period")
    st.dataframe(results_df)
    
    # Chart 1: Day-Ahead Trading Results
    st.subheader("Day-Ahead Trading Chart")
    fig_da, ax_da = plt.subplots(figsize=(10, 6))
    ax_da.plot(results_df["Settlement Period"], results_df["DayAhead Trade (vol)"],
               label="Day-Ahead Trade Volume", marker="o", color="blue")
    ax_da.set_xlabel("Settlement Period")
    ax_da.set_ylabel("Trade Volume", color="blue")
    ax_da.tick_params(axis="y", labelcolor="blue")
    ax_da.legend(loc="upper left")
    
    ax_da_sec = ax_da.twinx()
    ax_da_sec.plot(results_df["Settlement Period"], results_df["DayAhead Cashflow"],
                   label="Day-Ahead Cashflow", marker="o", color="red")
    ax_da_sec.set_ylabel("Cashflow", color="red")
    ax_da_sec.tick_params(axis="y", labelcolor="red")
    ax_da_sec.legend(loc="upper right")
    st.pyplot(fig_da)
    
    # Chart 2: Intra-Day Trading Results
    st.subheader("Intra-Day Trading Chart")
    fig_id, ax_id = plt.subplots(figsize=(10, 6))
    ax_id.plot(results_df["Settlement Period"], results_df["IntraDay Trade (vol)"],
               label="Intra-Day Trade Volume", marker="o", color="green")
    ax_id.set_xlabel("Settlement Period")
    ax_id.set_ylabel("Trade Volume", color="green")
    ax_id.tick_params(axis="y", labelcolor="green")
    ax_id.legend(loc="upper left")
    
    ax_id_sec = ax_id.twinx()
    ax_id_sec.plot(results_df["Settlement Period"], results_df["IntraDay Cashflow"],
                   label="Intra-Day Cashflow", marker="o", color="orange")
    ax_id_sec.set_ylabel("Cashflow", color="orange")
    ax_id_sec.tick_params(axis="y", labelcolor="orange")
    ax_id_sec.legend(loc="upper right")
    st.pyplot(fig_id)

if __name__ == "__main__":
    main()
