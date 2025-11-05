# src/aura_core/foreman.py
import sys
import ollama
import json
import importlib
import re # Import the regular expression module
import traceback # Import traceback for better error logging

# SYSTEM_PROMPT including all apprentices and detailed doc_creator
SYSTEM_PROMPT = """
You are a "Foreman" AI. Your job is to take a user's request and break it down into a
series of steps to be executed by "Apprentice" modules. Choose ONLY the most appropriate tool for each step.
You MUST use the full module path for the "apprentice" key (e.g., "aura_core.apprentices.slide_creator").
Generate detailed and structured content when creating documents or presentations.

You have the following tools (Apprentices) available:
1. "web_searcher":
    - Module: "aura_core.apprentices.web_searcher"
    - Input (JSON): {"query": "Search term"}

2. "web_researcher":
    - Module: "aura_core.apprentices.web_researcher"
    - Input (JSON): {"url": "https://..."}

3. "file_writer":
    - Module: "aura_core.apprentices.file_writer"
    - Input (JSON): {"filename": "file.txt", "content": "Text"}

4. "file_reader":
    - Module: "aura_core.apprentices.file_reader"
    - Input (JSON): {"filename": "file.txt"}

5. "pdf_reader":
    - Module: "aura_core.apprentices.pdf_reader"
    - Input (JSON): {"filename": "document.pdf"}

6. "file_manager":
    - Module: "aura_core.apprentices.file_manager"
    - Input (JSON): {"action": "copy", "source": "src", "destination": "dest"}

7. "archiver":
    - Module: "aura_core.apprentices.archiver"
    - Input (JSON): {"action": "create", "source_folder": "folder", "zip_filename": "archive.zip"}

8. "image_finder":
    - Module: "aura_core.apprentices.image_finder"
    - Input (JSON): {"query": "image description", "filename": "image.png"}

9. "doc_creator":
    - Module: "aura_core.apprentices.doc_creator"
    - Input (JSON): {
        "filename": "mydocument.docx",
        "header": "Optional header",
        "footer": "Optional footer",
        "content": [
            {"type": "heading1", "text": "My Title", "align": "center"},
            {"type": "paragraph", "text": "This is a test.", "formatting": {"bold": true, "color": "FF0000"}},
            {"type": "table", "data": [["H1","H2"],["R1C1","R1C2"]], "header": true}
        ]
       }

10. "slide_creator":
    - Module: "aura_core.apprentices.slide_creator"
    - Input (JSON): {
        "filename": "presentation.pptx",
        "template": "optional/template.pptx",
        "slides": [
            {
                "layout": "title_slide",
                "items": [
                    {"type": "title", "content": "Main Title"},
                    {"type": "subtitle", "content": "My Subtitle"}
                ],
                "notes": "Optional speaker notes."
            },
            {
                "layout": "title_content",
                "items": [
                    {"type": "title", "content": "Slide 2 Title"},
                    {"type": "body", "align": "left", "content": ["Bullet 1", "Bullet 2"]}
                ]
            },
            {
                 "layout": "content",
                 "items": [
                     {"type": "title", "content": "Rich Text"},
                     {"type": "body", "align": "center", "content": [
                         "Normal text, ",
                         {"text": "bold red", "bold": true, "color": "FF0000"},
                         ", then ",
                         {"text": "italic blue.", "italic": true, "color": "0000FF", "size": 18}
                     ]}
                 ]
            },
            {
                 "layout": "title_only",
                 "items": [
                     {"type": "title", "content": "Slide with Table"},
                     {"type": "table", "data": [["Col1", "Col2"], ["R1", 10]],
                      "left": 1.0, "top": 1.5, "width": 8.0, "header": true, "font_size": 10}
                 ]
            },
            {
                 "layout": "blank",
                 "items": [
                     {"type": "image", "path": "images/logo.png",
                      "left": 1.0, "top": 1.0, "width": 2.0}
                 ]
            },
            {
                 "layout": "comparison",
                 "items": [
                     {"type": "title", "content": "Comparison Slide"},
                     {"type": "left_body", "content": ["Point A1", "Point A2"]},
                     {"type": "right_body", "content": ["Point B1", "Point B2"]}
                 ]
            },
            {
                 "layout": "pic_caption",
                 "items": [
                     {"type": "title", "content": "Image in Placeholder"},
                     {"type": "image", "path": "images/chart.png"},
                     {"type": "caption", "content": "This is the caption."}
                 ]
            }
        ]
       }

11. "spreadsheet_creator":
    - Module: "aura_core.apprentices.spreadsheet_creator"
    - Input (JSON): {"filename": "sheet.xlsx", "data": [["H1", "H2"], ["R1C1", "R1C2"]]}

12. "summarizer":
    - Module: "aura_core.apprentices.summarizer"
    - Input (JSON): {"text": "Long text..."}

You must respond ONLY with a valid JSON array of "steps".
Each step uses ONE tool. Format: [{"apprentice": "module_name", "payload": {input_json}}]
You MUST use the full module path (e.g., "aura_core.apprentices.slide_creator").
DO NOT add extra characters, markdown, or commentary outside the JSON array.

**--- CRITICAL RULES FOR PASSING DATA ---**
**- Use "$PREV_OUTPUT" in payload value ONLY to use output from the PREVIOUS step.**
**- DO NOT invent tokens.**
"""

# --- START OF UPDATED FUNCTION ---
def call_llm(user_request):
    """Calls the local LLM to generate the JSON plan."""
    print(f"--- Foreman: Planning task for: '{user_request}' ---")
    raw_output = "" # Store the raw output for debugging
    json_plan_str = "" # Initialize
    try:
        response = ollama.chat(
            model='llama3', # Using llama3
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_request}
            ],
            options={'temperature': 0.0}
        )

        raw_output = response['message']['content'].strip()

        # --- START OF ENHANCED CLEANUP LOGIC ---
        start_index = raw_output.find('[')
        end_index = raw_output.rfind(']')

        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_plan_str = raw_output[start_index : end_index + 1]
            
            # --- Apply all cleanup rules sequentially ---
            json_plan_str = json_plan_str.replace("```json", "").replace("```", "")
            json_plan_str = json_plan_str.replace("**", "")
            json_plan_str = json_plan_str.replace(": True", ": true").replace(", True", ", true")
            json_plan_str = json_plan_str.replace(": False", ": false").replace(", False", ", false")
            json_plan_str = json_plan_str.replace(": None", ": null").replace(", None", ", null")
            json_plan_str = json_plan_str.replace(" null", " null") 
            json_plan_str = json_plan_str.replace("'", "\"")
            
            # --- FAULTY BRACE FIX REMOVED ---
            
            json_plan_str = json_plan_str.strip()

        else:
            # Fallback if no brackets found
            json_plan_str = raw_output
            json_plan_str = json_plan_str.replace(": True", ": true").replace(": False", ": false")
            json_plan_str = json_plan_str.replace(": None", ": null").replace(" null", " null")
            json_plan_str = json_plan_str.replace("'", "\"")
            print("--- Foreman: Warning - Could not find JSON brackets in LLM output. Using raw output. ---")
        # --- END OF ENHANCED CLEANUP LOGIC ---
        
        # --- Brace-Balancing Logic (from Solution B) ---
        # This will fix the missing brace at the end of the first step
        open_braces = json_plan_str.count('{')
        close_braces = json_plan_str.count('}')
        if open_braces > close_braces:
            json_plan_str += '}' * (open_braces - close_braces)
            print(f"--- Foreman Info: Added {open_braces - close_braces} missing closing braces. ---")
        # --- END FIX ---

        print(f"--- Foreman: Cleaned Plan String ---\n{json_plan_str}\n-------------------------------")
        parsed_json = json.loads(json_plan_str)

        if not isinstance(parsed_json, list): raise ValueError("Parsed JSON is not a list.")
        for item in parsed_json:
            if not isinstance(item, dict): raise ValueError("Item in parsed JSON list is not a dictionary.")
            if "apprentice" not in item or "payload" not in item: raise ValueError("Dictionary item missing 'apprentice' or 'payload'.")

        return parsed_json

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Could not parse valid JSON plan. Reason: {e}")
        print(f"Raw Output:\n{raw_output}"); print(f"Attempted to parse:\n{json_plan_str}"); return None
    except Exception as e:
        print(f"Error calling LLM or processing response: {e}\n{traceback.format_exc()}"); return None
# --- END OF UPDATED FUNCTION ---


# --- START OF UPDATED FUNCTION ---
def execute_step(step, previous_output):
    """Dynamically imports and executes an apprentice's 'run' function."""
    module_name = step.get("apprentice")
    payload = step.get("payload")

    # --- FIX: Prepend full path if short name is given ---
    if module_name and not module_name.startswith("aura_core.apprentices."):
        print(f"--- Foreman Info: Received short name '{module_name}'. Prepending full path. ---")
        module_name = f"aura_core.apprentices.{module_name}"
        step["apprentice"] = module_name
    # --- END FIX ---

    if not module_name or payload is None: print(f"Error: Invalid step. Missing 'apprentice' or 'payload'. Step: {step}"); return None, False

    def replace_prev_output(data_structure, output):
        if isinstance(data_structure, dict): return {k: replace_prev_output(v, output) for k, v in data_structure.items()}
        elif isinstance(data_structure, list): return [replace_prev_output(item, output) for item in data_structure]
        elif isinstance(data_structure, str) and data_structure == "$PREV_OUTPUT": return str(output) if output is not None else ""
        else: return data_structure

    payload = replace_prev_output(payload, previous_output)

    try:
        print(f"--- Apprentice: Executing '{module_name}' ---")
        
        apprentice_module = importlib.import_module(module_name)
        
        output = apprentice_module.run(payload)
        print(f"Apprentice Output: {output}")
        
        if isinstance(output, str) and output.strip().lower().startswith(("error:", "❌")): 
            return output, False
        elif isinstance(output, str) and output.strip().lower().startswith(("success:", "✅", "--- presentation saved")):
            return output, True
        return output, True
    except ImportError: error_msg = f"Error: Could not find module '{module_name}'."; print(error_msg); return error_msg, False
    except AttributeError as ae:
         error_msg = f"Critical error: Module '{module_name}' does not have a 'run' function. {ae}";
         print(traceback.format_exc()); return error_msg, False
    except Exception as e:
        error_msg = f"Critical error executing {module_name}: {e}";
        print(traceback.format_exc()); return error_msg, False
# --- END OF UPDATED FUNCTION ---


# --- START OF UPDATED FUNCTION ---
def handle_request(user_request):
    """Main function to handle a user's natural language request."""
    plan = call_llm(user_request)
    if not plan: print("--- Foreman: Halting task. No valid plan generated. ---"); return

    previous_step_output = None # This is the variable that gets updated
    all_steps_succeeded = True
    for i, step in enumerate(plan):
        print(f"\n--- Foreman: Starting Step {i+1}/{len(plan)} ---")
        # --- FIX: Use the correct variable name ---
        output, success = execute_step(step, previous_step_output)
        # --- END OF FIX ---
        
        if not success:
            print(f"--- Foreman: Halting task. Step {i+1} failed: {output} ---")
            all_steps_succeeded = False
            break
        previous_step_output = output # Update the variable for the next loop

    if all_steps_succeeded:
        print("\n--- Foreman: Task completed successfully. ---")
    else:
        print("\n--- Foreman: Task failed during execution. ---")
# --- END OF UPDATED FUNCTION ---