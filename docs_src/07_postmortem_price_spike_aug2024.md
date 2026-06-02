# Incident Postmortem — ERCOT Price Spike Event
## Incident ID: INC-2024-0823
### Date of Incident: August 23, 2024 | 14:00–17:45 CPT
### Postmortem Completed: August 30, 2024
### Severity: SEV-1 (Trading Loss > $400K; Emergency Protocol Activated)
### CONFIDENTIAL — INTERNAL DISTRIBUTION ONLY

---

## Executive Summary

On August 23, 2024, ERCOT real-time settlement point prices at the HB_SOUTH and HB_HOUSTON hubs spiked to $3,800–$4,900/MWh during the hours ending 15:00–18:00 CPT, driven by a combination of unforecasted demand surge, forced outage of a 750 MW combined-cycle unit, and a binding 345kV transmission constraint on the Houston Import Limit. The firm held a net short position of approximately 320 MW during the spike window, resulting in a realized mark-to-market loss of $427,000 over the 15:00–18:00 CPT window. The incident triggered emergency risk protocols, activated demand response reserves, and required post-event reconciliation with the ERCOT Market Monitor.

---

## Timeline of Events

| Time (CPT) | Event |
|------------|-------|
| 06:30 | DAM offer process begins. Internal load forecast: 73,400 MW peak. ERCOT public forecast: 72,900 MW. |
| 09:58 | DAM offers submitted. Net portfolio position: long 85 MW vs. DAM award. |
| 11:15 | Weather service updates — forecast temperatures revised upward by 4°F for Houston metro area. Desk notified; no position change made. |
| 13:22 | Unit SGAS-04 (750 MW CCGT, Fayette County) trips on turbine rotor vibration alarm. Forced outage notification filed with ERCOT. |
| 13:30 | DAM results show firm awarded 1,240 MWh short across HB_SOUTH node. RT position now critically short. |
| 13:45 | RT trader notes reserve level declining — 3,100 MW. Shift Supervisor alerted. |
| 14:05 | ERCOT issues Operating Condition Notice (OCN): system-wide reserves below 2,500 MW. Emergency import requests to neighboring regions activated. |
| 14:20 | HB_SOUTH RT LMP: $487/MWh. Alert threshold breached. Risk On-Call notified (x2200). |
| 14:35 | Houston Import Limit (HIL) constraint goes binding — 345kV Silsbee-Beaumont line at 98% loading. Congestion component contributes $1,200/MWh to HB_SOUTH LMP. |
| 14:50 | Risk Officer authorizes demand response activation (75 MW available). DR activated at 14:53. |
| 15:00 | HB_SOUTH LMP reaches $3,847/MWh. HB_HOUSTON: $4,120/MWh. |
| 15:30 | Second CCGT (SGAS-07, 500 MW) brought to warm-start; expected online 17:00. |
| 16:00 | ERCOT Emergency Energy Alert (EEA) Level 1 declared. |
| 17:00 | SGAS-07 synchronized to grid. Reserve level recovers to 2,800 MW. |
| 17:30 | HB_SOUTH LMP falls to $189/MWh as congestion clears. |
| 17:45 | EEA Level 1 lifted. System normal. Prices return to $65–$95/MWh range. |
| 18:30 | Daily P&L flash: realized loss -$427K, within weekly limit. Risk Officer closes emergency protocol. |

---

## Root Cause Analysis

### Primary Causes

**1. Weather forecast miss (+4°F)**
The morning weather update raised Houston forecast temperatures by 4°F for the afternoon hours. This translated to approximately 1,800–2,200 MW of additional demand versus the DAM forecast. The desk was aware of the revision at 11:15 but did not re-evaluate the DAM short position. This is the primary operational failure.

**2. Coincident forced outage (SGAS-04)**
The 750 MW trip at 13:22 removed ~3% of south Texas generation capacity at precisely the moment load was surging. The combined effect of the demand over-forecast and the generation loss created a ~2,500 MW supply shortfall in the southern zone.

**3. Transmission constraint activation (HIL)**
The Houston Import Limit binding was not forecast in the morning congestion model. The constraint isolated HB_SOUTH and HB_HOUSTON from cheaper generation in HB_NORTH, amplifying the price spike to extreme levels and preventing effective hedging.

### Contributing Factors

- **Position review gap:** No process exists to re-evaluate open RT exposure following material weather forecast revisions. The 11:15 revision should have triggered a position review.
- **Demand response activation delay:** DR was not activated until 14:50, approximately 45 minutes after the first alert. DR procedures require manual approval chain that added 25 minutes.
- **SGAS-07 warm-start delay:** Warm-start procedures took 90 minutes from authorization to synchronization. Pre-positioning SGAS-07 in warm standby during high-temperature forecasts was not standard practice.

---

## Financial Impact

| Category | Amount |
|----------|--------|
| RT imbalance charges (short position) | -$641,200 |
| Demand response activation offset | +$87,400 |
| SGAS-07 emergency start fuel cost | -$38,500 |
| DAM award revenue | +$165,300 |
| **Net realized loss** | **-$427,000** |

---

## What Went Well

1. **Risk escalation worked.** Once the $250/MWh threshold was breached, Risk On-Call was notified within 15 minutes per protocol.
2. **Demand response executed correctly** once authorized — all 75 MW of DR performed as contracted.
3. **No compliance violations.** All SCED instructions were followed; no uninstructed deviations during the event.
4. **Communication with ERCOT was timely.** Forced outage notifications for both SGAS-04 and SGAS-07 (emergency start) were filed correctly.

---

## Action Items

| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | Add "Weather Revision Trigger" step to RT monitoring checklist: any ≥3°F intra-day revision triggers mandatory position review | Trading Manager | Sep 15, 2024 | OPEN |
| 2 | Reduce DR activation approval chain from 3 approvers to 2 for events where LMP > $300/MWh | Risk Officer | Sep 20, 2024 | OPEN |
| 3 | Define "pre-warm standby" policy: SGAS-07 and SGAS-11 to be held in warm standby on days where H+36 ERCOT load forecast exceeds 73,000 MW | Plant Operations | Oct 1, 2024 | OPEN |
| 4 | Back-test congestion model against HIL constraint — determine if model should include HIL sensitivity in morning congestion forecast | Analytics Team | Sep 30, 2024 | OPEN |
| 5 | Update VaR model to include extreme weather scenario stress test (1-in-10-year heat event) | Risk Analytics | Oct 15, 2024 | OPEN |
| 6 | Conduct tabletop drill for EEA Level 1 scenario with full desk (quarterly going forward) | Desk Manager | Sep 30, 2024 | OPEN |

---

## Lessons Learned

> *"The weather revision was on the board at 11:15. In retrospect, the question isn't why the spike happened — it's why we didn't move when we had the data."*
> — Senior RT Trader (post-incident debrief)

This incident confirms that **intra-day information triggers must be systematically linked to position review obligations**. Awareness of a weather revision is not sufficient; the runbook must mandate a position review whenever material forecast changes occur.

Separately, the congestion model's failure to anticipate HIL binding under a high-load scenario highlights a structural gap in the morning risk assessment. The HIL is a known constraint; it should be part of standard pre-market scenario analysis on days forecast above 71,000 MW.

---

## Review and Sign-Off

| Role | Name | Date |
|------|------|------|
| Incident Lead | J. Harrington | Aug 30, 2024 |
| Trading Manager | M. Castillo | Aug 30, 2024 |
| Risk Officer | D. Nguyen | Aug 30, 2024 |
| Compliance | A. Patel | Sep 2, 2024 |

*This postmortem is filed under INC-2024-0823 in the Incident Management System.*
*Distribution: Trading, Risk, Compliance, Legal. Do not forward externally.*
