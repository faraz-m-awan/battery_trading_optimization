# Battery Trading Optimization

## Overview
This repository contains a battery revenue optimization tool for day-ahead and intra-day electricity trading. The optimization is implemented using Pyomo for mathematical modeling and Streamlit for interactive visualization.

## Features
- **Day-Ahead Optimization**: Determines the optimal battery trading strategy in the day-ahead market.
- **Intra-Day Optimization**: Adjusts the trading strategy based on intra-day market prices.
- **Battery Constraints**: Incorporates constraints such as charging/discharging efficiency, power limits, and cycling limits.
- **Interactive Dashboard**: Allows users to configure battery parameters and visualize results in a web-based interface.
- **Unit Tests & CI/CD**: Includes automated tests and a CI/CD pipeline for continuous integration and deployment.

## Project Structure
```
├── battery_trading_optimization
│   ├── da_optimiser.py      # Main optimization script with Streamlit UI
├── tests
│   ├── test_unit.py         # Unit tests for the optimization models
├── Dockerfile               # Docker container setup
├── ci_pipeline.yml          # GitHub Actions CI/CD pipeline
├── pyproject.toml           # Poetry dependencies and package management
├── README.md                # Project documentation
```

## Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-repository-url.git
   cd battery_trading_optimization
   ```
2. **Install dependencies using Poetry:**
   ```sh
   pip install poetry
   poetry install
   ```

## Running the Application
Run the Streamlit application:
```sh
poetry run streamlit run battery_trading_optimization/da_optimiser.py
```
This will launch a web-based dashboard where you can configure parameters and visualize the results.

## Running Tests
To run unit tests, execute:
```sh
poetry run pytest tests/
```

## Docker Deployment
1. **Build the Docker image:**
   ```sh
   docker build -t battery-trading-app .
   ```
2. **Run the Docker container:**
   ```sh
   docker run -p 8501:8501 battery-trading-app
   ```

## CI/CD Pipeline
This repository includes a GitHub Actions workflow for:
- Running unit tests on push and pull requests.
- Building a Docker image and testing the container.

The pipeline is defined in `ci_pipeline.yml` and automatically runs on branches `main` and `intra-day-feature`.

## Contributions
Feel free to open issues or submit pull requests to improve the optimization model or add new features.


