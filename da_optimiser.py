import pyomo.environ as pyo
from pyomo.environ import value
import pandas as pd

data_df = pd.read_csv("dataset.csv")
day = 38
prices = data_df["day-ahead"].values[day*48:(day+1)*48]

power = 100
capacity = 100
charging_efficiency = 0.85
discharging_efficiency = 1.0
daily_cycles = 2.0
initial_soc = 25

model = pyo.ConcreteModel("Optimiser")
model.time = pyo.Set(initialize=list(range(len(prices))))
model.volume_traded = pyo.Var(model.time)
model.flow_in = pyo.Var(model.time, within=pyo.NonNegativeReals)
model.flow_out = pyo.Var(model.time, within=pyo.NonNegativeReals)
model.soc = pyo.Var(model.time, within=pyo.NonNegativeReals)


def cash_flow(model):
    return pyo.quicksum(model.volume_traded[i] * prices[i] for i in model.time)


model.profit = pyo.Objective(rule=cash_flow, sense=pyo.maximize)


def upper_bound(model, t):
    return model.flow_out[t] <= power


def lower_bound(model, t):
    return model.flow_in[t] <= power


def soc_bound(model, t):
    return model.soc[t] <= capacity


def final_soc_bound(model):
    # Same energy in as out
    return model.soc[model.time.at(-1)] == initial_soc


def energy_rule(model, t):
    return model.volume_traded[t] == model.flow_out[t] - model.flow_in[t]


def cycling_limit(model):
    return (
        pyo.quicksum(model.flow_out[t] for t in model.flow_out)
        <= daily_cycles * capacity
    )


def soc_rule(model, t):
    if t != model.time.at(1):
        return model.soc[t] == model.soc[t - 1] + (
            - model.flow_out[t - 1] * discharging_efficiency
            + model.flow_in[t - 1] * charging_efficiency
        )
    else:
        return model.soc[t] == initial_soc


def final_export(model):
    # Avoid free discharge at the end of the day
    return model.volume_traded[model.time.at(-1)] == 0


model.up_bound_eqn = pyo.Constraint(model.time, rule=upper_bound)
model.low_bound_eqn = pyo.Constraint(model.time, rule=lower_bound)

model.soc_eqn = pyo.Constraint(model.time, rule=soc_bound)

model.sum_eqn = pyo.Constraint(rule=cycling_limit)
model.final_soc_eqn = pyo.Constraint(rule=final_soc_bound)
model.sum_export_eqn = pyo.Constraint(rule=final_export)

model.energy_eqn = pyo.Constraint(model.time, rule=energy_rule)
model.soc_rule_eqn = pyo.Constraint(model.time, rule=soc_rule)

opt = pyo.SolverFactory("appsi_highs")
res = opt.solve(model)
res.write()
# total profit
obj_val = value(model.profit)


volumes = []
soc = []
for i in model.time:
    volumes.append(model.volume_traded[i].value)
    soc.append(model.soc[i].value)

pd.DataFrame({"volumes": volumes, "prices": prices, "soc": soc}).plot()
