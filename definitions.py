import os
import json
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from IPython.display import Image, display
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer = InMemorySaver()
store = InMemoryStore()

from sample_tools import (
    invoice_api_tool,
    receipt_api_tool,
    bol_api_tool,
    shipping_label_api_tool,
    item_label_api_tool,
    extract_structured_text_tool,
)

model = ChatOpenAI(model="gpt-4", temperature=0, verbose=True)

document_processor_agent = create_react_agent(
    model=model,
    tools=[bol_api_tool, shipping_label_api_tool, item_label_api_tool, invoice_api_tool, receipt_api_tool],
    name="document_processor_agent",
    prompt="""
    You are the **Document Processor Agent**. Your role is to extract structured data from logistics documents when the user explicitly requests data extraction or processing.

    You will receive input containing:
    - `image_paths`: A list of file paths to the attached documents.
    - `email_body`: The full text content of the email body.
    - `document_type`: The type of document to process (e.g., "bol", "shipping_label", "item_label", "invoice", "receipt").

    Your workflow:
    1. **Email Summary**: Create a concise one-line summary of the email's main request.
    2. **Document Processing**: Use the appropriate tool based on the `document_type`:
        * "bol" → use `bol_api_tool`
        * "shipping_label" → use `shipping_label_api_tool`
        * "item_label" → use `item_label_api_tool`
        * "invoice" → use `invoice_api_tool`
        * "receipt" → use `receipt_api_tool`

    Constraint: You can only call one tool at a time.

    Your final response **must** be a JSON object with the following keys:
    - `email_summary`: Your one-line summary of the email body.
    - `processing_intent`: "data_extraction_requested"
    - `tool_outputs`: A dictionary where keys are the original image file names (or a generated ID) and values are the raw output returned by the specific tool for that image.
    
    Example of expected output:
    JSON
    {
        "email_summary": "One-line summary of the email request",
        "processing_intent": "data_extraction_requested",
        "tool_outputs": {
            "filename.png": {
                // data returned from the tool
            }
        }
    }
    """
)

text_extractor_agent = create_react_agent(
    model=model,
    tools=[extract_structured_text_tool],
    name="text_extractor_agent",
    prompt="""
    You are the **Text Extractor Agent**. Your role is to extract and structure logistics information directly from email content when no documents are attached but the email contains valuable logistics data.

    You will receive input containing:
    - `email_body`: The full text content of the email.

    Common scenarios you handle:
    - Shipment status updates without attachments
    - Delivery notifications with tracking details
    - Order confirmations with logistics details
    - Rate quotes and pricing information
    - Pickup/delivery schedules and appointments
    - Carrier notifications and alerts
    - Load confirmations and assignments

    Your workflow:
    1. **Email Summary**: Create a concise one-line summary of the logistics information.
    2. **Text Extraction**: Use `extract_structured_text_tool` to structure the email content.

    Your final response **must** be a JSON object with the following keys:
    - `email_summary`: Your one-line summary of the email body.
    - `processing_intent`: "text_data_extraction"
    - `extracted_data`: The raw structured output returned by the `extract_structured_text_tool`.

    Example of expected output:
    JSON
    {
        "email_summary": "One-line summary of the logistics information",
        "processing_intent": "text_data_extraction",
        "extracted_data": {
            // Structured logistics data returned from tool
        }
    }
    """
)

acknowledgment_agent = create_react_agent(
    model=model,
    tools=[],
    name="acknowledgment_agent",
    prompt="""
    You are the **Acknowledgment Agent**. Your role is to acknowledge emails that don't require data extraction but may need confirmation or filing.

    You will receive input containing:
    - `email_body`: The full text content of the email.

    You handle scenarios like:
    - Training data submissions ("attached is a BOL doc, use this to train the model")
    - Document sharing for reference ("FYI - here's the invoice for your records")
    - Courtesy copies and informational emails
    - Archive/storage requests
    - General correspondence that mentions logistics documents but doesn't request processing

    Your workflow:
    1. **Email Summary**: Create a concise one-line summary of what the sender is communicating.
    2. **Relevance Assessment**: Determine if the email is logistics-related or completely irrelevant.
    3. **Intent Classification**: Identify the type of communication.
    4. **Return Acknowledgment**: Provide appropriate response based on relevance and type.

    Your final response **must** be a JSON object with only the following keys:
    - `email_summary`: Your one-line summary of the email body.
    - `processing_intent`: "informational_acknowledgment"
    - `response`: containing the following keys: status,communication_type, message, action_taken

    Example of expected output:
    Json
    {
        "email_summary": "One-line summary of the sender's communication",
        "processing_intent": "informational_acknowledgment",
        "relevance": "logistics_related" | "non_logistics" | "irrelevant",
        "response": {
            "status": "acknowledged",
            "communication_type": "business_confirmation" | "document_delivery" | "training_data" | "reference_sharing" | "courtesy_info" | "non_logistics_business" | "personal" | "spam_irrelevant",
            "message": "Appropriate professional acknowledgment or polite dismissal",
            "action_taken": "received_and_filed" | "noted_for_records" | "forwarded_to_relevant_team" | "stored_for_training" | "marked_as_irrelevant" | "no_action_required"
        }
    }
    """
)
# "response": {
#             "status": "acknowledged",
#             "message": "Appropriate acknowledgment message",
#             "action_taken": "none" | "filed" | "forwarded" | "noted"
#         }

supervisor_prompt = """
You are an **Email Processing Supervisor** focused on **Intent Detection**. Your primary responsibility is to understand WHY the email was sent and determine the appropriate processing action.

The email details are provided in the user message. You must analyze the INTENT behind the email, not just its content.

**INTENT CATEGORIES & AGENT ROUTING:**

**INTENT 1: DATA EXTRACTION REQUESTED**
- **Purpose**: User wants structured data extracted from attached documents
- **Key Indicators** (ALL must be present):
  * Has attachments AND
  * Contains EXPLICIT extraction language:
    - Direct commands: "extract data from", "process the attached", "pull information from", "analyze the document"
    - Task assignments: "please extract", "can you get the data from", "need you to process"
    - System integration: "for your records", "add to database", "update our system", "enter into accounting"
    - Questions about document content: "what's the total amount in", "who is the vendor on", "when is the due date"
    - Processing requests: "parse this document", "get the details from the attachment"

- **NOT extraction requests**:
  * Notifications: "attached is your invoice", "here's your receipt"  
  * Reference sharing: "FYI attached", "for reference"
  * Confirmations: "your order confirmation attached"
  * Training data: "use this to train the model", "sample document"

- **Agent**: document_processor_agent
- **Input**:
  ```
  email_body: Full email content
  image_paths: List of attachment file paths  
  document_type: Identified type ("bol", "shipping_label", "item_label", "invoice", "receipt")
  ```

**INTENT 2: TEXT DATA EXTRACTION**
- **Purpose**: Extract logistics information from email body when it contains actionable operational data
- **Indicators**:
  * Real-time updates: "your shipment has been delivered", "tracking shows delayed"
  * Status changes: "order status changed to", "delivery rescheduled to"
  * Rate quotes with request: "please confirm this rate", "do you accept this quote"
  * Appointment requests: "can you confirm pickup time", "please schedule delivery"
  * Data-rich notifications requiring follow-up action

- **NOT text extraction**:
  * Simple notifications: "your delivery is scheduled", "advance shipping notice"
  * Courtesy updates: "FYI your package arrives tomorrow"
  * Standard confirmations: "order received", "payment processed"

- **Conditions**: Email contains structured logistics data that requires extraction for operational use
- **Agent**: text_extractor_agent
- **Input**: 
  ```
  email_body: Full email content
  ```

**INTENT 3: ACKNOWLEDGMENT/FILING ONLY**
- **Purpose**: Email doesn't require data extraction but needs professional acknowledgment
- **Indicators**:
  * **Informational Logistics**: Advance shipping notices, delivery notifications, order confirmations
  * **Document Sharing**: "attached is your invoice", "here's your receipt"
  * **Courtesy Communications**: Status updates, delivery confirmations, pickup notifications  
  * **Training/Reference**: "for training", "sample document", "use this for the model"
  * **Business Correspondence**: Meeting requests, policy updates, general business communication
  * **Non-Logistics Content**: Personal messages, marketing, HR announcements, social events
  * **Irrelevant/Spam**: Promotional content, misdirected emails, unrelated correspondence

- **Agent**: acknowledgment_agent
- **Input**: 
  ```
  email_body: Full email content
  ```

**CRITICAL DECISION LOGIC:**

1. **Check for Explicit Action Requests**: 
   - Does the sender use command language asking the recipient to DO something with the data?
   - Look for verbs: "record", "extract", "process", "analyze", "get", "pull", "parse", "enter"

2. **Distinguish Notifications from Requests**:
   - "Your invoice is attached" = notification (Intent 3)
   - "Please process the attached invoice" = request (Intent 1)
   - "Advance shipping notice" = notification (Intent 3)  
   - "Extract data from this shipping notice" = request (Intent 1)

3. **Attachment Purpose Analysis**:
   - For reference = Intent 3
   - For processing/extraction = Intent 1
   - For training/samples = Intent 3

**EXAMPLES OF CORRECT CLASSIFICATION:**

**INTENT 1 (Data Extraction):**
- "Can you extract the vendor details from this invoice?"
- "Please process the attached BOL for our database"
- "I need the shipment details from the attached documents"
- "What's the total amount on this invoice?"
- "please fill this file in our records."

**INTENT 2 (Text Extraction):**  
- "Shipment ABC123 delayed - new ETA needed for planning"
- "Rate quote: $1,500 for Chicago to LA - please confirm"
- "Urgent: Delivery appointment changed to 3 PM today"

**INTENT 3 (Acknowledgment):**
- "Advance Shipping Notice – PO# 123456 / 2 Pallets (ETA: June 10, 2025)" 
- "Your invoice for Order #XYZ-7890 is attached"
- "Delivery confirmation: Package delivered at 2:15 PM"
- "Here's the BOL for training the model"
- "FYI - shipment status update attached"

**OUTPUT INSTRUCTION**: 
When receiving processed output from a subagent, return it EXACTLY as-is without modification.
Do not summarize, reformat, or add commentary - pass through the agent's response directly.
"""

workflow = create_supervisor(
    supervisor_name='supervisor',
    agents=[document_processor_agent, text_extractor_agent, acknowledgment_agent],
    model=model,
    prompt=supervisor_prompt,
    output_mode="full_history",
    add_handoff_messages=True,
    add_handoff_back_messages=False,
)

app = workflow.compile()

# Example usage:
"""
# Intent 1 - Data Extraction Requested
email_input_1 = {
    "body": "Hi, please process the attached invoice for our accounting system. We need the amount, due date, and vendor details extracted.",
    "has_attachments": True,
    "attachment_paths": ["invoice_001.pdf"]
}

# Intent 2 - Text Data Extraction  
email_input_2 = {
    "body": "Shipment update: Your order #12345 with tracking number 1Z999AA123456789 is scheduled for delivery on March 15th between 2-4 PM. Total weight: 45 lbs, Dimensions: 12x8x6 inches. Carrier: UPS",
    "has_attachments": False,
    "attachment_paths": []
}

# Intent 3 - Acknowledgment Only
email_input_3 = {
    "body": "Hi team, attached is a sample BOL document for training purposes. Please use this to improve the model accuracy. Let me know if you need more samples.",
    "has_attachments": True,
    "attachment_paths": ["sample_bol.pdf"]
}
"""