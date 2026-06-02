# ERCOT Congestion Revenue Rights (CRR) Auction Rules
## Calendar Year 2024
### Document: ERCOT-CRR-RULES-2024 | Effective: January 1, 2024

---

## Part I: General Provisions

### Article 1: Purpose and Scope

These Auction Rules govern the conduct of Congestion Revenue Rights (CRR) auctions administered by the Electric Reliability Council of Texas (ERCOT) pursuant to ERCOT Protocols Section 7 and PUCT Substantive Rule 25.501. CRR auctions provide market participants a mechanism to hedge against Day-Ahead Market congestion costs between any two Settlement Points in the ERCOT network.

CRRs entitle or obligate their holders to receive the congestion component of the Settlement Point Price difference between the CRR sink and CRR source, for each MWh of CRR MW quantity, during each Settlement Interval in the CRR obligation period.

**CRR Payoff Formula:**
```
CRR_payment = CRR_MW × (SPP_sink_congestion - SPP_source_congestion) × settlement_hours
```

Where congestion components are derived from DAM LMP decomposition.

---

### Article 2: CRR Types

| CRR Type | Description | Obligation/Option |
|----------|-------------|------------------|
| **Point-to-Point (PTP) Obligation** | Fixed right/obligation to receive congestion spread | Obligation — pays or receives |
| **PTP Option** | Right (not obligation) to receive positive congestion spread | Option — receives positive; $0 floor |
| **Network Service Upgrade (NSU) CRR** | Issued to entities funding network upgrades | Long-term obligation; non-auctionable |

**Primary products auctioned:** PTP Obligations and PTP Options  
**Note:** PTP Options carry a premium cost; PTP Obligations are cleared at zero upfront cost with positive/negative annual value.

---

### Article 3: Eligible Participants

The following entities may participate in CRR auctions:

1. Qualified Scheduling Entities (QSEs) registered with ERCOT
2. Load-Serving Entities (LSEs) with an executed ERCOT Market Participation Agreement
3. CRR Account Holders — entities registered solely for CRR participation (financial players)
4. Transmission and Distribution Service Providers (TDSPs) for load-obligation hedges

**Registration Requirements:**
- Active ERCOT Market Participation Agreement (MPA)
- Minimum creditworthiness: BBB- (S&P) or Baa3 (Moody's), or cash/letter of credit equal to 25% of maximum potential CRR obligation
- Completion of ERCOT CRR System training (certification required annually)

---

## Part II: Auction Schedule and Products

### Article 4: Auction Calendar 2024

#### 4.1 Annual CRR Auction

| Phase | Period | Activity |
|-------|--------|----------|
| Open Enrollment | Oct 7–11, 2024 | New participant registration deadline |
| Offer Submission Round 1 | Oct 21–25, 2024 | Long/short position submissions |
| Clearing Round 1 | Oct 28, 2024 | ERCOT publishes Round 1 results |
| Offer Submission Round 2 | Oct 29–Nov 1, 2024 | Residual capacity bidding |
| Clearing Round 2 | Nov 4, 2024 | Final annual results |
| Settlement | Nov 15, 2024 | Upfront payments/receipts settled |
| Obligation Start | Jan 1, 2025 | Annual CRRs become effective |

#### 4.2 Monthly CRR Auction Schedule (2024)

| Month | Bid Window Opens | Bid Window Closes | Results Published | Obligation Starts |
|-------|-----------------|------------------|------------------|------------------|
| January | Dec 11, 2023 | Dec 15, 2023 | Dec 18, 2023 | Jan 1, 2024 |
| February | Jan 15, 2024 | Jan 19, 2024 | Jan 22, 2024 | Feb 1, 2024 |
| March | Feb 12, 2024 | Feb 16, 2024 | Feb 19, 2024 | Mar 1, 2024 |
| April | Mar 11, 2024 | Mar 15, 2024 | Mar 18, 2024 | Apr 1, 2024 |
| May | Apr 15, 2024 | Apr 19, 2024 | Apr 22, 2024 | May 1, 2024 |
| June | May 13, 2024 | May 17, 2024 | May 20, 2024 | Jun 1, 2024 |
| July | Jun 10, 2024 | Jun 14, 2024 | Jun 17, 2024 | Jul 1, 2024 |
| August | Jul 15, 2024 | Jul 19, 2024 | Jul 22, 2024 | Aug 1, 2024 |
| September | Aug 12, 2024 | Aug 16, 2024 | Aug 19, 2024 | Sep 1, 2024 |
| October | Sep 16, 2024 | Sep 20, 2024 | Sep 23, 2024 | Oct 1, 2024 |
| November | Oct 14, 2024 | Oct 18, 2024 | Oct 21, 2024 | Nov 1, 2024 |
| December | Nov 11, 2024 | Nov 15, 2024 | Nov 18, 2024 | Dec 1, 2024 |

#### 4.3 Weekly Reconfiguration Auction

Weekly auctions clear residual transmission capacity not allocated in Annual or Monthly auctions. Bid windows open Monday 08:00 CPT, close Tuesday 17:00 CPT, results published Wednesday 12:00 CPT.

---

### Article 5: Auction Products

#### 5.1 Standard Products

| Product | On-Peak Definition | Off-Peak Definition |
|---------|-------------------|---------------------|
| 24×7 (Flat) | All hours | — |
| On-Peak | HE 07–22 Mon–Fri, excl. NERC holidays | — |
| Off-Peak | All hours NOT in On-Peak | — |
| Super-Peak | HE 15–20 Mon–Fri, Jun–Sep | — |

#### 5.2 Popular Hedge Paths (2024 Reference)

| Source | Sink | Typical Annual Spread | Liquidity Rating |
|--------|----|----------------------|-----------------|
| HB_WEST | HB_NORTH | $8–$25/MWh off-peak | High |
| HB_PAN | HB_NORTH | $10–$30/MWh off-peak | High |
| HB_SOUTH | HB_HOUSTON | $2–$8/MWh | Medium |
| LZ_WEST | LZ_NORTH | $6–$20/MWh off-peak | High |
| HB_BUSAVG | LZ_HOUSTON | $1–$5/MWh | Medium |
| HB_NORTH | HB_HOUSTON | $0–$6/MWh | Medium |

---

## Part III: Bidding Rules

### Article 6: Bid Submission Requirements

**Bid Structure**
Each CRR bid must specify:
- CRR type (PTP Obligation or PTP Option)
- Source Settlement Point
- Sink Settlement Point
- Time period (Annual/Monthly/Weekly; hours)
- MW quantity (minimum 1 MW, maximum subject to simultaneous feasibility)
- Bid price ($/MWh, range: -$500 to $1,000 for obligations; $0 to $1,000 for options)

**Negative bids** on Obligations are permitted — a participant willing to accept a cash payment for taking on an obligation position may bid negative.

**Bid confidentiality:** All bids are anonymous during the auction period. Post-clearing, aggregate clearing statistics are published; individual bids remain confidential.

### Article 7: Simultaneous Feasibility Test (SFT)

ERCOT clears CRR auctions subject to the **Simultaneous Feasibility Test**, which verifies that the portfolio of all awarded CRRs is simultaneously flowable on the transmission network without violating any security constraint. The SFT uses ERCOT's full network model (admittance matrix) updated to reflect expected transmission topology for the obligation period.

**Infeasibility resolution:** When auction clearing encounters infeasibility, the algorithm iteratively reduces awarded quantities (starting with lowest-value bids) until a feasible solution is achieved.

---

## Part IV: Settlement and Clearing

### Article 8: CRR Revenue Adequacy

ERCOT settles CRRs using Day-Ahead congestion revenues collected from market participants. When total CRR payments exceed collected congestion revenues (revenue inadequacy), ERCOT applies a pro-rata haircut to all CRR holders' payments for that settlement period.

**Historical Revenue Adequacy (2023):**

| Quarter | Congestion Revenue Collected | CRR Obligations | Adequacy Ratio |
|---------|----------------------------|----------------|----------------|
| Q1 2023 | $142.3M | $138.7M | 100% (surplus $3.6M) |
| Q2 2023 | $89.4M | $94.2M | 94.9% (haircut applied) |
| Q3 2023 | $218.6M | $201.3M | 100% (surplus $17.3M) |
| Q4 2023 | $167.8M | $159.4M | 100% (surplus $8.4M) |

*Q2 2023 haircut: 5.1% reduction applied to all CRR holders for May–June 2023 congestion events.*

### Article 9: Transmission Upgrade CRR Allocation

Entities funding Transmission Upgrades (via Competitive Renewable Energy Zone (CREZ) credits or Direct Assignment Network Upgrades) receive NSU CRRs. These are allocated annually by ERCOT's Grid Planning department and are not subject to auction rules. NSU CRRs have 30-year terms and are fully tradeable after a 3-year lock-up period.

---

## Part V: Default and Credit

### Article 10: Credit Requirements

ERCOT evaluates each participant's creditworthiness monthly. Credit exposure is calculated as the maximum potential mark-to-market loss on open CRR positions using a 99th-percentile price scenario.

| Credit Rating | Unsecured Credit Limit |
|--------------|----------------------|
| AAA/Aaa | $50M |
| AA/Aa | $30M |
| A/A | $15M |
| BBB/Baa | $5M |
| BB/Ba or below | $0 (full collateral required) |

**Collateral types accepted:** Cash, irrevocable letter of credit (A-rated or better issuer), Treasury securities (at 95% face value).

### Article 11: Default Procedures

A CRR Account Holder in default (failure to post required collateral within 2 business days of ERCOT demand) shall have their CRR positions immediately transferred to ERCOT for liquidation. Proceeds offset the defaulting party's obligations; shortfalls are socialized pro-rata among all non-defaulting CRR participants.

---

*These rules are subject to the ERCOT Protocols and PUCT regulations. In the event of conflict, the Protocols and PUCT rules take precedence. Questions: crrauctions@ercot.com*
