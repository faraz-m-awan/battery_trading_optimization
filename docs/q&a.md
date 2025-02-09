# Q&A Documentation

## 1. Methodology
### Objective
The goal of this study is to optimize battery trading operations in the day-ahead electricity market while incorporating intra-day adjustments. This enables better revenue management for battery storage operators, ensuring that both market strategies contribute to profitability.

### Approach
- **Data Preprocessing:** We use historical electricity price data for both the day-ahead and intra-day markets.
- **Optimization Strategy:**
  - **Day-Ahead Trading:** A perfect foresight optimization model determines optimal trading volumes.
  - **Intra-Day Trading:** Adjustments are made based on real-time intra-day prices, while ensuring the integrity of the battery's state of charge (SOC).
- **Model Implementation:** The optimization is implemented using Pyomo for constraint modeling and Streamlit for visualization.
- **Validation:** The model is validated by running multiple simulations with different battery configurations and market conditions.

## 2. Findings

```markdown
![Day-Ahead Trading and Price Chart](https://github.com/faraz-m-awan/battery_trading_optimization/blob/intra-day-feature/battery_trading_optimization/output/day_ahead.png)
```

The figure provided illustrates key insights from the day-ahead optimization process:
The figure provided illustrates key insights from the day-ahead optimization process:

- **Day-Ahead Trade Volume vs. Cashflow:**
  - Trade volumes (blue) fluctuate throughout the settlement periods, aligning with periods of high price volatility.
  - The cashflow (red) follows a similar pattern, with significant peaks and drops indicating profitable trading opportunities.
  
- **Day-Ahead Price Trends:**
  - Prices exhibit cyclical behavior with noticeable peaks.
  - High prices correlate with increased trading activity, as expected in an arbitrage-based optimization model.
  
- **Key Takeaways:**
  - The model successfully identifies periods where trading is most beneficial.
  - The synchronization of trade volume and price peaks indicates effective forecasting.
  - The final state of charge is preserved, ensuring operational feasibility for subsequent trading days.

These results confirm that the optimized battery trading strategy improves revenue generation while adhering to physical and market constraints. Future enhancements will incorporate stochastic modeling to handle market uncertainties.

