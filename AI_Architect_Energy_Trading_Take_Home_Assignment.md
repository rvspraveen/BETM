# Take-Home Assignment: AI-Powered Power Market Intelligence & Risk Copilot


## 1. Objective

Design and implement a **production-minded AI platform** that helps internal energy trading, analytics, and risk teams investigate complex market questions using a combination of:

- structured power market data,
- internal position and exposure data,
- unstructured ISO / market documents,
- and explainable AI workflows.

The solution should demonstrate how AI can support **market intelligence, historical event investigation, and exposure analysis** while maintaining strong controls around:

- traceability,
- grounded responses,
- deterministic analytics,
- uncertainty handling,
- architecture quality,
- and enterprise readiness.

> **Important:** This assignment is for **historical or synthetic/redacted data only**. The goal is to assess architecture and engineering depth, not to build a live trading or autonomous decisioning system.

---

## 2. Required Technology Stack

Please use the following technologies for your implementation.

### Frontend
- **React**
- **TypeScript**
- Recommended: Vite 
- UI should be lightweight and functional; heavy design/polish is not required

### Backend
- **Python**
- **FastAPI** for API services
- **Pydantic** for request/response models and validation

### AI Orchestration
- **LangGraph** for workflow orchestration
- Use graph-based routing for multi-step flows such as:
  - document-only Q&A
  - structured-data-only analysis
  - hybrid investigation
  - review / escalation path

### RAG / Vector Store
- **PostgreSQL + pgvector** for embeddings storage and semantic retrieval
- Support metadata-aware retrieval
- Hybrid retrieval (vector + keyword) is a plus if implemented cleanly

### Data / Storage
- **PostgreSQL** as the primary application database
- Use pgvector extension for RAG storage
- Structured market data may be queried from PostgreSQL tables or loaded through deterministic processing layers

### Suggested Supporting Libraries
Candidates may use reasonable supporting libraries, for example:
- `langchain` where helpful, but the orchestration layer should be centered on **LangGraph**
- SQLAlchemy / SQLModel
- pandas / polars for deterministic analytics
- Alembic for migrations
- pytest for testing
- Docker / Docker Compose for local environment setup

### Containerization
- Provide **Docker Compose** for local startup if possible
- At minimum, the app should run locally with clear setup instructions

---

## 3. Business Context

Power trading organizations operate across highly complex datasets and workflows, including:

- day-ahead and real-time locational marginal prices,
- nodal and hub pricing,
- congestion and basis behavior,
- load and generation trends,
- outages and transmission constraints,
- trade positions and exposure,
- settlement and PnL analysis,
- ISO rules, notices, and operational manuals.

Analysts and risk teams often need to answer questions that span both **structured market data** and **unstructured market documentation**. In practice, they need systems that can:

- analyze historical price and congestion behavior,
- explain unusual market outcomes,
- link market behavior to operational events,
- compare exposure against changing market conditions,
- retrieve supporting evidence from ISO manuals, outage notices, and internal runbooks,
- and surface uncertainty or conflicting evidence rather than fabricate conclusions.

This assignment is designed to simulate that environment.

---

## 4. Assignment Summary

Build an **AI-Powered Power Market Intelligence & Risk Copilot** that supports the following capabilities:

1. **Document-based Q&A**  
   Answer questions from ISO manuals, market notices, outage documents, and internal runbooks with citations.

2. **Structured data analysis**  
   Answer questions using historical market prices, load, outages, positions, settlements, and risk data.

3. **Hybrid investigation workflows**  
   Support questions that require combining retrieved document evidence with structured analytics.

4. **Explainable market-event analysis**  
   Explain unusual historical price, congestion, basis, or settlement events using structured and unstructured evidence.

5. **Exposure and risk interpretation**  
   Summarize how historical market behavior would have affected a given portfolio, book, asset, node, or position.

6. **Governed recommendation support**  
   Provide analyst-facing next steps or follow-up suggestions while clearly separating facts from interpretation.

7. **Traceability, observability, and review**  
   Surface evidence, confidence, workflow path, and escalation when evidence is weak or conflicting.

---

## 5. Core Use Case

Your system should function as an internal **analyst and risk copilot** for historical power market intelligence.

It should be able to address questions such as:

### Market Behavior
- What likely drove the congestion spike on a given date/hour?
- Why did real-time prices diverge from day-ahead prices at a node or hub?
- Which outages or constraints coincided with a price event?

### Exposure & Risk
- Which positions were most exposed to congestion in a selected period?
- What historical events most resemble the selected basis pattern?
- Which assets or books showed the largest volatility-adjusted exposure?

### Rules & Market Context
- Which ISO rules or market notices are relevant to this event?
- Did any recent manual changes affect settlement or auction logic?
- Which documents describe congestion management or uplift treatment?

### Hybrid Analysis
- Compare historical price spikes with known outage notices and explain likely drivers.
- Summarize portfolio exposure for a trading book and cite relevant market conditions and operational notices.
- Explain a settlement variance using both structured settlement data and supporting documents.

---

## 6. Input Data

You may assume the following data types are provided in either historical or synthetic/redacted form.

### 6.1 Structured Datasets
Examples may include:

- `da_lmp.csv` � day-ahead locational marginal prices
- `rt_lmp.csv` � real-time locational marginal prices
- `constraints.csv` � transmission constraints and shadow prices
- `outages.csv` � planned / unplanned outages
- `load_forecast.csv` � system load forecast and actuals
- `generation_mix.csv` � fuel mix / unit availability
- `ftr_positions.csv` � FTR / CRR positions
- `physical_positions.csv` � physical generation / load exposure
- `trade_pnl.csv` � historical trade PnL
- `settlements.csv` � settlement outcomes and adjustments
- `asset_metadata.csv` � nodes, hubs, plants, books, traders, regions

### 6.2 Unstructured Documents
Examples may include:

- ISO market manuals
- market notices / operational advisories
- outage bulletins
- auction rules
- settlement guides
- internal runbooks
- postmortems
- methodology / model notes

### 6.3 Data Complexity
Your design should anticipate realistic data conditions, including:

- inconsistent naming across sources
- missing values
- conflicting document versions
- duplicate notices
- noisy documents
- late-arriving data
- differing market calendars and time granularities

---

## 7. Functional Requirements

### 7.1 Document Ingestion and Indexing

Your solution must:

- ingest the provided documents,
- extract and normalize text,
- split content into retrievable chunks,
- generate embeddings,
- store embeddings in **pgvector**,
- preserve metadata for traceability.

At a minimum, document metadata should include:

- document name
- document type
- section / heading
- page number if available
- publish/effective date if available
- version if available
- market / ISO tag if applicable

### 7.2 Retrieval-Augmented Question Answering

Your assistant must answer document-based questions using retrieved evidence only.

Responses must:

- be grounded in retrieved content,
- include source citations,
- avoid unsupported claims,
- explicitly state when the answer cannot be determined from the available material.

### 7.3 Structured Data Analysis

Your solution must support analytical questions over structured datasets.

Examples include:

- DA/RT spreads
- nodal vs hub price comparisons
- congestion drivers
- exposure by asset / book / node
- historical event analysis
- settlement anomalies
- relationships between outages, constraints, and price behavior

You may implement this using:

- PostgreSQL queries,
- SQL generation with validation,
- deterministic dataframe computation,
- or another reliable analytical approach.

> **Important:** calculations should be deterministic wherever possible. The LLM should not be relied on for numeric computation when reproducible programmatic logic is appropriate.

### 7.4 Hybrid Investigation Workflow

Your system must support **multi-step investigative workflows** that combine:

- retrieval from unstructured sources,
- structured market analytics,
- reasoning and summarization,
- evidence-backed explanation.

A strong solution should route user queries through distinct workflow paths such as:

- document-only
- structured-data-only
- hybrid investigation
- exposure analysis
- unsupported / out-of-scope

### 7.5 Event Explanation / Root-Cause Analysis

Given a selected historical market event (for example, a price spike, basis blowout, congestion event, or settlement anomaly), the system should:

- identify relevant time windows,
- pull related structured evidence,
- retrieve related documents,
- summarize plausible contributing factors,
- distinguish facts from hypotheses,
- cite all relevant evidence,
- indicate uncertainty where necessary.

### 7.6 Risk and Exposure Interpretation

Your solution should support internal risk interpretation scenarios such as:

- identifying positions most sensitive to congestion or spread changes,
- summarizing exposure concentration by node, hub, asset, trader, or book,
- describing historical market conditions associated with elevated exposure,
- comparing recent portfolio behavior with past events.

This should remain **analytical and interpretive**, not prescriptive trading advice.

### 7.7 Recommendation Support

Your assistant may generate **analyst workflow recommendations**, such as:

- suggested follow-up analyses,
- additional datasets to review,
- documentation to validate,
- possible causes that require human confirmation.

Recommendations must be:

- evidence-backed,
- clearly framed as recommendations,
- not autonomous decisions,
- not live trading instructions.

### 7.8 Conflict, Ambiguity, and Review Handling

Your solution must detect and respond appropriately when:

- source documents conflict,
- structured data and documentation disagree,
- evidence is incomplete,
- naming mismatches prevent reliable joins,
- the requested conclusion is too speculative.

In such situations, the system should:

- explain what is missing or conflicting,
- provide the best available evidence,
- avoid overconfident conclusions,
- and optionally return a `needs_review` or similar status.

### 7.9 Traceability and Explainability

Each response should include enough detail to explain how it was produced.

At a minimum, include:

- sources used,
- workflow / route selected,
- analytical entities used (book, asset, node, date range, etc.),
- confidence or review status,
- high-level reasoning trace.

A strong implementation may also include:

- tools invoked,
- model version,
- prompt version,
- retrieval scores,
- latency and cost metadata.

---

## 8. LangGraph Workflow Expectations

Use **LangGraph** to model the orchestration layer.

A recommended workflow is:

1. **Intent classification node**
   - identify whether the request is document-only, data-only, hybrid, exposure-oriented, or out-of-scope

2. **Entity extraction / normalization node**
   - extract market identifiers such as node, hub, book, date range, ISO, asset, or event window

3. **Route selection node**
   - select the appropriate path based on intent and available inputs

4. **Retrieval / analytics nodes**
   - document retrieval from pgvector
   - structured analytics via SQL / deterministic computations
   - hybrid aggregation when both are needed

5. **Answer synthesis node**
   - produce a grounded response with citations and clear separation between facts, interpretation, and recommendations

6. **Review / escalation node**
   - return `needs_review` when evidence is conflicting, missing, or confidence is low

The candidate is expected to use LangGraph meaningfully rather than as a thin wrapper around a single LLM call.

---

## 9. Frontend Expectations (React + TypeScript)

Build a lightweight frontend in **React + TypeScript** that allows a reviewer to:

- submit questions / investigation requests,
- select example scenarios,
- view responses,
- inspect citations and evidence,
- view workflow status or route selected,
- see `needs_review` or low-confidence outcomes.

### Suggested UI Sections
- Query input panel
- Filters / scenario selectors (date range, node, hub, book, ISO, event type)
- Response panel
- Citations / evidence drawer
- Workflow trace summary
- Optional review status banner

The frontend does **not** need to be visually elaborate. Prioritize usability and clarity.

---

## 10. Backend Expectations (FastAPI)

Implement a **FastAPI** backend with clear request/response models.

### Suggested API Endpoints

#### Health
- `GET /health`

#### Ingestion
- `POST /api/v1/ingest/documents`
- `POST /api/v1/ingest/datasets`

#### Query / Investigation
- `POST /api/v1/investigate`

#### Metadata / Reference
- `GET /api/v1/documents`
- `GET /api/v1/datasets`
- `GET /api/v1/examples`

#### Optional Review Endpoints
- `GET /api/v1/reviews`
- `POST /api/v1/reviews/{review_id}/resolve`

### Example Request
```json
{
  "question": "Explain the likely drivers of the congestion event at Node A during HE18-HE21 on 2025-08-14.",
  "filters": {
    "iso": "ERCOT",
    "date": "2025-08-14",
    "node": "Node A"
  }
}
```

### Example Response
```json
{
  "status": "ok",
  "route": "hybrid_investigation",
  "answer": "The congestion event appears associated with Constraint X, coincident outage Y, and elevated real-time divergence from day-ahead prices.",
  "facts": [
    "Constraint X shadow price increased materially during HE18-HE21.",
    "Outage Y was active during the same interval.",
    "RT prices exceeded DA prices at Node A by a significant margin."
  ],
  "recommendations": [
    "Review the associated outage bulletin and settlement notes before finalizing the event summary."
  ],
  "sources": [
    {
      "type": "document",
      "name": "market_notice_2025_08_14.pdf",
      "page": 2
    },
    {
      "type": "dataset",
      "name": "constraints.csv",
      "record_hint": "constraint_id=1234"
    }
  ],
  "needs_review": false
}
```

---

## 11. Data Model and Storage Expectations

Use **PostgreSQL** as the core storage layer.

### Expected Logical Tables (Illustrative)
- `documents`
- `document_chunks`
- `document_embeddings` (pgvector-backed)
- `market_prices_da`
- `market_prices_rt`
- `constraints`
- `outages`
- `positions`
- `settlements`
- `investigation_logs`
- `review_queue` (optional)

### Expected RAG Metadata Fields
For chunk-level retrieval, store metadata such as:
- `document_id`
- `chunk_id`
- `document_name`
- `document_type`
- `section`
- `page_number`
- `effective_date`
- `version`
- `market`
- `source_uri` (optional)

---

## 12. Deliverables

Please submit the following:

### 12.1 Source Code
Complete source code with instructions to run locally

### 12.2 README
Include:
- project overview,
- assumptions,
- local setup instructions,
- how to run ingestion and query workflows,
- limitations,
- future improvements.

### 12.3 Architecture Document
Provide a concise but formal architecture summary covering:
- logical components,
- data flow,
- orchestration design,
- AI model usage,
- retrieval strategy,
- structured analytics design,
- governance and observability approach,
- scaling considerations.

A diagram is strongly encouraged.

### 12.4 API / Usage Documentation
Document major interfaces such as:
- ingestion endpoints,
- investigation/query endpoints,
- health/status endpoints,
- review/status outputs.

### 12.5 Evaluation Strategy
Describe how you evaluated:
- retrieval quality,
- answer groundedness,
- analytical correctness,
- route selection quality,
- uncertainty handling,
- system performance.

### 12.6 Benchmark Queries
Provide a sample benchmark set including:
- document-only questions,
- structured-data questions,
- hybrid investigative questions,
- conflicting-evidence cases,
- unsupported/out-of-scope prompts.

---

## 13. Testing Expectations

Please include at least a basic testing strategy.

### Minimum Expectations
- unit tests for core service logic
- tests for at least one API endpoint
- tests for deterministic analytical functions
- tests for workflow routing where practical

### Suggested Tools
- `pytest`
- `httpx` / FastAPI test client
- factory or fixture-based test data

A strong submission will validate:
- correct route selection,
- correct fallback behavior,
- correct structured calculations,
- and citation presence in grounded answers.

---

## 14. Non-Functional Expectations

Please design with the following principles in mind.

### Reliability
- graceful handling of bad inputs and partial data
- safe fallbacks when evidence is insufficient
- robust processing for noisy sources

### Maintainability
- modular design
- clean abstractions
- manageable configuration
- understandable code structure

### Performance
- reasonable latency for a small historical dataset
- sensible handling of repeated queries
- clear explanation of scale-up approach

### Security and Governance
- no hardcoded secrets
- clear treatment of sensitive position or PnL data
- design awareness for row-level or book-level access control
- explainability and auditability

### Enterprise Readiness
- architecture should reflect production thinking
- candidate should demonstrate how the design could evolve for broader deployment

---

## 15. Required Engineering Practices

Please follow these engineering practices:

- use environment variables for secrets and configuration
- provide a `.env.example`
- maintain clear separation between frontend and backend
- use typed request/response contracts
- keep business logic out of controllers where possible
- structure code for extensibility and testability
- do not hardcode market assumptions unless clearly documented

### Recommended Repository Structure
```text
project-root/
  frontend/                 # React + TypeScript app
  backend/                  # FastAPI app
    app/
      api/
      core/
      services/
      graphs/               # LangGraph workflows
      models/
      schemas/
      repositories/
      tests/
  data/
  docs/
  docker-compose.yml
  README.md
```

---

## 16. Nice-to-Have Enhancements

The following are optional but will be considered positively if implemented thoughtfully:

- hybrid retrieval (vector + keyword)
- reranking
- entity resolution for node/hub/asset aliases
- time-series aware reasoning workflows
- event window detection
- batch + interactive architecture separation
- prompt or workflow versioning
- containerization
- CI/CD notes
- unit/integration tests
- cost tracking
- response caching
- human review queue
- document version conflict handling
- access-control design for books/traders/portfolios
- prompt injection and source poisoning mitigation

---

## 17. Time Expectation

Please aim to spend approximately **8 to 12 hours** on this assignment.

We do not expect every feature to be fully implemented. A strong submission may implement the highest-value workflows and clearly describe how the remaining architecture would be completed.

Thoughtful scope management is part of the evaluation.

---

## 18. Evaluation Criteria

Your submission will be evaluated across the following dimensions:

### 18.1 Domain-Aware Problem Structuring
- quality of decomposition across market data, documents, AI workflows, and analytics
- evidence of understanding complex operational domains

### 18.2 Architecture Quality
- service/component boundaries
- orchestration design
- extensibility and production awareness

### 18.3 AI / Retrieval Design
- grounding discipline
- citation quality
- retrieval relevance
- handling of conflicting documentation

### 18.4 Analytical Reasoning Quality
- correctness of time-series and exposure analysis
- disciplined separation of deterministic computation and LLM generation
- entity/time-window handling

### 18.5 Engineering Quality
- modularity
- maintainability
- clarity
- testability

### 18.6 Governance and Explainability
- traceability
- review routing
- uncertainty management
- audit-friendly outputs

### 18.7 Observability and Production Thinking
- logging
- metrics
- failure handling
- cost/performance awareness
- versioning approach

### 18.8 Communication
- README quality
- architecture explanation
- tradeoff clarity
- completeness of submission

---

## 19. Example Benchmark Prompts

### Document-Oriented
- Which ISO documents describe congestion management and settlement adjustments?
- What documentation applies to a transmission outage affecting nodal price formation?
- What changed between two versions of the settlement rules?

### Structured Analytics
- Which nodes exhibited the highest DA/RT divergence during the selected week?
- Which books had the largest congestion-related exposure during the selected month?
- What were the top price spikes by node and what constraints were active?

### Hybrid Investigative
- Explain the likely drivers of the congestion event at Node A during HE18-HE21 on the selected date.
- Summarize the settlement variance for Book Z using both structured settlement data and supporting documentation.
- Which historical events look most similar to the recent basis widening, and what operational notices were associated with them?

### Uncertainty / Review
- If outage data and market notices disagree on timing, how should the system respond?
- What if the same node appears under multiple aliases across datasets?
- What if the documentation suggests one interpretation but structured data does not support it?

---

## 20. Submission Notes

Please submit:

- source code repository or archive
- README
- architecture notes / diagram
- instructions to run the application
- any supporting documentation

If applicable, include:
- sample environment file (without secrets)
- Docker instructions
- test instructions

---

## 21. Closing Note

There are many valid ways to approach this assignment. We are less interested in a polished demo and more interested in whether you can think and build like an **AI Architect**:

- designing systems, not just prompts,
- balancing AI capability with engineering controls,
- handling ambiguity responsibly,
- and building something that could realistically evolve into an enterprise platform.

Please make reasonable assumptions where necessary, document those assumptions clearly, and focus on producing a solution that is thoughtful, explainable, and well-architected.
