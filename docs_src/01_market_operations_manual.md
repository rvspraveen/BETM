# ERCOT Market Operations Manual
## Version 4.2 | Effective Date: January 1, 2024
### Document Control: ERCOT-MOM-2024-04.2

---

## Foreword

This Manual governs the day-to-day operational conduct of the Electric Reliability Council of Texas (ERCOT) wholesale electricity markets. It is binding on all Qualified Scheduling Entities (QSEs), Transmission and Distribution Service Providers (TDSPs), Generation Resources, and Load Resources participating in ERCOT markets. This version supersedes MOM v4.1 (effective April 2023) and incorporates revisions arising from ERCOT Nodal Protocol Revision Requests (NPRRs) 1142, 1158, and 1177.

---

## Chapter 1: Market Structure Overview

### 1.1 Market Segments

ERCOT operates three primary market segments:

**Day-Ahead Market (DAM)**
The DAM opens at 06:00 CPT and closes at 10:00 CPT each day for the operating day beginning at hour-ending 01:00 the following day. Participants submit energy offers, ancillary service offers, load resource bids, and self-schedules. ERCOT clears the DAM using a co-optimization algorithm that simultaneously clears energy, Regulation Service (Reg), Responsive Reserve Service (RRS), Non-Spinning Reserve Service (NSRS), and ERCOT Contingency Reserve Service (ECRS).

**Real-Time Market (RTM)**
The RTM operates continuously. Security-Constrained Economic Dispatch (SCED) runs every 5 minutes to dispatch generation and controllable load resources. Settlement Point Prices (SPPs) are calculated at each settlement interval.

**Ancillary Services Market**
AS procurement occurs during the DAM and via Real-Time AS Deployment. ERCOT procures:
- Regulation Up (Reg-Up): ±300 MW minimum system procurement
- Regulation Down (Reg-Down): ±300 MW minimum system procurement
- Responsive Reserve Service (RRS): 2,800 MW minimum (includes UFLS obligation)
- ERCOT Contingency Reserve Service (ECRS): 3,000 MW target
- Non-Spinning Reserve Service (NSRS): 5,000 MW target

### 1.2 Settlement Points

Settlement Points are the pricing locations used in ERCOT markets:

| Type | Description | Count (2024) |
|------|-------------|--------------|
| Load Zone | Four load zones (LZ_HOUSTON, LZ_NORTH, LZ_SOUTH, LZ_WEST) | 4 |
| Hub | Aggregate pricing hubs (HB_BUSAVG, HB_NORTH, HB_HOUSTON, HB_SOUTH, HB_WEST, HB_PAN) | 6 |
| Resource Node | Individual generator pricing nodes | ~600 |
| Electrical Bus | Bus-level pricing points | ~4,000 |

**Key Hubs and Aliases (Trading Desk Reference)**

| Commercial Alias | ERCOT Settlement Point | Zone |
|-----------------|----------------------|------|
| ERCOT North | HB_NORTH | North |
| ERCOT Houston | HB_HOUSTON | Houston |
| ERCOT South | HB_SOUTH | South |
| ERCOT West | HB_WEST / HB_PAN | West |
| ERCOT Bus Average | HB_BUSAVG | System |
| North Load Zone | LZ_NORTH | North |
| Houston Load Zone | LZ_HOUSTON | Houston |

### 1.3 Locational Marginal Pricing (LMP)

The Locational Marginal Price at any settlement point is computed as:

```
LMP = MCP_energy + MCP_congestion + MCP_loss
```

Where:
- **MCP_energy** = System-wide marginal cost of energy (shadow price of system energy balance constraint)
- **MCP_congestion** = Sum of shift factor × shadow price for all binding transmission constraints
- **MCP_loss** = Marginal cost of transmission losses at the node

---

## Chapter 2: Day-Ahead Market Operations

### 2.1 DAM Timeline (All times Central Prevailing Time)

| Time | Activity |
|------|----------|
| D-1 06:00 | DAM opens; QSEs may submit offers/bids |
| D-1 09:00 | Preliminary Constraint Management Plan (CMP) published |
| D-1 10:00 | DAM closes; no further offer/bid changes accepted |
| D-1 10:00–13:00 | ERCOT runs co-optimization; resolves transmission security |
| D-1 13:30 | DAM results published (awards, SPPs, AS obligations) |
| D-1 14:00 | QSE notification deadline for DAM award acceptance |
| D-1 18:00 | Updated CMP reflecting DAM awards published |

### 2.2 Offer Structure

**Energy Offers (EOs)**
QSEs submit energy offers for each resource as a step-function of price–quantity pairs:
- Maximum 20 price–quantity pairs per resource per hour
- Price range: -$250/MWh to $5,000/MWh (Low Systemwide Offer Cap to High SWCAP)
- Offers must be submitted in 1 MW increments
- Minimum offer quantity: 1 MW

**Capacity Assessment (COAS)**
Resources must maintain Capacity Assessment Output Schedules (COAS) updated no later than 3 hours prior to the operating hour. COAS changes after gate closure require curtailment notice.

### 2.3 DAM Price Caps

| Parameter | Value | Notes |
|-----------|-------|-------|
| Low Systemwide Offer Cap (Low SWCAP) | -$250/MWh | Applies when reserves adequate |
| High Systemwide Offer Cap (High SWCAP) | $5,000/MWh | Applies when reserves adequate |
| Emergency offer cap | $9,000/MWh | Triggered by EEA Level 1 or higher |
| Voltage support cap | $1,000/MWh | For reliability-must-run resources |

---

## Chapter 3: Real-Time Market Operations

### 3.1 SCED Dispatch

Security-Constrained Economic Dispatch (SCED) executes every 5 minutes. The SCED objective minimizes total offer cost subject to:
1. System energy balance
2. Transmission security constraints (thermal, stability, voltage)
3. Resource ramp rate limits
4. Minimum/maximum resource output limits
5. Ancillary service deployment

**SCED Inputs:**
- Current telemetry (MW output, status) from all resources ≥10 MW
- Remaining offer curves (not yet deployed in DAM)
- Network model (updated nightly; intrahour topology changes via switching)
- Load forecast (updated every 15 minutes from telemetry extrapolation)

### 3.2 Real-Time Settlement Point Prices

Real-Time SPPs are calculated at 15-minute settlement intervals by averaging the four 5-minute SCED LMPs within each interval. SPPs are published within 30 minutes of interval close.

### 3.3 Congestion Revenue Rights (CRRs)

CRRs are financial instruments that hedge against congestion cost between two settlement points. CRR holders receive (or pay) the congestion component of the price difference between sink and source nodes, proportional to their CRR MW holding.

**Annual CRR Auction:** Conducted each October for the following calendar year.  
**Monthly CRR Auction:** Conducted the third week of the prior month.  
**Reconfiguration Auctions:** Conducted weekly for the upcoming week.

---

## Chapter 4: Transmission Constraints and Congestion Management

### 4.1 Binding Constraint Management

When a transmission element reaches its security limit, ERCOT constrains dispatch through SCED re-dispatch. The congestion cost is reflected in LMP spreads between settlement points on opposing sides of the constraint.

**Frequently Binding Paths (2023 Historical)**

| Constraint Name | Element | Avg Congestion Cost (2023) |
|----------------|---------|--------------------------|
| Midland-Odessa 138kV | Permian Basin export | $12.4M |
| Houston Import Limit | Gulf Coast thermal interface | $8.9M |
| Panhandle Wind Export | West Texas 345kV | $22.1M |
| RIO CRR segment | South Texas nuclear export | $6.3M |

### 4.2 Reliability Unit Commitment (RUC)

When the DAM clearing results in projected reliability violations, ERCOT issues RUC commitments. RUC-committed resources receive:
- RUC Guarantee payment if their offer cost exceeds SCED dispatch revenue
- Resources are obligated to follow ERCOT dispatch instructions

---

## Chapter 5: Ancillary Services Operations

### 5.1 Ancillary Service Definitions

**Regulation Service**
Resources providing Regulation must respond automatically to Automatic Generation Control (AGC) signals within 1 second. Regulation resources must maintain a continuous ramp capability of at least 8 MW/min.

**Responsive Reserve Service (RRS)**
RRS resources must be capable of arresting frequency decline within 20 seconds of a contingency event. At least 50% of the RRS obligation must be held by resources with Under-Frequency Load Shedding (UFLS) capability set at 59.3 Hz.

**ECRS (Effective June 2023)**
ECRS was introduced following Winter Storm Uri lessons learned. ECRS resources must be deployable within 10 minutes and must maintain a 30-minute sustained output capability.

### 5.2 AS Deployment and Activation

| Service | Activation Trigger | Response Time |
|---------|-------------------|---------------|
| Reg Up | AGC signal | < 1 second |
| Reg Down | AGC signal | < 1 second |
| RRS | Frequency < 59.91 Hz | < 20 seconds |
| ECRS | ERCOT instruction | < 10 minutes |
| NSRS | ERCOT instruction | < 30 minutes |

---

## Chapter 6: Market Monitoring and Mitigation

### 6.1 Market Surveillance

The ERCOT Market Monitoring division monitors all market activity in real time. Automated surveillance flags:
- Offers deviating >300% from 90-day rolling average offer price
- Sudden capacity withdrawals >500 MW within 2 hours of operating hour
- Repeated self-scheduling at uneconomic prices (potential DEC gaming)
- Physical withholding: resource online but submitting above-SWCAP offers

### 6.2 Offer Cap Mitigation

Under PUCT rule 25.505(g), ERCOT may apply offer caps to resources found to have market power in constrained areas. Mitigation applies the resource's 90-day weighted average offer curve or ERCOT's estimate of short-run marginal cost, whichever is lower.

---

## Chapter 7: Emergency Operations

### 7.1 Emergency Electric Advisory (EEA) Levels

| Level | Trigger | Actions |
|-------|---------|---------|
| EEA Level 1 | Operating reserves < 2,300 MW | Conservation appeal, emergency offer cap activation |
| EEA Level 2 | Operating reserves < 1,750 MW | Firm load interruptions authorized, interregional emergency assistance |
| EEA Level 3 | Operating reserves < 1,000 MW | Controlled outages, UFLS relay activation risk |

### 7.2 Load Shedding Protocol

Controlled outages (rotating outages) are implemented at the TDSP level under ERCOT instruction. Each rotating outage block is approximately 30 minutes duration. ERCOT targets restoration within 10–15 minutes when reserves recover above EEA Level 1 threshold.

---

## Appendix A: Key Contacts

| Function | Contact | Hours |
|---------|---------|-------|
| Market Operations Hotline | (512) 248-3900 | 24/7 |
| QSE Help Desk | (512) 248-3000 | 24/7 |
| CRR Desk | (512) 248-3400 | 06:00–18:00 CPT |
| Settlements Inquiries | settlements@ercot.com | Business hours |

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| AGC | Automatic Generation Control |
| COAS | Capacity Assessment Output Schedule |
| CRR | Congestion Revenue Right |
| DAM | Day-Ahead Market |
| ECRS | ERCOT Contingency Reserve Service |
| EEA | Emergency Electric Advisory |
| LMP | Locational Marginal Price |
| NSRS | Non-Spinning Reserve Service |
| QSE | Qualified Scheduling Entity |
| RRS | Responsive Reserve Service |
| RTM | Real-Time Market |
| RUC | Reliability Unit Commitment |
| SCED | Security-Constrained Economic Dispatch |
| SPP | Settlement Point Price |
| SWCAP | Systemwide Offer Cap |
| TDSP | Transmission and Distribution Service Provider |
| UFLS | Under-Frequency Load Shedding |

---

*This document is maintained by the ERCOT Market Operations group. Questions regarding interpretation should be directed to marketrules@ercot.com. Revision history is maintained in the ERCOT Document Management System.*
