# Agentic Email Processing System

This repository contains an intelligent, modular email processing system built using **LangChain**, **LangGraph**, and **OpenAI's GPT-4**. It automates triage and routing of incoming emails—especially those related to logistics—by detecting intent and dispatching them to specialized agents for appropriate action.

---

## Features

- **Intelligent Email Triage**  
  Automatically determines the primary intent of an email, such as:
  - Data extraction from attached documents
  - Structuring logistics-related text in email body
  - Informational or confirmation messages

- **Specialized AI Agents**
  - **Document Processor Agent**: Extracts structured data from attached logistics documents (e.g., BOLs, shipping labels, invoices, receipts, item labels).
  - **Text Extractor Agent**: Extracts structured logistics data from the email body when no attachments are relevant.
  - **Acknowledgment Agent**: Handles informational emails, confirmations, or training submissions that require no extraction.

- **Supervisor-led Workflow**  
  A central supervisor agent orchestrates the workflow by analyzing the email and assigning it to the correct specialist agent.

- **Modular and Extensible Architecture**  
  Powered by LangGraph, enabling easy addition of new agents and tools.

---

## How It Works

The system uses a **Supervisor-Agent Pattern**:

1. **Email Ingestion**  
   The system receives an email and any attached files (images, PDFs, etc.).

2. **Intent Detection by Supervisor Agent**  
   The supervisor analyzes:
   - Email subject
   - Body text
   - Presence or absence of attachments

   It determines whether to:
   - Extract data from documents
   - Parse logistics data from the text
   - Acknowledge the email

3. **Agent Routing**  
   Depending on intent, the supervisor dispatches the request to one of the following:
   - `document_processor_agent`
   - `text_extractor_agent`
   - `acknowledgment_agent`

4. **Agent Task Execution**  
   The selected agent performs the appropriate task using tools like:
   - `bol_api_tool`
   - `shipping_label_api_tool`
   - `extract_structured_text_tool`

5. **Output**  
   The system returns structured output including:
   - `extracted_data`: structured logistics info
   - `summary`: natural language summary of the email
   - `processing_intent`: intent classified by the supervisor

---

## Setup and Installation

### Prerequisites

- Python 3.9+
- An [OpenAI API Key](https://platform.openai.com/)
- Access to an OCR API (via `api_calls.py`)

---

### Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate

