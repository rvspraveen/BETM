# ERCOT Settlement Calculation Guide
## For QSEs and Load-Serving Entities
### Version 3.1 | Effective January 1, 2024
### Document: ERCOT-SETTLE-GUIDE-2024-3.1

---

## 1. Introduction

This guide explains how ERCOT calculates wholesale market settlements for Qualified Scheduling Entities (QSEs). It is intended as a practical reference for traders, schedulers, and settlement accountants. All calculations are governed by ERCOT Protocols Section 9; this guide provides worked examples and clarifications.

**Settlement Calendar:** ERCOT issues invoices on the **second Wednesday** of each month for the prior calendar month's activity. Payments are due the **second Friday** of each month (same week as invoice). For December activity, invoices are issued the second Wednesday of January.

---

## 2. Settlement Intervals and Timing

| Market Segment | Settlement Interval | Publication Lag | Final Settlement |
|---------------|--------------------|-----------------|--------------------|
| Day-Ahead Market | Hourly | D+3 business days (preliminary) | D+55 days (final) |
| Real-Time Market | 15-minute | HE+30 min (preliminary) | D+55 days (final) |
| Ancillary Services | Hourly | D+3 business days | D+55 days (final) |
| CRR Settlements | Monthly | M+5 business days | M+30 days (final) |

**Resettlement:** ERCOT may issue resettled invoices up to 730 days (24 months) after the operating day for errors, meter data corrections, or protocol compliance issues.

---

## 3. Day-Ahead Market Settlement

### 3.1 DAM Energy Settlement

For each settlement interval *h* and settlement point *p*:

```
DAM_Energy_Settlement(h,p) = 
    DAM_SPP(h,p) × [DAM_Award_Gen(h,p) - DAM_Award_Load(h,p)]
```

- **DAM_SPP:** Day-Ahead Settlement Point Price ($/MWh), published post-clearing
- **DAM_Award_Gen:** MWh of generation awarded in DAM at settlement point *p*
- **DAM_Award_Load:** MWh of load awarded (load bids cleared) at settlement point *p*

*Sign convention:* Positive = QSE receives payment (net generation); Negative = QSE pays (net load)

### 3.2 DAM Ancillary Service Settlement

For each AS type and hour:
```
DAM_AS_Settlement = AS_Clearing_Price × AS_MW_Awarded × 1_hour
```

AS Clearing Prices are published with DAM results. Units are $/MW-hour.

**2024 Reference: Typical AS Clearing Price Ranges**

| AS Product | Typical Range ($/MW-hr) | Summer Peak Range |
|-----------|------------------------|-------------------|
| Reg-Up | $3–$15 | $8–$25 |
| Reg-Down | $2–$12 | $5–$18 |
| RRS | $1–$8 | $3–$15 |
| ECRS | $2–$10 | $5–$20 |
| NSRS | $0.50–$4 | $1–$8 |

---

## 4. Real-Time Market Settlement

### 4.1 Real-Time Energy Imbalance

The Real-Time settlement charges/credits QSEs for the difference between their DAM schedule and actual real-time metered quantities.

For each 15-minute interval *i* and settlement point *p*:

```
RT_Imbalance_Settlement(i,p) = 
    RT_SPP(i,p) × [Actual_Metered(i,p) - DAM_Schedule(i,p)] / 4
```

*(Division by 4 converts 15-min interval to hourly MWh basis)*

**Important:** The DAM schedule used in this calculation is the Hourly DAM Award, applied uniformly across all four 15-minute intervals within the hour.

### 4.2 Uninstructed Deviation (UD) Charge

When a resource's actual output deviates from ERCOT's SCED dispatch instruction (HASL/LASL) without authorization, an Uninstructed Deviation Charge applies:

```
UD_Charge = |Deviation_MW| × UD_Adder × interval_hours
```

The UD Adder is set equal to the greater of:
- $0/MWh (if system is long — resource deviated high when it should have been lower)
- RTM_SPP – offer_price (if resource deviated high when system is short)

Per ERCOT Protocols, UDs exceeding **±25 MW** or **±10% of HASL** for more than **2 consecutive intervals** trigger an automatic compliance review.

### 4.3 RT Settlement Point Price Calculation

RT SPPs for a 15-minute interval are computed as the **arithmetic average of the four 5-minute SCED LMPs** within that interval:

```
RT_SPP(15-min interval) = (SCED_LMP_1 + SCED_LMP_2 + SCED_LMP_3 + SCED_LMP_4) / 4
```

For Load Zone settlement points (LZ_NORTH, LZ_HOUSTON, LZ_SOUTH, LZ_WEST), the RT_SPP is calculated as the load-weighted average of all Resource Node prices within that zone.

---

## 5. Congestion Revenue Rights Settlement

### 5.1 CRR Payment Calculation

For each CRR held in a given DAM settlement hour:

```
CRR_Payment(h) = CRR_MW × [DAM_LMP_congestion(h, sink) - DAM_LMP_congestion(h, source)]
```

Note: CRR settlements use **Day-Ahead** congestion components only, not real-time. Participants wishing to hedge real-time congestion must transact in the bilateral market (no ERCOT-cleared RT CRR product exists).

### 5.2 Revenue Adequacy Haircut

If total CRR obligations exceed total DAM congestion revenue collected in a settlement period, ERCOT applies a pro-rata haircut:

```
Haircut_Factor = Total_DAM_Congestion_Revenue / Total_CRR_Obligations
Adjusted_CRR_Payment = CRR_Payment × min(Haircut_Factor, 1.0)
```

---

## 6. Capacity Settlement (Performance Credit Mechanism)

Effective June 1, 2023, ERCOT implemented the Performance Credit Mechanism (PCM) — a capacity market that compensates resources for performance during scarcity events.

### 6.1 Performance Credit Value

Performance Credits are earned during **Performance Credit Hours (PCH)** — system stress events when reserves fall below 2,000 MW.

```
PCH_Credit = Resource_Output_during_PCH × Credit_Rate ($/MWh)
```

The Credit Rate is determined annually based on the value of lost load (VoLL) and expected PCH hours. For 2024, the Credit Rate is set at **$75/MWh** for PCH output.

### 6.2 Performance Credit Obligation

Load resources and LSEs pay a performance credit obligation proportional to their load ratio share:

```
LSE_Obligation = Load_Ratio_Share × Total_PCH_Credits_paid
```

**2024 Estimated PCM Impact:**

| Month | PCH Events | Total Credits Paid | Avg LSE Cost (¢/MWh served) |
|-------|-----------|-------------------|----------------------------|
| Jan | 0 | $0 | $0 |
| Feb | 2 | $3.2M | 0.28¢ |
| Mar–May | 0 | $0 | $0 |
| Jun | 1 | $8.4M | 0.74¢ |
| Jul | 4 | $31.7M | 2.80¢ |
| Aug | 6 | $48.9M | 4.32¢ |

---

## 7. Meter Data and True-Up Process

### 7.1 Meter Types and Hierarchy

| Meter Type | Used For | Timing |
|-----------|---------|--------|
| Telemetry (SCADA) | Real-time dispatch | Online (5-min) |
| Interval Data Recorder (IDR) | Preliminary settlement | D+3 business days |
| Certified Meter Read | Final settlement | D+55 days |
| Estimated Read | If IDR unavailable | Corrected at final |

### 7.2 Common Settlement Disputes

Frequent causes of settlement disputes and resolution paths:

| Issue | Resolution | Timeline |
|-------|-----------|----------|
| Missing meter data (estimated read used) | Submit corrected IDR data via ERCOT portal | Up to D+55 for auto-correction |
| Resource node misassignment | Submit node correction form to ERCOT Settlements | 5 business days |
| COAS/HASL discrepancy | Review SCED outputs; dispute via Market Issues process | 10 business days |
| CRR haircut dispute | Haircut factors are non-disputable; escalate if calculation error | 15 business days |

---

## 8. Invoice Components Summary

A typical monthly ERCOT invoice includes:

| Line Item | Direction | Notes |
|-----------|-----------|-------|
| DAM Energy Settlement | Credit/Charge | Net of all gen/load positions |
| DAM Ancillary Service Payment | Credit | For AS awards |
| RT Energy Imbalance | Credit/Charge | 15-min actual vs DAM schedule |
| Uninstructed Deviation Charges | Charge | If applicable |
| CRR Settlements | Credit/Charge | If CRR account holder |
| PCM Performance Credits | Credit | If resource had PCH output |
| PCM Load Obligation | Charge | For load-serving QSEs |
| RUC Guarantee | Credit | For RUC-committed resources |
| Administrative Fees | Charge | ERCOT admin fee (~$0.10/MWh) |
| PUCT Assessment | Charge | ~0.05% of load-weighted SPP |

**Interest on Late Payments:** 1.5% per month (18% annualized) on outstanding balances past due date.

---

## 9. Worked Example: Simple QSE Settlement

**Scenario:** QSE Alpha operates a 200 MW gas peaker in the Houston Zone. For HE 15 (3:00–4:00 PM) on a summer weekday:

| Parameter | Value |
|-----------|-------|
| DAM Award | 200 MW at HB_HOUSTON |
| DAM SPP (HB_HOUSTON) | $125/MWh |
| Actual output (all 4 intervals avg) | 185 MW |
| RT SPP (avg, all 4 intervals) | $210/MWh |
| SCED dispatch instruction | 195 MW |

**Calculations:**

1. **DAM Energy Payment:** 200 MW × $125/MWh × 1 hr = **+$25,000**

2. **RT Imbalance Settlement:**  
   (185 MW – 200 MW) × $210/MWh × 1 hr = -15 MW × $210 = **-$3,150**  
   *(QSE under-delivered vs DAM schedule; pays at RT price)*

3. **Uninstructed Deviation:**  
   Actual 185 MW vs Instruction 195 MW = -10 MW deviation  
   10 MW < 25 MW threshold → **No UD charge this interval**

4. **Net Settlement for HE 15:**  
   $25,000 – $3,150 = **+$21,850**

---

*For settlement questions: settlements@ercot.com | (512) 248-3900*  
*ERCOT Settlement Calculator tool available on ERCOT MIS portal.*
