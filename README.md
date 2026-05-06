# ContractorFlow-AI
An AI-native data platform that automates contractor performance analysis, transforming messy multi-lingual reports into actionable management insights using RAG and Multi-Agent orchestration.
Bridging the gap between messy operational data and strategic decision-making.

📌 The ProblemIn large-scale industrial projects, managing multiple contractors results in fragmented, multi-lingual (Hebrew/English), and unstructured Excel reports. 
Project managers often face:  
1. Data Silos: Manual consolidation of inconsistent data formats.
2. Insight Gaps: Difficulty in identifying real-time bottlenecks within hundreds of rows of comments.
3. Delayed Decisions: Lack of automated forecasting and KPI tracking.

💡 The SolutionContractorFlow AI is an end-to-end data product designed to automate the lifecycle of contractor oversight:
1. Smart Ingestion: Uses LLMs for schema-matching to handle inconsistent Excel headers and forward-fill structural gaps.
2. Contextual Intelligence (RAG): A retrieval-augmented generation pipeline that allows managers to "chat" with their contractor data to find root causes of delays.
3. Agentic Workflow: Multi-agent orchestration (LangGraph) that separates data cleaning, SQL analysis, and trend visualization.
4. Dynamic Visualization: A Vanilla JS frontend that generates custom dashboards on-demand via natural language prompts.

🛠️ The Tech Stack
1. Backend: Python, FastAPI, LangGraph, Pandas.
2. AI/LLM: OpenAI GPT-4o, RAG (Pinecone/ChromaDB).
3. Frontend: JavaScript, HTML5, CSS3, Chart.js.
4. Infrastructure: Docker, AWS EC2.
5. Methodology: Agile/Scrum, User-Centric Design (PRD & Mockups).

📊 Business Impact
1. Operational Efficiency: Reduces report generation time from hours to seconds.
2. Risk Mitigation: Automatically flags SLA breaches and identifies critical path bottlenecks.
3. Data Accuracy: Normalizes mixed-language data and inconsistent quantitative metrics (e.g., "70%" vs "0.7").

   
