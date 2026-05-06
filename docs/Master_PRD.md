# Master Product Requirements Document (PRD): ContractorFlow AI

## 1. Executive Summary
ContractorFlow AI is an enterprise-grade, AI-native data product designed to transform chaotic, multi-lingual contractor reporting into structured, actionable intelligence. By bridging the gap between unstructured field data and predictive analytics, the system provides project managers and operational leaders with real-time visibility into contractor performance, schedule adherence, and SLA compliance. The product leverages a multi-agent LLM architecture and Retrieval-Augmented Generation (RAG) to enable dynamic, conversational "Text-to-BI" dashboarding, replacing static reporting with on-demand operational insights.

## 2. Target Audience (User Personas)
* **Operational Project Managers & Plant Engineers:** Require immediate visibility into task completion, delay bottlenecks, and contractor efficiency to maintain project critical paths.
* **QA & Compliance Managers:** Need automated extraction of qualitative field notes to ensure safety, quality, and SLA standards are met without spending hours reading unstructured logs.
* **Data/Operations Analysts:** Require clean, standardized data pipelines to feed downstream BI tools and forecasting models.

## 3. The Business Problem
In large-scale industrial and technological projects, contractor reporting is fundamentally broken.
* **Data Silos & Structural Chaos:** Subcontractors submit progress reports in varying formats (mixed Hebrew/English, inconsistent column headers, merged cells, and varied data types).
* **Manual QA Overhead:** Operations teams spend excessive administrative hours cleaning data and standardizing metrics, leading to delayed decision-making.
* **Lost Qualitative Intelligence:** Critical context regarding delays and bottlenecks is often buried in unstructured "Notes" columns, rendering it invisible to standard SQL queries or traditional BI tools.
* **Reactive vs. Proactive SLA Management:** Without real-time, normalized data, SLA breaches are identified retroactively rather than prevented proactively.

## 4. Product Vision & Core Epics (Technical Architecture)
To solve these bottlenecks, ContractorFlow AI is divided into four distinct technical Epics, moving from data ingestion to cloud deployment.

### Epic 1: Autonomous Ingestion & Normalization Engine
* **Objective:** Eliminate manual data cleaning by utilizing LLMs to dynamically map unpredictable incoming data to a strict internal schema.
* **Tech Stack:** Python, Pandas, OpenAI/Anthropic API, PostgreSQL.
* **Core Capabilities:**
  * Ingest raw .xlsx files via API.
  * Execute dynamic schema matching using LLM prompts (translating Hebrew/English headers to standardized database columns).
  * Normalize data types (e.g., converting "70%" or "Almost Done" into standardized floats).
  * Forward-fill missing relational data (e.g., matching merged contractor name cells to corresponding rows).

### Epic 2: Multi-Agent NLP & Contextual RAG Architecture
* **Objective:** Decouple structured numerical data from unstructured qualitative notes, enabling hybrid search and summarization.
* **Tech Stack:** LangGraph (Multi-Agent Routing), Pinecone/ChromaDB (Vector Database), PostgreSQL.
* **Core Capabilities:**
  * Implement an Intent Router Agent to classify user queries (Analytical vs. Contextual).
  * Store standardized numerical data in PostgreSQL for exact quantitative aggregation.
  * Embed and store unstructured contractor comments/delay notes in a Vector DB to enable Retrieval-Augmented Generation (RAG).

### Epic 3: Dynamic Visualization & "Text-to-BI" UI
* **Objective:** Provide a conversational interface where non-technical management can type natural language queries and receive dynamic, AI-generated charts and insights.
* **Tech Stack:** FastAPI (Backend), Vanilla JavaScript / HTML / CSS (Frontend), Chart.js.
* **Core Capabilities:**
  * Expose asynchronous REST endpoints via FastAPI.
  * Translate user text queries into actionable JSON configurations for the frontend charting library.
  * Render dynamic visualizations (bar charts, line graphs) directly within the chat interface.

### Epic 4: Cloud-Native Deployment & Infrastructure
* **Objective:** Package the application as an independent, scalable web service.
* **Tech Stack:** Docker, AWS EC2, Uvicorn.
* **Core Capabilities:**
  * Containerize the backend API, the Python ingestion engine, and the frontend assets.
  * Deploy the containers to an AWS EC2 instance for continuous availability.

## 5. Success Metrics (KPIs)
To measure the ROI and technical success of the product, we will track:
* **Data Processing Latency:** Time taken to ingest, map, and standardize a 1,000-row messy Excel file (Target: < 30 seconds).
* **Schema Mapping Accuracy:** Percentage of dynamically mapped columns that require zero manual correction (Target: > 95%).
* **Time-to-Insight (MTTI):** Reduction in management time required to generate a specific contractor delay report (Target: Reduction from hours to < 5 seconds via Text-to-BI).
* **Query Routing Accuracy:** Precision of the LangGraph agent in correctly routing queries to the SQL DB vs. the Vector DB.

## 6. Out of Scope (V1.0)
* **Optical Character Recognition (OCR):** Ingesting scanned, non-digital PDFs is excluded; V1.0 relies strictly on digital .xlsx and .csv uploads.
* **Complex Role-Based Access Control (RBAC):** V1.0 will not feature multi-tenant authentication or tiered user permissions.
* **Automated Live System Integrations:** Polling data directly from external ERPs is excluded; V1.0 utilizes manual file upload triggers.
