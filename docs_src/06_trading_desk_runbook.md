# Power Trading Desk — Operational Runbook
## ERCOT Real-Time & Day-Ahead Desk
### Version 3.1 | Last Updated: September 2024
### INTERNAL USE ONLY — PROPRIETARY AND CONFIDENTIAL

---

> **This document is for authorized desk personnel only. Do not distribute externally.
> Print copies are uncontrolled — always reference SharePoint (TradingOps › Runbooks) for the current version.**

---

## 1. Desk Structure and Responsibilities

### 1.1 Desk Roles

| Role | Responsibilities | Coverage |
|------|----------------|----------|
| **DAM Trader** | DAM offer strategy, AS bids, self-schedule optimization | 06:00–16:00 CPT |
| **RT Trader** | SCED monitoring, real-time dispatch, imbalance management | 24/7 (3 shifts) |
| **Scheduling Coordinator** | COAS maintenance, outage scheduler, ERCOT portal submissions | 06:00–18:00 CPT |
| **Settlements Analyst** | Invoice review, dispute tracking, meter data | 08:00–17:00 CPT |
| **Risk On-Call** | VaR breach, emergency escalation | 24/7 (pager) |

### 1.2 Shift Handover Checklist

Every shift change, the outgoing trader must verbally brief and document the following in the Shift Log (SharePoint › TradingOps › Shift Logs):

- [ ] Open positions vs. DAM awards — any material imbalance?
- [ ] Active outages (unit forced outages; expected return times)
- [ ] Binding constraints affecting portfolio nodes
- [ ] Any open CRR positions with unusual congestion exposure
- [ ] Market alerts / ERCOT notices received this shift
- [ ] Any limit breaches (VaR, position, loss) — even if resolved
- [ ] Pending ERCOT communications requiring follow-up
- [ ] System anomalies (SCED data gaps, metering issues)

---

## 2. Day-Ahead Market Procedures

### 2.1 DAM Offer Preparation (06:30–09:30 CPT)

**Step 1: Load forecast pull**
```
1. Open ERCOT MIS portal → Forecasts → ERCOT Load Forecast
2. Download 72-hour forecast CSV for operating day
3. Paste into DeskTools > DAM_LoadForecast tab
4. Flag any hour where ERCOT forecast deviates >5% from internal model
```

**Step 2: Gas price check**
```
1. Pull Henry Hub prompt-month + basis: Bloomberg NGASGSHH
2. Pull Katy Hub (NGASKS KATY) and Waha Hub (NGASKS WAHA) basis
3. Update DeskTools > FuelCost tab:
   - Gas_price_south = HH + Katy_basis + transport_adder
   - Gas_price_west = HH + Waha_basis + transport_adder
   - Default transport: South $0.35/MMBtu, West $0.28/MMBtu (review quarterly)
```

**Step 3: Heat rate optimization**
```
For each gas unit in portfolio:
1. Calculate breakeven LMP = (Gas_price / HR) + VOM
   Example: $3.20/MMBtu ÷ 8.5 MMBtu/MWh + $2.50 VOM = $40.18/MWh
2. Set DAM offer stack:
   - 0–50% output:   breakeven – $2  (ensure minimum dispatch)
   - 50–80% output:  breakeven + $1
   - 80–100% output: breakeven + $5
3. For peakers (CT units): offer only above breakeven + $15 unless system is tight
```

**Step 4: COAS verification**
```
Before 09:45 CPT (15 min before DAM close):
1. Log into ERCOT Nodal portal → Resource Management → COAS
2. Verify all online units show COAS ≥ expected dispatch level
3. For units on planned outage: confirm COAS = 0, outage ticket open
4. Any COAS discrepancy: contact Scheduling Coordinator IMMEDIATELY
   Escalate if not resolved by 09:55 → call Market Operations (512) 248-3900
```

**Step 5: Submit offers**
```
DEADLINE: 09:58 CPT (2-minute buffer before 10:00 close)
1. DeskTools → DAM Submission → Export to ERCOT XML format
2. Upload via ERCOT API or MIS portal
3. Confirm submission receipt — screenshot to Shift Log
4. If portal unresponsive: call (512) 248-3000 QSE hotline immediately
```

### 2.2 DAM Results Review (13:30–15:00 CPT)

When DAM results publish (~13:30):
1. Pull results: ERCOT MIS → Markets → DAM → Results (operating day)
2. Verify awards match submitted offers (check each resource node)
3. Calculate net DAM position:
   - **DAM long:** awarded generation > load → watch RT short risk
   - **DAM short:** awarded load > generation → watch RT long risk (exposure to high RT prices)
4. Update Risk System (Oati Workbench) with DAM awards
5. Flag any resource not awarded despite being economic → review offer

**DAM Short-Position Alert:**
If net DAM short > 200 MW entering on-peak, notify Risk Desk.
If short > 500 MW, risk officer must acknowledge and approve exposure or authorize hedge.

---

## 3. Real-Time Trading Procedures

### 3.1 Continuous Monitoring

**Primary monitors (always visible):**
- ERCOT Operations Dashboard — https://www.ercot.com/gridmgr/dashbd
- Internal SCED tracking tool (real-time vs. dispatch instruction delta)
- System frequency (target: 60.00 ± 0.02 Hz)
- Operating reserve level (alert threshold: < 2,500 MW)
- LMP ticker: HB_NORTH, HB_HOUSTON, HB_SOUTH, HB_WEST

### 3.2 Real-Time Price Spike Protocol

**Trigger:** Settlement point price > $250/MWh for two consecutive 5-min intervals.

```
IMMEDIATE ACTIONS:
1. Identify cause: ERCOT bulletin? Congestion? Reserve shortage?
   → Check ERCOT Nodal messaging for active notices
2. Assess portfolio exposure:
   → RT long: benefit from spike (hold unless reserves collapsing)
   → RT short: LOSS exposure — evaluate curtailment options immediately
3. If RT price > $500/MWh and persisting:
   → Call Risk On-Call: internal x2200
   → Deploy any available demand response
4. Log all actions in Shift Log with timestamps
5. Do NOT make bilateral trades to cover unless approved by Risk (> $1M exposure)
```

**Trigger:** Price > $2,000/MWh (approaching emergency offer cap)
```
EMERGENCY PROTOCOL:
1. Notify Risk Officer immediately (call, not message)
2. If generation offline and capable of starting: evaluate emergency startup
   → Authorization required from Shift Supervisor for startup cost > $500K
3. If short position: accept losses; do not chase with bilaterals at extreme prices
4. Document everything — ERCOT Market Monitoring reviews all such events
```

### 3.3 SCED Uninstructed Deviation Prevention

```
Every 30 minutes (RT shift):
1. Check SCED dashboard — actual output vs. HASL dispatch instruction
2. Deviation > 10 MW for > 2 intervals: investigate immediately
   Causes: governor droop, fuel supply issue, plant control error
3. Call plant control room if deviation persists > 10 minutes
4. If plant cannot comply: report to ERCOT Operations (512) 248-3900
   State: "Resource [name] unable to follow DI due to [reason]"
```

---

## 4. Risk Limits and Breach Procedures

### 4.1 Trading Limits (Q3 2024)

| Limit | Alert | Hard Stop |
|-------|-------|-----------|
| Daily P&L Loss | -$300K | -$500K |
| Weekly P&L Loss | -$1.0M | -$1.5M |
| Net Open Position — RT | ±700 MWh | ±1,000 MWh |
| Net Open Position — DAM | ±3,500 MWh | ±5,000 MWh |
| Value at Risk (1-day 95%) | $600K | $800K |
| Single-node concentration | 200 MW | 300 MW |

**HARD STOP = NO FURTHER TRADING WITHOUT RISK OFFICER APPROVAL.**
Trading through a hard stop without approval is grounds for immediate suspension.

### 4.2 End-of-Day P&L Reconciliation

By 18:00 CPT each trading day:
1. Pull preliminary RT settlement data (ERCOT MIS → Settlements → Preliminary)
2. Reconcile against DeskTools P&L tracker
3. Calculate DAM vs. RT basis (DAM position P&L vs. RT settlement)
4. Email daily flash P&L to: Trading Manager, Risk Officer, CFO (if daily loss > $200K)

---

## 5. Technology Failure Procedures

### 5.1 ERCOT MIS Portal Unavailable

```
1. Wait 5 minutes — brief outages are common
2. If > 5 min: call ERCOT QSE Help Desk (512) 248-3000
3. If portal down at DAM close: ERCOT accepts faxed offers (legacy)
   Fax: (512) 248-5765 — Scheduling Coordinator sends immediately
4. ERCOT grants deadline extensions for confirmed system-wide outages
   Get extension confirmation number and log it
```

### 5.2 Internal Systems Down

```
1. Switch to ERCOT MIS directly for all market operations
2. Use backup manual offer calculator:
   SharePoint → TradingOps → Emergency → Manual_Offer_Calculator.xlsx
3. Two-person sign-off required for any offer submission during system outage
4. IT Help Desk: x4444 internal | (512) 555-4444 external
5. After-hours emergency IT: (512) 555-9999
```

---

## 6. Contacts Quick Reference

| Contact | Number |
|---------|--------|
| ERCOT Market Operations (24/7) | (512) 248-3900 |
| ERCOT QSE Help Desk | (512) 248-3000 |
| Risk Officer On-Call | Internal x2200 |
| Shift Supervisor (after-hours) | Internal x2100 |
| Plant Control — South Gas Portfolio | (361) 555-2300 |
| Plant Control — North Gas Portfolio | (214) 555-8800 |
| IT Emergency | (512) 555-9999 |
| Legal (urgent contract matters) | Internal x3310 |

---

*This runbook is reviewed quarterly. Submit corrections to tradingops@company.com.*
*Next scheduled review: December 2024*
