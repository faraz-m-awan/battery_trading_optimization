
# Network Infrastructure Analytics Python test

## Task disclaimer

The following questions are required preparation for the 2nd interview in order to get an idea of your technical capability, analytical mindset, coding and DevOps practices, data visualisation and handling. These questions are intentionally open-ended and there is no correct answer – it’s more about the approach you take and how you can explain/justify this than the answer you get.


## Main Task

Zenobe carry out technical due-diligence to convince investors to provide financing for a large battery which will be connected to the GB transmission network.
Your team has developed a python script that can estimate the revenues for a battery trading in the day-ahead wholesale electricity market which has been used for some time. However, the investment committee has decided that they require a more sophisticated model which includes revenues achievable by trading also in the intra-day electricity market.

You are tasked with modifying the existing model so it can meet the new requirements. It is expected that you will refactor the codebase turning a script in a more robust piece of software. The stakeholders also require for the new model to be accessible via some user interface that can allow running it and visualising results without a python installation.


### Problem details

The existing model is given in the python script `da_optimiser.py`, and the data to use is included in the file `dataset.csv`.
This file contains a timeseries of day-ahead and intra-day wholesale electricity prices for the year 2021-2022.
There is one data point per half-hour (also known as a __settlement period__).

The revenue optimisation model you are building is a perfect foresight one, i.e. it assumes perfect knowledge of the market prices at the time that the trading positions in each market are set. However, you should assume that the intra-day prices are not known at the time of the submission of the day-ahead trades. Your model should therefore reflect the following requirements:
1. The model should optimise one day at a time and produce a consistent state of charge history.
2. Perfect foresight optimisation of the day-ahead market. Note that the day-ahead market is cleared in hourly intervals.
3. Re-optimisation in the intra-day market. Note that day-ahead trades are to be treated as fixed in this step, however they can be stacked with intra-day trades. The intra-day market is cleared in half-hourly intervals.
4. Provide the cashflows (traded volumes times prices) for the two markets at each settlement period.

The overall product requirements are as follows:
* Create a repository with the existing script as the main branch and include your edits as a well-documented pull request.
* Create a dashboard (Streamlit or other equivalent) with two tabs:
  - Input tab to set battery power and energy capacity, charging/discharging efficiency, daily maximum discharge cycles and selection of price timeseries input file.
  - Output tab providing a clear visualisation of the battery's operational profile and the corresponding revenues. 
* CI/CD pipeline to deploy changes to the model in your repository.
* Containerise your app with Docker so it can be run on machines without a python installation.


Tips: 
* You can simultaneously buy and sell in different wholesale markets up to your rated power capacity, however you cannot simultaneously charge and discharge the battery.
* The provided script implements the battery optimisation as a linear program, where all decision variables are floats. Such an optimisation instance which includes discrete decision variables is called mixed-integer linear program.

## Questions

In addition to the code, please provide some supporting documentation (e.g. .pdf or .md) explaining your methodology and findings (including plots if required).

### Question 1

Provide the requirements for the main task.
* Repository with pull request detailing the model improvements and CI/CD pipeline
* Containerised Streamlit (or equivalent) app that runs the model
* Supporting documentation

### Question 2

Your solution is now ready to be cloud deployed. Can you outline, with specific references to products and solutions for existing cloud providers of your choosing, how you would structure your deployment given the following requirements:
* You receive a daily email with the input prices for the previous day
* The model should provide results with all latest available data when it is run
* Only a subset of company users should be able to access and run your solution
* You want to keep a database of existing runs so that previous runs can be queried and viewed rather than resubmitted

### Question 3

What are the most critical factors you would need to consider in a continuous deployment pipeline, ensuring consistent uptime for your solution?

### Question 4

The model outputs can be benchmarked against real operational data, which is stored in a structured database. 

* What database would you use for large volumes of sensitive operational data?
* Can you write an instance of a query for such database that joins the operational data to the timeseries output by the model on a per-timestamp basis? 
* What possible issues would you look out for in joining the data?
