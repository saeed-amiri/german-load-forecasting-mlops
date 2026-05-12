# Project Introduction

This project uses machine learning to predict electricity load in Germany.

It integrates Airflow for pipelines and MLflow for tracking.

Production-style MLOps platform for German electricity load forecasting with API serving, authentication, orchestration, and monitoring.

This repository is an ongoing portfolio project focused on showing end-to-end machine learning system design, not only model training.

## Problem and Goal

Energy systems require accurate short-term load forecasts and robust anomaly detection to maintain grid stability and operational efficiency. This project aims to provide:

- Hourly and day-ahead load forecasting workflow
- API-based prediction and data access layer
- Monitoring-ready runtime stack with health/metrics visibility
- Reproducible ML/data operations workflow
- MLflow experiment tracking with optional DagsHub remote tracking

## Data Sources

This project focuses on German power-system time series and uses open datasets as primary inputs.

- ENTSO-E Transparency Platform
  - Used for German load actual and load forecast signals.
  - In this repo, mapped fields include DE_load_actual_entsoe_transparency and DE_load_forecast_entsoe_transparency.

- Open Power System Data
  - Used as the main public historical time-series source for electricity-related signals.
  - Repository sample input is data/raw/time_series-2020-10-06.csv (tracked with DVC metadata).

- Weather context (planned/extendable)
  - Weather covariates are planned as optional enrichments for forecasting quality.
  - Suggested providers include Meteostat and OpenWeather.

Current raw-to-clean mapping is defined in configs/inputs/sql.yml under sources.load.columns.