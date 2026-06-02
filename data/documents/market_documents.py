"""
8 synthetic ERCOT market documents for RAG ingestion.
Each has realistic structure matching real ISO docs.
"""

DOCUMENTS = [
    {
        "title": "ERCOT Market Notice MN-2024-0892 — Brazos Valley Unit 3 Forced Outage",
        "doc_type": "market_notice",
        "source": "ERCOT Operations",
        "effective_date": "2024-06-15",
        "content": """ERCOT MARKET NOTICE
MN-2024-0892 | June 15, 2024 13:45 CDT | Priority: HIGH

SUBJECT: Forced Outage — Brazos Valley Unit 3 (750 MW), BUS_BRAZOS Injection Node

OUTAGE DETAILS:
  Resource Name   : Brazos Valley Unit 3
  Unit ID         : BV_UNIT3 / BUS_BRAZOS
  Capacity        : 750 MW (nameplate)
  Outage Start    : June 15, 2024 13:22 CDT
  Estimated Return: June 17, 2024 08:00 CDT
  Reason          : Forced — High exhaust temperature alarm; automatic trip on GT-3B

SYSTEM IMPACT:
  Available generation in the SOUTH zone immediately reduced by 750 MW.
  ERCOT deployed 600 MW of Responsive Reserve Service (RRS) and 150 MW of
  Emergency Response Service (ERS) to maintain frequency within NERC standards.

MARKET IMPACT ADVISORY:
  Real-time prices at HB_HOUSTON and LZ_HOUSTON elevated significantly.
  Sabine-Jasper 345kV line (SABINE_345) is simultaneously out of service for
  emergency maintenance (see MN-2024-1021). Combined effect: reduced import
  capability from East Texas combined with local supply loss. Traders with
  long positions at HB_HOUSTON nodes should monitor positions closely.

ASSOCIATED CONSTRAINT:
  SABINE_345 constraint activated 13:00 CDT — see constraint advisory
  CONST-ADVISORY-2024-0615.

ERCOT CONTACT: operations@ercot.com | 512-248-3000
""",
        "metadata": {"event_id": "A", "affects_nodes": ["HB_HOUSTON", "BUS_BRAZOS", "LZ_HOUSTON"]}
    },
    {
        "title": "ERCOT Market Notice MN-2024-1021 — Sabine-Jasper 345kV Emergency Outage",
        "doc_type": "market_notice",
        "source": "ERCOT Transmission",
        "effective_date": "2024-06-14",
        "content": """ERCOT MARKET NOTICE
MN-2024-1021 | June 14, 2024 22:15 CDT | Priority: CRITICAL

SUBJECT: Emergency Transmission Outage — Sabine-Jasper 345kV Line (SABINE_345)

OUTAGE DETAILS:
  Facility        : Sabine-Jasper 345kV Transmission Line
  Constraint ID   : SABINE_345
  Transfer Limit  : 1,000 MW (reduced to 0 MW during outage)
  Outage Start    : June 14, 2024 22:00 CDT
  Estimated Return: June 15, 2024 20:00 CDT
  Reason          : Emergency — insulator damage detected during patrol; risk of flashover

SECURITY ASSESSMENT:
  Without this line, Houston load pocket import capability reduced ~40%.
  N-1 security limit for HB_HOUSTON area: 2,800 MW (from 4,200 MW).
  ERCOT has pre-positioned generation reserves accordingly.

SETTLEMENT IMPLICATIONS:
  During the outage period, binding constraint SABINE_345 will generate
  significant congestion rent. CRR holders on Sabine-to-Houston paths
  will receive offsetting congestion rent credits per ERCOT Nodal Protocols
  Section 7.4.2 (CRR Auction Revenue Rights).

NOTE: Timing of this outage overlaps with Brazos Valley Unit 3 forced outage
(MN-2024-0892). Combined supply shortfall in Houston load pocket may cause
Real-Time prices to significantly exceed Day-Ahead prices.

ERCOT CONTACT: transmission@ercot.com
""",
        "metadata": {"event_id": "A", "affects_nodes": ["HB_HOUSTON", "BUS_SABINE"], "constraint": "SABINE_345"}
    },
    {
        "title": "ERCOT Nodal Protocols Section 4.4 — Ancillary Service Obligations",
        "doc_type": "protocol",
        "source": "ERCOT Nodal Protocols v14.2",
        "effective_date": "2024-01-01",
        "content": """ERCOT NODAL PROTOCOLS
Section 4.4 — Ancillary Service Obligations and Procurement

4.4.1 OVERVIEW
ERCOT procures Ancillary Services (AS) to maintain reliable system operation.
Market Participants with Qualified Scheduling Entities (QSEs) are subject to
AS obligations based on their load ratio share.

4.4.2 ANCILLARY SERVICE TYPES
(a) Responsive Reserve Service (RRS)
    - Minimum: 2,300 MW systemwide at all times
    - Response: Full deployment within 10 minutes of ERCOT instruction
    - Comprised of: Primary Frequency Response (PFR) + Controllable Load Resources

(b) Non-Spinning Reserve (Non-Spin)
    - Minimum: 1,750 MW
    - Response: Full deployment within 30 minutes
    - Used for: Next-contingency coverage

(c) Regulation Service (Reg-Up / Reg-Down)
    - Minimum: 300 MW each (Reg-Up and Reg-Down)
    - Response: Continuous automated response via AGC

(d) Emergency Response Service (ERS)
    - Voluntary load curtailment program
    - Response: 10-minute or 30-minute notification

4.4.3 QSE OBLIGATIONS
Each QSE's pro-rata share of AS obligations is calculated:
  AS_Obligation_QSE = (QSE_Load_MWh / Total_ERCOT_Load_MWh) × Total_AS_Requirement

Failure to meet obligations results in make-whole charges at the Real-Time
AS clearing price, plus an administrative surcharge of 110% per ERCOT
Operating Procedure OP-10.

4.4.4 CRR INTERACTION
Congestion Revenue Rights (CRRs) do not offset AS obligations. AS charges
are settlement-separate from energy and congestion components.

4.4.5 FORCE MAJEURE
During an Energy Emergency Alert (EEA) Level 2 or 3, ERCOT may:
  - Invoke Emergency Response Service contracts without prior notice
  - Direct QSEs to shed load on an emergency basis
  - Suspend AS obligation settlement for the duration of the emergency
""",
        "metadata": {"section": "4.4", "category": "ancillary_services"}
    },
    {
        "title": "ERCOT Settlement Guide — Day-Ahead and Real-Time Settlement Methodology",
        "doc_type": "settlement_guide",
        "source": "ERCOT Market Operations",
        "effective_date": "2024-03-15",
        "content": """ERCOT SETTLEMENT GUIDE
Day-Ahead and Real-Time Settlement Methodology
Revision 8.3 | Effective March 15, 2024

SECTION 1: SETTLEMENT OVERVIEW
ERCOT settles energy transactions in two market intervals:
  - Day-Ahead Market (DAM): Financially binding hour-ahead market
  - Real-Time Market (RTM): 15-minute Settlement Point Prices (SPP)

SECTION 2: DAY-AHEAD SETTLEMENT
2.1 Day-Ahead Prices
  Settlement Point Price (SPP_DA) = Energy Component + Congestion Component + Loss Component
  Settled at: Hourly intervals, posted by 18:00 CPT day prior

2.2 DA Obligation
  For each MWh scheduled in the DAM, the QSE pays/receives:
    DA_Charge = Quantity_MWh × SPP_DA(node)

SECTION 3: REAL-TIME SETTLEMENT
3.1 Real-Time Prices
  SPP_RT calculated every 15 minutes (settlement interval)
  ERCOT publishes preliminary SPPs within 3 business days; final within 55 days

3.2 RT Imbalance
  Imbalance = RT_Quantity - DA_Quantity
  RT_Imbalance_Charge = Imbalance_MWh × SPP_RT(node)

SECTION 4: NET SETTLEMENT
  Net_Settlement = DA_Charge + RT_Imbalance_Charge + AS_Charges + CRR_Credits

SECTION 5: SETTLEMENT RULE CHANGES (Effective March 15, 2024)
  Change 1: Loss factor calculation updated to use nodal loss factors (NLF)
    instead of zonal loss factors. Affects settlement for all physical resources.
  Change 2: CRR auction revenue allocation methodology updated per PUCT Order 56789.
    Shortfall allocation changed from pro-rata to counter-flow weighting.
  Change 3: RT price cap raised from $5,000/MWh to $5,000/MWh (no change to cap)
    but scarcity pricing adder rules updated — Low Systemwide Offer Cap (LCAP)
    triggers now at 1,750 MW reserve margin instead of 2,000 MW.

SECTION 6: DISPUTE RESOLUTION
  Settlement disputes must be filed within 45 calendar days of preliminary settlement.
  Use ERCOT Market Portal → Settlements → Dispute Filing.
""",
        "metadata": {"version": "8.3", "category": "settlement"}
    },
    {
        "title": "ERCOT Market Notice MN-2024-0941 — Wind Curtailment Advisory West Zone",
        "doc_type": "market_notice",
        "source": "ERCOT Operations",
        "effective_date": "2024-06-21",
        "content": """ERCOT MARKET NOTICE
MN-2024-0941 | June 21, 2024 19:30 CDT | Priority: MODERATE

SUBJECT: Wind Curtailment Advisory — West Zone Oversupply June 21-23

ADVISORY:
  ERCOT anticipates system-wide wind generation to exceed load + exports
  during low-load overnight periods on June 21-23, 2024 (approximately
  00:00 – 06:00 CDT each night).

EXPECTED CURTAILMENT:
  Estimated curtailment: 1,000 – 1,400 MW Panhandle Wind Farm Complex
  Duration: Nightly (00:00 – 06:00 CDT)
  Affected nodes: HB_WEST, LZ_WEST, HB_NORTH (partially)
  Outage ID: OUT-2024-0941

PRICE FORECAST:
  Real-time prices at HB_WEST and LZ_WEST may go negative during curtailment
  periods. ERCOT does NOT guarantee price floors; prices may reach the
  Real-Time Low Systemwide Offer Cap (-$250/MWh) during deep oversupply.

DA/RT DIVERGENCE WARNING:
  Day-Ahead prices were set before this oversupply forecast materialized.
  Significant DA/RT divergence is expected for West zone nodes. Load-serving
  entities and traders with long West zone positions should review exposures.

SETTLEMENT IMPLICATION:
  Negative RT prices will result in RT charges for generators (they pay
  rather than receive) and credits for loads. Net settlement for entities
  with short RT positions at HB_WEST will be advantageous.

ERCOT CONTACT: operations@ercot.com
""",
        "metadata": {"event_id": "B", "affects_nodes": ["HB_WEST", "LZ_WEST"], "type": "curtailment"}
    },
    {
        "title": "ERCOT Summer Reliability Assessment 2024 — Peak Demand and Reserve Margins",
        "doc_type": "protocol",
        "source": "ERCOT Planning",
        "effective_date": "2024-04-01",
        "content": """ERCOT SUMMER RELIABILITY ASSESSMENT 2024

EXECUTIVE SUMMARY
ERCOT's installed generating capacity is projected at 103,000 MW for summer 2024.
Peak demand forecast: 85,500 MW (extreme scenario: 88,600 MW).
Planning Reserve Margin: 17.4% — above NERC minimum but lower than 2023.

DEMAND FORECAST
  50th Percentile Peak: 83,200 MW (July 15-20, 2024 expected peak window)
  90th Percentile Peak: 85,500 MW
  Extreme Peak (1-in-10): 88,600 MW

  Load growth drivers:
  - EV charging infrastructure buildout: +800 MW from 2023
  - Data center expansion (Austin metro): +1,200 MW
  - Crypto mining facilities (West Texas): +600 MW

GENERATION CAPACITY
  Thermal (gas, coal, nuclear): 64,200 MW (firm capacity)
  Wind: 37,800 MW nameplate — contribution at peak: 11,000 MW (29% capacity factor)
  Solar: 16,500 MW nameplate — contribution at peak: 9,400 MW (57% capacity factor)

RISK FACTORS
  1. Extreme heat events (July 4th weekend, July 15-20 window) — high risk
  2. Wind generation below forecast during peak hours — moderate risk
  3. Unplanned thermal outage during peak — moderate risk
  4. Transmission constraints in Houston load pocket (SABINE_345, BRAZOS_HOUSTON)
     — historically binding in extreme summer heat

JULY 4TH ADVISORY
  July 4th holiday peak demand (14:00-20:00) expected to stress Travis County
  345kV infrastructure. ERCOT will pre-position reserves and may activate ERS.
  Constraint TRAVIS_345 has historically bound during July 4th peak events.
""",
        "metadata": {"category": "reliability", "event_id": "C"}
    },
    {
        "title": "ERCOT Congestion Revenue Rights Auction Results — Q3 2024",
        "doc_type": "settlement_guide",
        "source": "ERCOT CRR Desk",
        "effective_date": "2024-07-01",
        "content": """ERCOT CONGESTION REVENUE RIGHTS
Q3 2024 Auction Results Summary

AUCTION DATE: June 28, 2024
AUCTION PERIOD: July 1 – September 30, 2024

TOP PATHS BY CLEARING PRICE:

Path                     | MW    | Price ($/MW·month) | Direction
BUS_BRAZOS → HB_HOUSTON  | 4,200 | $287.40            | SINK
BUS_SABINE → HB_HOUSTON  | 2,800 | $198.65            | SINK
HB_WEST → HB_NORTH       |   800 | $32.10             | SINK (negative — oversupply risk)
HB_NORTH → LZ_HOUSTON    | 1,200 | $44.25             | SINK
LZ_WEST → HB_HOUSTON     | 3,100 | $156.80            | SINK

NOTES:
  - BUS_BRAZOS → HB_HOUSTON path highest-priced CRR this auction; reflects
    outage risk premium following MN-2024-0892 (Brazos Valley Unit 3 history).
  - West → North path (HB_WEST → HB_NORTH) cleared NEGATIVE reflecting
    market expectation of continued wind oversupply and negative RT price risk.
  - Total CRR auction revenue: $28.4M allocated to load-serving entities
    on pro-rata basis per ERCOT Nodal Protocols Section 7.4.

SHORTFALL RISK:
  CRR holders should note: ERCOT does NOT guarantee CRR payouts exceed
  auction payments. If congestion rent is insufficient, shortfalls are
  allocated to all CRR holders pro-rata (counter-flow weighted as of March 2024
  settlement rule change).
""",
        "metadata": {"category": "CRR", "quarter": "Q3_2024"}
    },
    {
        "title": "ERCOT Nodal Protocols Section 7.4.2 — CRR Auction Revenue Rights Settlement",
        "doc_type": "protocol",
        "source": "ERCOT Nodal Protocols v14.2",
        "effective_date": "2024-03-15",
        "content": """ERCOT NODAL PROTOCOLS
Section 7.4.2 — CRR Auction Revenue Rights (ARR) Settlement

7.4.2.1 OVERVIEW
CRR Auction Revenue Rights entitle holders to receive a share of congestion
rent collected in the Day-Ahead Market. CRRs are financial instruments —
they do not confer scheduling rights.

7.4.2.2 CONGESTION RENT CALCULATION
  Congestion_Rent = Σ(Quantity_MW × Congestion_Component_$/MWh × Hours)
  Where congestion component = SPP(sink) − SPP(source)

7.4.2.3 CRR SETTLEMENT
  CRR_Credit = CRR_Quantity_MW × (Sink_SPP_DA − Source_SPP_DA) × Hours
  Negative CRR_Credit (counter-flow periods) results in charges to CRR holder.

7.4.2.4 SHORTFALL ALLOCATION (Revised March 2024)
  When total CRR credits exceed collected congestion rent:
    Shortfall = Σ(CRR_Credits) − Congestion_Rent_Collected
  Prior to March 2024: Shortfall allocated pro-rata to all CRR holders.
  Effective March 15, 2024: Shortfall allocated counter-flow weighted.
    Counter_Flow_Weight_i = max(0, CRR_i × (Source_SPP − Sink_SPP)) / Σ(counter_flows)
  Rationale: Entities holding CRRs on paths where congestion is counter-flow
  bear more responsibility for shortfalls (PUCT Order 56789, Feb 2024).

7.4.2.5 NODE ALIAS RESOLUTION
  CRR settlement uses ERCOT canonical node IDs. Internal aliases must be
  mapped to canonical IDs prior to position submission. Alias mismatches
  result in settlement exceptions requiring manual resolution.
  Current known aliases: see ERCOT Node Alias Registry (quarterly published).

7.4.2.6 AUDIT RIGHTS
  QSEs may request CRR settlement detail audit within 45 days of monthly
  settlement. ERCOT will provide node-level disaggregated settlement data.
""",
        "metadata": {"section": "7.4.2", "category": "CRR_settlement"}
    },
]
