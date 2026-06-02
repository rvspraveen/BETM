# ERCOT Real-Time LMP Forecast Model — Methodology and Model Notes
## Model ID: FCST-LMP-RT-v2.4
### Prepared by: Analytics & Quantitative Research Group
### Last Revised: October 2024
### CONFIDENTIAL — PROPRIETARY MODEL DOCUMENTATION

---

## 1. Purpose and Scope

This document describes the methodology, data inputs, calibration procedures, and known limitations of the firm's real-time Locational Marginal Price (LMP) forecast model for ERCOT, designated FCST-LMP-RT-v2.4. The model produces 15-minute and hourly LMP forecasts for the four ERCOT load zones (HB_NORTH, HB_HOUSTON, HB_SOUTH, HB_WEST) and 12 key settlement points (including key generation nodes such as PSN_DCEC_ALL, PSN_RAYBN_ALL) for a rolling 72-hour horizon.

Outputs are consumed by:
- Day-ahead offer optimization engine (OFFER-OPT)
- Real-time position management system (RTPM)
- Risk VaR engine (RISK-VAR)
- The AI Market Copilot question-answering layer (COPILOT-v1)

---

## 2. Model Architecture Overview

FCST-LMP-RT-v2.4 is a **hybrid ensemble model** combining:

1. **Fundamental price stack** — merit order model driven by gas prices, heat rates, and wind/solar availability
2. **Statistical residual model** — gradient boosted trees (XGBoost) capturing historical patterns not explained by fundamentals
3. **Congestion overlay** — constraint shadow price estimator using historical constraint binding frequencies
4. **Ensemble combiner** — weighted average using time-of-day and season-specific weights, optimized on rolling 90-day out-of-sample performance

```
Inputs → [Fundamental Stack] ──┐
                                ├──→ [Ensemble Combiner] → LMP Forecast
Inputs → [XGBoost Residual] ───┤
                                │
Inputs → [Congestion Overlay] ─┘
```

---

## 3. Input Data Sources

### 3.1 Weather Inputs

| Input | Source | Update Frequency | Lag |
|-------|--------|-----------------|-----|
| 2-m temperature (5 ERCOT zones) | NOAA HRRR | Hourly | 1.5 hr |
| Dew point / humidity | NOAA HRRR | Hourly | 1.5 hr |
| Wind speed at 80m (10 grid points) | NOAA HRRR | Hourly | 1.5 hr |
| GHI solar irradiance (6 grid points) | NOAA HRRR | Hourly | 1.5 hr |
| Forecast confidence (ensemble spread) | NOAA GEFS | 6-hourly | 3 hr |

**Weather normalization:** All temperature inputs are converted to Cooling Degree Hours (CDH) using a base temperature of 65°F for load estimation. Wind and solar inputs are fed directly to the renewable generation sub-model (see §3.3).

### 3.2 Fuel Price Inputs

| Input | Source | Update Frequency |
|-------|--------|-----------------|
| Henry Hub day-ahead gas price | ICE / Bloomberg | Daily at 10:00 CPT |
| Katy Hub basis differential | ICE | Daily at 10:00 CPT |
| Waha Hub basis differential | ICE | Daily at 10:00 CPT |
| Fuel oil #2 (backup fuel) | OPIS | Daily |
| CO2 allowance price (voluntary) | S&P | Daily |

**Gas price to plant dispatch cost:** For each gas-fired resource in the model unit commitment database (396 ERCOT thermal units as of Q3 2024), dispatch cost is computed as:

```
Dispatch_cost(i) = [Gas_price_hub(i) × HR_full_load(i)] + VOM(i) + StartCost_amortized(i)
```

Where `HR_full_load` is the full-load heat rate (MMBtu/MWh), `VOM` is variable O&M ($/MWh), and `StartCost_amortized` is the per-MWh startup cost amortized over minimum run time.

### 3.3 Renewable Generation Forecast

**Wind:** A site-level wind power curve model translates HRRR 80m wind speed forecasts to MW output for each ERCOT-registered wind plant (248 plants, 32,800 MW installed capacity as of model build). Aggregate ERCOT wind forecast is the sum of site-level outputs with a **10% upward bias correction** applied during low-wind hours (< 8 m/s) based on observed ERCOT STWPF vs. actuals analysis.

**Solar:** GHI-to-DC output conversion uses a fleet-average performance ratio of 0.82 and temperature-corrected cell efficiency. DC-to-AC conversion uses a fleet-average inverter loading ratio of 1.28. Forecast covers approximately 19,400 MW of utility-scale solar (Q3 2024). Distributed/BTM solar is estimated via a regression model using temperature and irradiance; this is a known source of model error (see §7).

### 3.4 Load Forecast

ERCOT's own Short-Term Load Forecast (STLF) is used as the primary load input, with a proprietary **weather-adjustment correction** applied:

```
Load_adjusted = ERCOT_STLF + α × (T_HRRR - T_ERCOT_wx) × dLoad/dTemp
```

Where `dLoad/dTemp` is the temperature sensitivity coefficient estimated by zone and hour-of-day from historical regression (summer peak: ~320 MW/°F for ERCOT system). `α` is a dampening factor (0.65) applied because ERCOT's model partially incorporates intra-day weather updates.

---

## 4. Fundamental Price Stack Model

### 4.1 Economic Dispatch Simulation

The fundamental stack model solves an approximate economic dispatch at each forecast interval:

1. Rank all dispatchable resources by marginal cost (ascending)
2. Dispatch units until total generation = forecast load + operating reserves target (currently 2,300 MW ORDC threshold)
3. The marginal unit's cost sets the system lambda (energy component of LMP)
4. Add ORDC adder: capacity shortfall below 2,300 MW triggers ORDC scarcity pricing

**ORDC Adder Calculation:**
```
ORDC(reserves) = VOLL × P(loss of load | reserves)
VOLL = $5,000/MWh (ERCOT regulatory value)
P(loss of load) modeled as log-normal curve calibrated to ERCOT historical reserve-loss data
```

### 4.2 Congestion Component

Transmission congestion is modeled using a **constraint shadow price lookup table** built from 3 years of ERCOT historical binding constraint data:

- 847 unique constraints identified in historical data
- For each constraint: binding frequency by hour-of-day, season, and weather regime
- Expected congestion component = Σ [P(constraint_k binds) × historical_avg_shadow_price_k]

Top constraints by expected contribution to HB_SOUTH price separation (summer peak):
1. Houston Import Limit (HIL) — avg shadow price $847/MWh when binding
2. Flores-Kendall 345kV — avg shadow price $312/MWh when binding
3. LCRA_LCRA 138kV — avg shadow price $187/MWh when binding

**Known limitation:** The congestion model cannot anticipate novel constraint activations driven by new topology changes or unusual generation patterns. See §7.3.

---

## 5. XGBoost Residual Model

### 5.1 Purpose

The fundamental stack systematically over- or under-estimates LMP in certain conditions — particularly during ramp events, low-load shoulder hours, and high-renewable penetration scenarios. The XGBoost residual model learns these patterns from 4 years of historical 15-minute data (2020–2024).

### 5.2 Features

| Feature Category | Features (36 total) |
|-----------------|----------------------|
| Time | Hour-of-day, day-of-week, month, holiday flag, days-to-expiry of prompt gas contract |
| Fundamental output | Stack lambda, ORDC adder, expected congestion, reserve level |
| Weather | CDH, temperature deviation from 30-day normal, humidity, wind ramp (dW/dt) |
| Renewable | Wind output (actual + 1hr lag), solar output, wind-to-load ratio, solar-to-load ratio |
| Market state | DAM vs. RT spread (prior day), recent RT volatility (6-hr rolling std), prior interval LMP |
| Grid | Outage capacity (MW) by fuel type, net load, ramp rate (dLoad/dt) |

### 5.3 Training and Validation

- **Training set:** Jan 2020 – Dec 2023 (4 years, ~140,000 15-min observations per node)
- **Validation set:** Jan – Jun 2024 (out-of-sample)
- **Test set:** Jul – Sep 2024 (held-out, evaluated at model release)
- **Hyperparameter tuning:** Bayesian optimization over 200 trials (Optuna)
- **Objective:** MAE (mean absolute error) — chosen over RMSE to reduce sensitivity to extreme price spikes

### 5.4 Model Performance (Test Set, Jul–Sep 2024)

| Node | MAE ($/MWh) | RMSE ($/MWh) | MAPE (%) | Spike Recall (>$200) |
|------|------------|-------------|---------|----------------------|
| HB_NORTH | 4.12 | 18.7 | 7.3% | 68% |
| HB_HOUSTON | 5.84 | 31.2 | 9.1% | 61% |
| HB_SOUTH | 6.21 | 34.8 | 9.8% | 58% |
| HB_WEST | 3.97 | 15.4 | 7.1% | 71% |

**Note on spike recall:** The model correctly predicts approximately 60–70% of hours with LMP > $200/MWh at least one interval in advance. False positive rate is ~8% (model predicts spike that does not materialize). Spike recall deteriorates significantly for spikes above $1,000/MWh; see §7.2.

---

## 6. Ensemble Weighting and Calibration

### 6.1 Combining Weights (Summer On-Peak, HB_SOUTH)

| Model Component | Weight |
|----------------|--------|
| Fundamental Stack | 0.35 |
| XGBoost Residual | 0.52 |
| Congestion Overlay | 0.13 |

Weights are re-optimized monthly using the prior 90 days of out-of-sample performance. Weights vary by time-of-day, season, and zone.

### 6.2 Uncertainty Quantification

The model produces **90% prediction intervals** derived from:
- Ensemble spread across 50 perturbed input scenarios (weather uncertainty + fuel price uncertainty)
- XGBoost quantile regression outputs (q=0.05, q=0.95 models)
- Combined via conformal prediction calibration (coverage verified quarterly)

Prediction interval width at HB_SOUTH, summer on-peak hours: median ±$28/MWh. During high-stress scenarios (reserves < 3,000 MW), interval width expands to ±$180/MWh reflecting model uncertainty.

---

## 7. Known Limitations and Open Issues

### 7.1 Extreme Price Events (> $1,000/MWh)

The model is not calibrated to predict extreme scarcity pricing events. Training data contains very few observations above $1,000/MWh (< 0.2% of intervals), and the model systematically under-predicts these events. Users should apply **manual stress overlays** when reserve levels are forecast below 2,000 MW or during heat emergency conditions.

**Recommendation:** Do not use model outputs as the sole risk input when ERCOT issues an Operating Condition Notice (OCN) or Energy Emergency Alert (EEA).

### 7.2 Distributed Solar (BTM) Estimation

Behind-the-meter solar (estimated 6,200 MW installed in ERCOT as of Q3 2024) is not directly metered. The model estimates BTM output via regression on weather data. Errors in BTM estimation of ±500–800 MW are common during rapid cloud cover changes, contributing to load forecast errors and LMP forecast errors particularly in the 11:00–15:00 CPT shoulder period.

### 7.3 Novel Transmission Constraints

The congestion overlay model is entirely backward-looking. When ERCOT activates a constraint not seen in the historical training set (e.g., following new transmission construction or unusual topology), the model will have zero expected congestion contribution for that constraint, potentially leading to significant underestimation of congestion costs.

**Mitigation:** Traders should manually review the ERCOT Morning Report (Congestion Analysis) and override model congestion forecasts when novel constraints are identified.

### 7.4 Model Staleness During Market Rule Changes

ERCOT implemented the ORDC reform in June 2022 and the Real-Time Co-optimization (RTC) pilot in Q4 2023. The model was retrained after each reform, but residual calibration issues may persist in scenarios that were not well-represented in post-reform training data. The RTC sub-model is considered **beta** and should not be used for positions > 500 MW without analyst review.

---

## 8. Governance and Review Schedule

| Activity | Frequency | Owner |
|----------|-----------|-------|
| Performance monitoring report | Weekly | Analytics Team |
| Hyperparameter re-tuning | Monthly | Quant Research |
| Full model re-training | Quarterly | Quant Research |
| Independent model validation | Annually | Risk Analytics (independent) |
| Material change review (rule changes, major market events) | Ad hoc | Model Governance Committee |

Model changes that affect VaR calculations require sign-off from the Risk Officer before deployment.

---

## 9. Version History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | Jan 2020 | Initial deployment — fundamental stack only |
| v1.5 | Jun 2021 | XGBoost residual layer added |
| v2.0 | Aug 2022 | Retrained post-ORDC reform; congestion overlay added |
| v2.1 | Jan 2023 | BTM solar estimation module improved |
| v2.2 | Nov 2023 | RTC pilot sub-model added (beta) |
| v2.3 | Apr 2024 | Ensemble combiner moved to conformal prediction intervals |
| v2.4 | Oct 2024 | Full quarterly retrain; spike recall improved +7pp via focal loss weighting |

---

*Questions: analytics@company.com*
*Model Governance issue tracker: internal Jira — project QUANT*
