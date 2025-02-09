import pytest
import pandas as pd
from battery_trading_optimization.da_optimiser import BatteryOptimizer

def create_dummy_data():
    """
    Create dummy data for two days (96 rows) with simple increasing prices.
    Each day has 48 settlement periods.
    """
    df = pd.DataFrame({
        "day-ahead": [50 + i * 0.1 for i in range(96)],
        "intra-day": [45 + i * 0.1 for i in range(96)]
    })
    return df

def test_optimize_day_ahead():
    df = create_dummy_data()
    optimizer = BatteryOptimizer(
        data=df,
        day=0,
        power=100,
        capacity=100,
        charging_efficiency=0.85,
        discharging_efficiency=1.0,
        daily_cycles=2.0,
        initial_soc=25
    )
    optimizer.optimize_day_ahead()
    # Verify that there are 48 settlement periods.
    assert len(optimizer.v_da_sol) == 48, "Expected 48 day‑ahead settlement results."
    # Check that the final state of charge equals the initial SOC.
    assert abs(optimizer.soc_da_sol[-1] - optimizer.initial_soc) < 0.001, "Final SOC should equal the initial SOC."

def test_optimize_intra_day():
    df = create_dummy_data()
    optimizer = BatteryOptimizer(
        data=df,
        day=0,
        power=100,
        capacity=100,
        charging_efficiency=0.85,
        discharging_efficiency=1.0,
        daily_cycles=2.0,
        initial_soc=25
    )
    # Run day‑ahead first.
    optimizer.optimize_day_ahead()
    optimizer.optimize_intra_day()
    # Verify that there are 48 settlement periods.
    assert len(optimizer.v_id_sol) == 48, "Expected 48 intra‑day settlement results."
    # Check that the combined SOC ends at the initial SOC.
    assert abs(optimizer.soc_total_sol[-1] - optimizer.initial_soc) < 0.001, "Combined SOC should end at the initial SOC."

def test_get_results():
    df = create_dummy_data()
    optimizer = BatteryOptimizer(
        data=df,
        day=0,
        power=100,
        capacity=100,
        charging_efficiency=0.85,
        discharging_efficiency=1.0,
        daily_cycles=2.0,
        initial_soc=25
    )
    optimizer.optimize_day_ahead()
    optimizer.optimize_intra_day()
    results_df, da_revenue, id_revenue = optimizer.get_results()
    expected_columns = [
        "Settlement Period", "DayAhead Trade (vol)", "IntraDay Trade (vol)",
        "DayAhead Price", "IntraDay Price", "DayAhead Cashflow",
        "IntraDay Cashflow", "Total Cashflow", "SOC after DayAhead", "SOC Total"
    ]
    for col in expected_columns:
        assert col in results_df.columns, f"Column '{col}' not found in results."

def test_intra_day_without_day_ahead():
    df = create_dummy_data()
    optimizer = BatteryOptimizer(
        data=df,
        day=0,
        power=100,
        capacity=100,
        charging_efficiency=0.85,
        discharging_efficiency=1.0,
        daily_cycles=2.0,
        initial_soc=25
    )
    with pytest.raises(Exception):
        optimizer.optimize_intra_day()
