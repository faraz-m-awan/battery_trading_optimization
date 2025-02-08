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
CMD ["poetry", "run","streamlit", "run", "/app/battery_trading_optimization/da_optimiser.py", "--server.port=8501", "--server.address=0.0.0.0"]
