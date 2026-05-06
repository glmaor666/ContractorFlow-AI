# Feature Specification: Sprint 1 - Autonomous Ingestion & Normalization Engine

## 1. Sprint Goal
Build a robust, LLM-powered data ingestion pipeline in Python that transforms chaotic, multi-lingual, and structurally inconsistent contractor Excel reports into a clean, standardized JSON schema ready for database insertion.

## 2. Technical Data Flow
The ingestion script (`ingestion.py`) will execute the following sequence:

* **Ingestion:** Load the raw `.xlsx` file using pandas.
* **Structural Pre-processing:** Apply forward-filling (`ffill`) to resolve merged cells (specifically for contractor names) and drop completely empty rows.
* **Header Extraction:** Extract the raw column headers and the first two rows of data to provide context to the LLM.
* **LLM Schema Mapping:** Construct an API call to OpenAI (GPT-4o) containing the raw headers, requesting a JSON response that maps the raw headers to our strict internal database schema.
* **Column Renaming:** Parse the LLM's JSON response and programmatically rename the pandas DataFrame columns.
* **Data Type Normalization:** Apply Python functions to clean quantitative columns (e.g., stripping "%" signs, converting string fractions to floats).
* **Output Generation:** Export the cleaned DataFrame as a list of dictionaries (JSON format) containing both the structured metrics and the preserved unstructured text.

## 3. Known Edge Cases to Handle
The script must be defensive against the following data anomalies commonly found in operational field reports:

* **Mixed-Language Headers:** Column names may be in English ("Progress"), Hebrew ("התקדמות"), or a mix ("Start Dt התחלה"). The LLM prompt must explicitly handle cross-lingual mapping.
* **Merged/Missing Categorical Data:** Excel files often merge the "Contractor Name" cell across multiple rows. The script must use Pandas `ffill()` to ensure every sub-task row retains its parent contractor name.
* **Inconsistent Quantitative Formats:** The "Progress" or "Completion" columns may contain "70%", "0.7", "70", or textual edge cases like "Almost done". The script must normalize numbers to a standard float (e.g., 0.7). Unresolvable textual anomalies in quantitative fields should be moved to the notes column and replaced with null/NaN.
* **Unstructured Chaos:** The "Notes" or "Comments" column will contain paragraph-long text with line breaks, dates, and irregular characters. This text must be preserved intact as a string, stripping only unreadable encoding artifacts.

## 4. User Stories & Acceptance Criteria

### Task 1: Data Pre-processing & Forward-Filling
* **Story:** As the pipeline, I need to ingest raw Excel files and resolve structural gaps so that the LLM receives contiguous, readable data.
* **Acceptance:** The script successfully loads an `.xlsx` file; missing/merged cells in the identifying columns are forward-filled; empty rows are dropped.

### Task 2: LLM-Powered Schema Matching (Multi-Lingual)
* **Story:** As the data ingestion engine, I need to map inconsistent, mixed-language column headers to a strict internal schema so data can be queried predictably.
* **Acceptance:** The LLM returns a valid JSON mapping regardless of the input language; Pandas columns are successfully renamed using this mapping.

### Task 3: Data Type Normalization & Anomaly Handling
* **Story:** As a Data Analyst, I need quantitative fields to be strictly numerical so that I can perform aggregations without type errors.
* **Acceptance:** Progress values are converted to standardized floats; strings in numerical columns are flagged and moved to notes.

### Task 4: Unstructured Context Extraction
* **Story:** As the RAG engine, I need raw comments preserved and cleaned so they can be embedded into the Vector DB later.
* **Acceptance:** The final JSON output retains all paragraph text in the notes field without truncation.

## 5. Expected Output Format
The final output of the script must be a JSON array of objects strictly adhering to this schema:
```json
[
  {
    "contractor_name": "string (e.g., 'Alpha Builders')",
    "task_description": "string",
    "start_date": "YYYY-MM-DD",
    "progress_percentage": "float (e.g., 0.75)",
    "status": "string (e.g., 'In Progress', 'Delayed', 'Completed')",
    "notes": "string (preserved raw text for Vector DB)"
  }
]
