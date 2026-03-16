# 13 Mär 2026
## Data
data is downloaded from:  

"https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv"

and save in "data/raw/time_series-2020-10-06.csv".

### The Mindset: "Compute where the data lives"

In MLOps, the rule of thumb is simple: **SQL prepares the ingredients; Pandas cooks the meal.**

*   **SQL (The Bouncer):** Handles filtering, joining, and aggregating millions of rows *before* they enter your Python memory. It is faster because it uses database indexes and doesn't have to move data across a network.
*   **Pandas (The Chef):** Handles complex mathematical transformations, custom feature engineering, and model-specific logic that SQL isn't designed for.

---

### When to use which? (The Map)

| Stage | Use SQL | Use Pandas | Why? |
| :--- | :--- | :--- | :--- |
| **Ingestion** | **YES** | No | Inserting raw API data into tables. |
| **Selection** | **YES** | No | Filtering dates, selecting specific regions. |
| **Joining** | **YES** | No | Joining Weather + Load tables. Much faster in DB. |
| **Feature Eng.** | Optional | **YES** | Complex logic like "Rolling Mean over 7 days" is easier to write/maintain in Python. |
| **Normalization**| No | **YES** | Scaling data (MinMax/StandardScaler) is a ML step, not a data step. |

---

### How to apply this to your project

To prove your SQL understanding without overdoing it, follow this workflow:

#### 1. The "Push-Down" Strategy
Don't pull all raw data into Pandas and *then* filter it. Do the heavy lifting in SQL.

**Scenario:** You have 10 years of data, but you only want to train on 2023 data, joining Load with Weather.

**Bad Approach (Pandas only):**
```python
# Loads EVERYTHING into RAM (Slow, memory heavy)
df_load = pd.read_csv("huge_load_file.csv")
df_weather = pd.read_csv("huge_weather_file.csv")
df = pd.merge(df_load, df_weather, on='time')
df = df[df['time'] > '2023-01-01']
```

**Good Approach (SQL + Pandas):**
```python
query = """
    SELECT 
        l.timestamp, 
        l.load_value, 
        w.temperature
    FROM load_table l
    JOIN weather_table w ON l.timestamp = w.timestamp
    WHERE l.timestamp >= '2023-01-01';  -- Filtering happens in DB!
"""
df = pd.read_sql(query, connection) # Only relevant data hits Python
```

#### 2. How to prevent duplication
Do not mix logic.
*   **SQL Script:** `SELECT`, `WHERE`, `JOIN`, `GROUP BY`.
*   **Python Script:** Calculated columns, lags, scaling.

**Example of Overdoing it (Avoid):**
Writing a 50-line SQL query to calculate a complex rolling average window.
**Better:** Use SQL to get the raw numbers clean -> Use Pandas `.rolling()` for the math.

### Summary for your Project
To show off your skills, implement this flow:

1.  **Ingestion Service:** Python fetches API data -> executes `INSERT INTO` SQL script.
2.  **Preprocessing Service:** Python executes `SELECT ... JOIN ... WHERE` SQL script -> loads result into Pandas -> does feature engineering -> saves to `processed/`.

This proves you know SQL is for **data management** and Pandas is for **data science**.