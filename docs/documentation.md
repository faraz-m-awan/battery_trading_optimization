# Documentation: Enhancements to Battery Revenue Optimization Model

## 1. Overview
This document provides an overview of the modifications made to the `da_optimiser.py` script, originally based on `da_optimiser_old.py`. The primary enhancements include:

- **Integration of intra-day market optimization**
- **Refactoring the script into an object-oriented format**
- **Developing a Streamlit-based UI for interaction**
- **Implementing CI/CD pipeline for automated deployment**
- **Containerizing the application using Docker**
- **Adding unit tests for robustness**

## 2. Modifications & Enhancements

### 2.1. Code Refactoring
- The script has been restructured into a `BatteryOptimizer` class to improve modularity and maintainability.
- The original procedural script has been encapsulated into methods, making it easier to test and extend.
- Optimizations have been divided into `optimize_day_ahead()` and `optimize_intra_day()` functions.
- The dataset handling has been improved to allow user-defined file uploads via Streamlit.

### 2.2. Intra-Day Market Optimization
- Added intra-day trading logic alongside day-ahead trading.
- Ensured day-ahead trades remain fixed while intra-day optimization is performed.
- Updated SOC calculations to accommodate intra-day adjustments.
- Introduced constraints for intra-day power limits and battery cycling.

### 2.3. Streamlit Dashboard
A graphical user interface has been built using Streamlit, featuring:
- **Input Tab:** Allows users to set battery parameters (power, capacity, efficiency, cycles) and upload custom datasets.
- **Output Tab:** Displays trading volumes, cashflows, and visualizations for day-ahead and intra-day markets.

## 3. CI/CD Implementation
A GitHub Actions workflow has been introduced to ensure continuous integration and deployment:

### Workflow Overview:
- **Triggers on push and pull requests** to the `main` and `intra-day-feature` branches.
- **Build job:**
  - Checks out the repository.
  - Sets up Python 3.11.
  - Installs dependencies using Poetry.
  - Sets the `PYTHONPATH` for package discovery.
  - Runs unit tests using `pytest`.
- **Docker job:**
  - Builds a Docker image for the application.
  - Runs the container to perform basic health checks.
  - Cleans up the container after execution.

GitHub Workflow File (`.github/workflows/ci_pipeline.yml`):
A GitHub Actions workflow has been introduced to ensure continuous integration and deployment:

GitHub Workflow File (`.github/workflows/ci_pipeline.yml`):
```yaml
name: CI Pipeline

on:
  push:
    branches:
      - main
      - intra-day-feature
  pull_request:
    branches:
      - main
      - intra-day-feature

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install Dependencies
        run: poetry install --no-root --no-interaction --no-ansi

      - name: Set PYTHONPATH
        run: echo "PYTHONPATH=$PYTHONPATH:$(pwd)" >> $GITHUB_ENV 
      
      - name: Run Unit Tests
        run: poetry run pytest tests/

  docker:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3
      
      - name: Build Docker Image
        run: docker build -t battery-trading-app .
      
      - name: Run Container Tests
        run: |
          docker run --name battery-optimizer-container -d -p 8501:8501 battery-trading-app
          sleep 5  # Give the container some time to start
          docker logs battery-optimizer-container
      
      - name: Cleanup Docker Container
        run: docker rm -f battery-optimizer-container
```

## 4. Dockerization
The application has been containerized using Docker to enable deployment on any machine without a Python installation.

### Docker Overview:
- **Uses an official Python 3.11 image as the base.**
- **Sets up the working directory** inside the container at `/app`.
- **Copies necessary files**, including `pyproject.toml`, `poetry.lock`, and the source code directory.
- **Installs Poetry** for dependency management.
- **Installs dependencies** using Poetry to ensure a consistent environment.
- **Exposes port 8501** for the Streamlit app.
- **Runs the Streamlit application** using Poetry.

Dockerfile:
```dockerfile
# Use an official Python image as a base
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY pyproject.toml poetry.lock README.md /app/
COPY battery_trading_optimization /app/battery_trading_optimization/
COPY tests /app/tests/

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies using Poetry
RUN poetry install --no-root --no-interaction --no-ansi

# Expose the Streamlit default port
EXPOSE 8501

# Set the entrypoint to run the Streamlit app
CMD ["poetry", "run", "streamlit", "run", "/app/battery_trading_optimization/da_optimiser.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
To build and run the Docker container:
```bash
docker build -t battery-trading-app .
docker run -p 8501:8501 battery-trading-app
```
The application has been containerized using Docker to enable deployment on any machine without a Python installation.

Dockerfile:
```dockerfile
FROM python:3.9
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "da_optimiser.py"]
```
To build and run the Docker container:
```bash
docker build -t da-optimiser .
docker run -p 8501:8501 da-optimiser
```

## 5. Unit Testing
Unit tests have been added using `pytest` to ensure correctness.

### Unit Testing Overview:
- **Tests initialization of the optimizer with dummy data.**
- **Ensures day-ahead optimization produces expected results.**
- **Verifies intra-day optimization executes correctly after day-ahead runs.**
- **Checks that the results contain all required columns.**
- **Raises an exception if intra-day optimization is attempted before day-ahead.**

Example `test_unit.py`:
```python
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
```
Run tests using:
```bash
pytest tests/
```
## 6. Conclusion
This updated model provides a more robust and scalable solution for battery revenue optimization in day-ahead and intra-day electricity markets. By integrating a dashboard, CI/CD pipeline, and Docker containerization, the application is now easier to deploy, test, and use for investment decision-making.

