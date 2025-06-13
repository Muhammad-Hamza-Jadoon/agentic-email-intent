import json
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field, conlist
from typing import List, Optional, Dict, Any
import time

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser

# For API calls
# from api_calls import OCRAPICall, RequestName

# model = ChatOpenAI(
#     base_url="https://api.together.xyz/v1",
#     # model="deepseek-ai/DeepSeek-R1",
#     model="Qwen/Qwen2.5-Coder-32B-Instruct",
#     # model="Qwen/Qwen2.5-Coder-32B",
#     api_key=os.getenv("TOGETHER_API_KEY")
# )
# model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)
model = ChatOpenAI(model="gpt-4", temperature=0)

def remove_none_values(obj):
    if isinstance(obj, dict):
        return {k: remove_none_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        # Remove None elements from the list, and recursively process other elements
        return [remove_none_values(elem) for elem in obj if elem is not None]
    else:
        return obj


# print(cleaned_data_deep)

class ImagePathsInput(BaseModel):
    """Input for tools that require a list of image paths."""
    image_paths: List[str] = Field(description="A list of file paths to the image attachments.")

class PlainTextInput(BaseModel):
    """Input for tools that expect a plain text string."""
    raw_text: str = Field(description="The plain text content from the email body.")

@tool(
    args_schema=ImagePathsInput,
    description="Processes images of documents. Use this when the email indicates BOL documents are attached."
    # return_direct=True
)
# def bol_api_tool(image_path: str) -> StructuredExtractionOutput:
def bol_api_tool(image_paths: List[str]) -> Dict:
    # print(f"DEBUG: Calling bol_api_tool for image: {image_paths}")
    all_results = {}
    for i, image_path in enumerate(image_paths):
        # Extract filename for key or use a simple index
        file_name = os.path.basename(image_path) # You'll need to import os
        # result = OCRAPICall(image_path, name=RequestName(11))
        result = remove_none_values(json.loads(result))

        # Mock data for demonstration
        result = {
            "bol_no": f"BOL-MOCK-{(i+1):03d}",
            "amount_due": 1000.00 + (i * 100),
            "currency": "USD",
            "due_date": "2024-07-01",
            "associated_shipment_id": "ABC-123"
        }

        all_results[file_name] = result
    return all_results

@tool(
    args_schema=ImagePathsInput,
    description="Processes images of documents. Use this when the email indicates shipping label documents are attached."
)
def shipping_label_api_tool(image_paths: List[str]) -> Dict: 
    # print(f"DEBUG: Calling shipping_api_tool for image: {image_paths}")
    all_results = {}
    for i, image_path in enumerate(image_paths):
        # Extract filename for key or use a simple index
        file_name = os.path.basename(image_path) # You'll need to import os
        # result = OCRAPICall(image_path, name=RequestName(10))
        # result = remove_none_values(json.loads(result))
        # Mock data for demonstration
        result = {
            "bol_no": f"BOL-MOCK-{(i+1):03d}",
            "amount_due": 1000.00 + (i * 100),
            "currency": "USD",
            "due_date": "2024-07-01",
            "associated_shipment_id": "ABC-123"
        }
        
        all_results[file_name] = result
    return all_results

@tool(
    args_schema=ImagePathsInput,
    description="Processes images of documents. Use this when the email indicates item label documents are attached."
)
def item_label_api_tool(image_paths: List[str]) -> Dict:
    # print(f"DEBUG: Calling item_label_api tool for image: {image_paths}")
    all_results = {}
    for i, image_path in enumerate(image_paths):
        # Extract filename for key or use a simple index
        file_name = os.path.basename(image_path)
        # result = OCRAPICall(image_path, name=RequestName(12))
        # result = remove_none_values(json.loads(result))
        # Mock data for demonstration
        result = {
            "bol_no": f"BOL-MOCK-{(i+1):03d}",
            "amount_due": 1000.00 + (i * 100),
            "currency": "USD",
            "due_date": "2024-07-01",
            "associated_shipment_id": "ABC-123"
        }
        all_results[file_name] = result
    return all_results

@tool(
    args_schema=ImagePathsInput,
    description="Processes images of documents. Use this when the email indicates invoice documents are attached."
)
def invoice_api_tool(image_paths: List[str]) -> Dict:
    # print(f"DEBUG: Calling invoice_api tool for image: {image_paths}")
    all_results = {}
    for i, image_path in enumerate(image_paths):
        # Extract filename for key or use a simple index
        file_name = os.path.basename(image_path) # You'll need to import os
        # result = OCRAPICall(image_path, name=RequestName(11))
        # result = remove_none_values(json.loads(result))
        # Mock data for demonstration
        result = {
            "inv_no": f"lalalalala-{(i+1):03d}",
            "amount_due": 1000.00 + (i * 100),
            "currency": "USD",
            "due_date": "2024-07-01",
            "associated_shipment_id": "ABC-123"
        }
        all_results[file_name] = result
    return all_results

@tool(
    args_schema=ImagePathsInput,
    description="Processes images of documents. Use this when the email indicates receipt documents are attached."
)
def receipt_api_tool(image_paths: List[str]) -> Dict:
    # print(f"DEBUG: Calling receipt_api_tool tool for image: {image_paths}")
    all_results = {}
    for i, image_path in enumerate(image_paths):
        # Extract filename for key or use a simple index
        file_name = os.path.basename(image_path)
        # result = OCRAPICall(image_path, name=RequestName(11))
        # result = remove_none_values(json.loads(result))
        # Mock data for demonstration
        result = {
            "bol_no": f"BOL-MOCK-{(i+1):03d}",
            "amount_due": 1000.00 + (i * 100),
            "currency": "USD",
            "due_date": "2024-07-01",
            "associated_shipment_id": "ABC-123"
        }
        
        all_results[file_name] = result
    return all_results
    
@tool(
    args_schema=PlainTextInput,
    description="""
        Extracts structured information from plain text content of logistics documents.
        Use this when the raw text pertaining to logistic information is provided directly in the email's text.
        The tool is designed to parse various logistics attributes, sender/recipient details, and tabular data.
    """
)
def extract_structured_text_tool(raw_text: str) -> Dict[str, Any]:
    """
    Extracts and structures logistics information from raw text, automatically determining
    the most appropriate organization of the data based on content.
    
    Args:
        raw_text: The raw logistics text to parse
    Returns:
        A structured dictionary containing the extracted information, organized logically
        based on the input content.
    """
    # print(f"DEBUG: Calling enhanced extract_structured_text_tool")
    
    prompt_template = """
    You are an advanced logistics document parser with the ability to intelligently structure
    information. Your task is to analyze the provided logistics text and extract only the information relevant to logistics,
    organizing it in the most logical structure possible.
    
    Key Principles:
    1. **Content-Driven Structure**: Let the content determine the structure rather than
       forcing it into a predefined schema.
    2. **Hierarchical Organization**: Group related information together naturally.
    3. **Preserve Relationships**: Maintain connections between data points (e.g., items
       with their quantities and weights).
    4. **Flexible Typing**: Use appropriate data types (lists for multiple items, dictionaries
       for structured data, strings for text, etc.).
    5. **Contextual Awareness**: Recognize and properly handle different document types
       (bills of lading, invoices, shipping manifests, etc.).
    6. **Completeness**: Extract all available information, including both obvious fields
       and implied relationships.
    
    Special Handling:
    - Dates: Normalize to ISO format (YYYY-MM-DD) when possible, but preserve original
      text if format is ambiguous.
    - Addresses: Structure when clear components exist, otherwise preserve as text.
    - Numbers/IDs: Extract all reference numbers, codes, and identifiers you find.
    - Tables/Lists: Structure tabular data appropriately based on column headers or patterns.
    
    Output Requirements:
    - Return ONLY valid JSON
    - Use proper nesting to reflect relationships in the data
    - Include all extracted information
    - Use null for missing/unknown values
    - Maintain original text values when structure is unclear
    
    Logistics Text to Analyze:
    {raw_text}
    """
    
    final_prompt = PromptTemplate(
        input_variables=["raw_text"], 
        template=prompt_template
    )
    
    chain = final_prompt | model | StrOutputParser()
    
    try:
        response = chain.invoke({"raw_text": raw_text})
        # print(response)
        return json.loads(response)
    except json.JSONDecodeError:
        print("ERROR: Failed to parse model output as JSON")
        return {"error": "Failed to parse structured data from input"}