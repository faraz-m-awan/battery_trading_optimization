import io
import streamlit as st
from battery_trading_optimization.da_optimiser import main

def dummy_number_input(label, **kwargs):
    """
    Dummy replacement for st.sidebar.number_input.
    Returns the default value provided via kwargs.
    """
    return kwargs.get("value", 0)

def dummy_slider(label, **kwargs):
    """
    Dummy replacement for st.sidebar.slider.
    Returns the default value provided via kwargs.
    """
    return kwargs.get("value", 0)

def dummy_file_uploader(label, **kwargs):
    """
    Dummy replacement for st.sidebar.file_uploader.
    Returns a StringIO object simulating a CSV file with 48 settlement periods.
    """
    # Create a dummy CSV for one day (48 rows)
    csv_content = "day-ahead,intra-day\n" + "50,45\n" * 48
    return io.StringIO(csv_content)

def test_main_integration(monkeypatch):
    """
    Integration test that monkeypatches the Streamlit sidebar functions to simulate user inputs.
    If main() runs without errors, the integration is considered successful.
    """
    # Monkeypatch sidebar functions
    monkeypatch.setattr(st.sidebar, "number_input", dummy_number_input)
    monkeypatch.setattr(st.sidebar, "slider", dummy_slider)
    monkeypatch.setattr(st.sidebar, "file_uploader", dummy_file_uploader)
    
    # Call the main function; success is indicated by the absence of exceptions.
    main()
