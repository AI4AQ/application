AI4AQ
==============================

## Problem and Motivation

The Salt Lake Valley experiences some of the worst air quality in the United States. In the winter, inversions trap polluted air for days at a time. 600,000 residents are especially threatened by the unhealthy air quality ([source](https://www.iqair.com/us/usa/utah/salt-lake-city)). Experts estimate that the poor air quality decreases the median life expectancy by up to 3.6 years ([source](https://www.mdpi.com/2073-4433/11/11/1238)).

To meet EPA guidelines, a region must not exceed a two-year weighted average of 3.2 days of unhealthy pollution. From 2016 to 2018, Salt Lake City had a weighted average of 25.7 days of unhealthy ozone levels and 11.5 days of unhealthy PM 2.5 levels ([source](https://www.iqair.com/us/usa/utah/salt-lake-city)). Residents need information about current air quality to make informed decisions about their daily actions. We present such information in our dashboard. Our dashboard also allows residents to understand historic air quality trends and investigate inequalities that exist by geographic region and income categories. Finally, we use machine learning to impute air quality levels for areas without sensors.

## Data Sources
- [PurpleAir](https://community.purpleair.com/c/purpleair-data/7): PurpleAir is a community science project that relies on the public to place sensors and crowdsource data, so some geographic areas in the Salt Lake Valley are not represented in the available data. PurpleAir Sensors are designed to accurately measure PM 2.5 and provide estimates for PM 10 and other values. Sensors may malfunction and yield unreliable results. We filter unreliable data.
- [Low to Moderate Income Population by Block Group](https://hudgis-hud.opendata.arcgis.com/datasets/HUD::low-to-moderate-income-population-by-block-group/about), US Department of Housing and Urban Development 
- [Census](https://www.census.gov/data.html): Census data was used to identify census tracts in the geographic area of interest. We also used census data as features in our machine learning models.
- [OpenStreetMaps](https://www.openstreetmap.org/#map=4/38.00/-95.80): Map images for modeling.
- [Open Meteo](https://open-meteo.com/): Weather and wind data.
- [Medicare Claims](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities): Full data was available for 2019, but for 2016-2018 and 2020-2022 only a 5% sample across the United States was available. Some records may have been suppressed for privacy reasons if there were fewer than 10 patient records for the aggregate category of weekly diagnosis counts at each facility.

## Data Science Approach

**Data Pipeline**: We utilize AWS Lambda functions to pull daily data from PurpleAir's API. These automated functions also process the data by removing implausible values. PurpleAir sensors have two channels that take two separate readings. When both channels yield plausible values, we will take the average. If a channel yields an implausible value (equal to zero or greater than 500), we will exclude that channel. The daily PurpleAir data is stored in an S3 bucket. We containerized our application and deployed it online using AWS Lightsail. 

**Machine Learning**: We explored three approaches to impute PM 2.5 and PM 10 values for census tracts that did not have a PurpleAir sensor: XGBoost, a dense neural network, and a CNN-feedforward neural network combination. We used features like the month, the average PM 2.5 value for that day, the county, the wind speed, wind gusts, latitude, longitude, income category, nearest PM 2.5 value, and nearest PM 10 value, and visual map data. The CNN-feedforward neural network performed the best and was used to generate estimates for census tracts without sensors.

**Evaluation**: We compared models with common metrics including mean absolute error, root mean squared error, and R<sup>2</sup>.

## Key Learnings and Impacts

Our work highlights the disparities felt by different geographic and economic communities within the Salt Lake region. Using our dashboard, anyone can easily see that sensors are not as common in lower income areas, and that low income areas face worse air quality.

We fill the data gap by using AI to generate PM 2.5 and PM 10 estimates for areas without sensors.

Our work is accessible. It can be used by Salt Lake valley residents to make daily decisions and long-term decisions, like where to move to. It can also be used by policymakers to uncover disparaties and protect their constituents. 

Project Organization
------------

    ├── README.md                      <- The top-level README for this project.
    ├── data   
    │   ├── external                   <- Data from third party sources.
    │   └── processed                  <- The final, canonical data sets for modeling.
    │
    ├── flask_app                      <- All code needed for the application.
    │   
    ├── notebooks                      <- Jupyter notebooks.
    │   └── EDA                        <- Notebooks containing initial EDA of relevant air quality datasets
    │       ├── AirNow                 <- EPA's realtime air quality data source
    │       ├── AQS                    <- EPA's historical air quality data source
    │       └── purple-air             <- Crowd-sourced sensor network
    │   └── health                     <- Notebooks containing initial EDA of health datasets
    │   
    ├── requirements.txt               <- The requirements file used in the Dockerfile
    │
    ├── Dockerfile                     <- Generates Docker image
    │   
    └── src                            <- Source code for use in this project.
        ├── coordinates.json           <- latitude/longitude coordinates for map area and sensor area
        ├── api_credentials.json       <- PurpleAir API credentials
        ├── purpleair_parameters.json  <- Sensor IDs in Salt Lake area used for the app
        └── data                       <- Scripts to download or generate data
