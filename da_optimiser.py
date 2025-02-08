import streamlit as st
import pyomo.environ as pyo
from pyomo.environ import value
import pandas as pd
import matplotlib.pyplot as plt

class EnergyOptimizer:
    def __init__(self, data, day=38, power=100, capacity=100, 
                 charging_efficiency=0.85, discharging_efficiency=1.0, 
                 daily_cycles=2.0, initial_soc=25):
        """
        Initialize the optimizer with data and parameters.
        Accepts either a DataFrame or a file path.
        """
        # Allow flexibility: if data is a DataFrame, use it directly; otherwise read from file.
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
        
        # Extract the prices for the given day (assuming 48 time steps per day)
        self.prices = self.data_df["day-ahead"].values[day * 48:(day + 1) * 48]

    def build_model(self):
        """Builds the Pyomo model with variables, objective, and constraints."""
        self.model = pyo.ConcreteModel("Optimiser")
        # Create a time set from 0 to (number of timesteps - 1)
        time_index = list(range(len(self.prices)))
        self.model.time = pyo.Set(initialize=time_index)
        
        # Define decision variables
        self.model.volume_traded = pyo.Var(self.model.time)
        self.model.flow_in = pyo.Var(self.model.time, within=pyo.NonNegativeReals)
        self.model.flow_out = pyo.Var(self.model.time, within=pyo.NonNegativeReals)
        self.model.soc = pyo.Var(self.model.time, within=pyo.NonNegativeReals)

        # Objective: maximize cash flow (profit)
        def cash_flow_rule(model):
            return pyo.quicksum(model.volume_traded[t] * self.prices[t] for t in model.time)
        self.model.profit = pyo.Objective(rule=cash_flow_rule, sense=pyo.maximize)

        # Constraint: Upper bound on discharge (flow_out)
        def upper_bound_rule(model, t):
            return model.flow_out[t] <= self.power

        # Constraint: Lower bound on charge (flow_in)
        def lower_bound_rule(model, t):
            return model.flow_in[t] <= self.power

        # Constraint: Limit on state-of-charge (SOC)
        def soc_bound_rule(model, t):
            return model.soc[t] <= self.capacity

        # Constraint: Final SOC must return to the initial level.
        def final_soc_bound_rule(model):
            last = max(model.time)
            return model.soc[last] == self.initial_soc

        # Constraint: Energy balance – traded volume equals net flow.
        def energy_rule(model, t):
            return model.volume_traded[t] == model.flow_out[t] - model.flow_in[t]

        # Constraint: Limit total discharge to available cycles
        def cycling_limit_rule(model):
            return pyo.quicksum(model.flow_out[t] for t in model.time) <= self.daily_cycles * self.capacity

        # Constraint: SOC dynamics
        def soc_rule(model, t):
            if t == 0:
                return model.soc[t] == self.initial_soc
            else:
                return model.soc[t] == model.soc[t - 1] \
                    - model.flow_out[t - 1] * self.discharging_efficiency \
                    + model.flow_in[t - 1] * self.charging_efficiency

        # Constraint: No free discharge at the end of the day.
        def final_export_rule(model):
            last = max(model.time)
            return model.volume_traded[last] == 0

        # Add all constraints to the model
        self.model.up_bound_eqn = pyo.Constraint(self.model.time, rule=upper_bound_rule)
        self.model.low_bound_eqn = pyo.Constraint(self.model.time, rule=lower_bound_rule)
        self.model.soc_eqn = pyo.Constraint(self.model.time, rule=soc_bound_rule)
        self.model.sum_eqn = pyo.Constraint(rule=cycling_limit_rule)
        self.model.final_soc_eqn = pyo.Constraint(rule=final_soc_bound_rule)
        self.model.sum_export_eqn = pyo.Constraint(rule=final_export_rule)
        self.model.energy_eqn = pyo.Constraint(self.model.time, rule=energy_rule)
        self.model.soc_rule_eqn = pyo.Constraint(self.model.time, rule=soc_rule)

    def solve_model(self):
        """Solves the optimization model using the 'appsi_highs' solver."""
        opt = pyo.SolverFactory("appsi_highs")
        self.results = opt.solve(self.model)
        self.obj_val = pyo.value(self.model.profit)
        return self.results

    def get_results(self):
        """Extracts the volume traded and state-of-charge (SOC) from the solved model."""
        volumes = [pyo.value(self.model.volume_traded[t]) for t in self.model.time]
        soc = [pyo.value(self.model.soc[t]) for t in self.model.time]
        return volumes, soc


def main():
    st.title("Energy Optimization with Pyomo")
    
    st.sidebar.header("Optimization Parameters")
    day = st.sidebar.number_input("Day", min_value=0, value=38, step=1)
    power = st.sidebar.number_input("Power", min_value=0.0, value=100.0, step=1.0)
    capacity = st.sidebar.number_input("Capacity", min_value=0.0, value=100.0, step=1.0)
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
            data_df = pd.read_csv("dataset1.csv")
        except Exception as e:
            st.error("No dataset provided and default 'dataset.csv' not found!")
            return

    # Create an instance of the optimizer with the given parameters
    optimizer = EnergyOptimizer(
        data=data_df,
        day=day,
        power=power,
        capacity=capacity,
        charging_efficiency=charging_eff,
        discharging_efficiency=discharging_eff,
        daily_cycles=daily_cycles,
        initial_soc=initial_soc
    )
    
    st.write("**Building the optimization model...**")
    optimizer.build_model()
    
    st.write("**Solving the model...**")
    results = optimizer.solve_model()
    
    st.subheader("Solver Results")
    st.text(results)
    st.write("**Total Profit:**", optimizer.obj_val)
    
    # Extract results from the model
    volumes, soc = optimizer.get_results()
    
    # Prepare data for plotting
    df_plot = pd.DataFrame({
        "Volume Traded": volumes,
        "Prices": optimizer.prices,
        "SOC": soc
    })
    
    st.subheader("Optimization Results Plot")
    st.line_chart(df_plot)
    
    st.subheader("Detailed Data")
    st.dataframe(df_plot)

if __name__ == "__main__":
    main()
