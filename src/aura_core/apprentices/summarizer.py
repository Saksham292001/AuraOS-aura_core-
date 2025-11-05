# src/aura_core/apprentices/summarizer.py
import ollama
import traceback
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Prompts for different tasks ---
PROMPTS = {
    "summary": """
You are a world-class summarization expert. The user will provide text.
Respond ONLY with a concise, 3-paragraph summary that captures the main points.

TEXT:
{text}
""",
    "summary_reduce": """
You are a world-class summarization expert. The user will provide a set of summaries
from different parts of a long document. Combine them into a single, final,
cohesive 3-paragraph summary.
Respond ONLY with the final summary.

SUMMARIES:
{text}
""",
    "bullets": """
You are a world-class summarization expert. The user will provide text.
Respond ONLY with a list of 5 key bullet points.

TEXT:
{text}
""",
    "qa": """
You are a world-class Q&A expert. You will be given a text and a question.
Analyze the text and answer the question based *only* on the information in the text.
If the answer is not in the text, say "Answer not found in text."
Respond ONLY with the answer.

TEXT:
{text}

QUESTION:
{query}
"""
}

# This is the size of the chunks we'll feed to the LLM
CHUNK_SIZE = 10000 # Max characters per chunk
CHUNK_OVERLAP = 500  # How much chunks overlap to maintain context

def run(payload):
    """
    Summarizes, extracts, or answers questions about a large block of text
    using a Map-Reduce strategy.
    """
    text_to_process = payload.get("text")
    task = payload.get("task", "summary").lower() # "summary", "bullets", "qa"
    query = payload.get("query")
    model = payload.get("model", "phi3:mini") # Default to fast model

    if not text_to_process:
        return "Error: Missing 'text' in payload for summarizer."
    if task == "qa" and not query:
        return "Error: Missing 'query' for 'qa' task."
    
    # 1. Select the correct prompt
    if task == "qa":
        prompt_template = PROMPTS["qa"]
    elif task == "bullets":
        prompt_template = PROMPTS["bullets"]
    else:
        prompt_template = PROMPTS["summary"]

    try:
        # 2. Check if text is short enough to process in one go
        if len(text_to_process) <= CHUNK_SIZE:
            print(f"--- Summarizer Info: Text is short. Processing in one step. ---")
            prompt = prompt_template.format(text=text_to_process, query=query)
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']

        # 3. --- Map-Reduce Strategy for Long Text ---
        print(f"--- Summarizer Info: Text is long ({len(text_to_process)} chars). Starting Map-Reduce. ---")
        
        # --- MAP Step: Split and Summarize Chunks ---
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(text_to_process)
        chunk_summaries = []

        print(f"--- Summarizer Info: Text split into {len(chunks)} chunks. ---")

        for i, chunk in enumerate(chunks):
            print(f"--- Summarizer: Processing chunk {i+1}/{len(chunks)}... ---")
            prompt = prompt_template.format(text=chunk, query=query)
            
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            chunk_summaries.append(response['message']['content'])

        # --- REDUCE Step: Combine and Finalize ---
        if task == "qa" or task == "bullets":
            # For Q&A or bullets, just join all results
            print("--- Summarizer Info: Joining all chunk results. ---")
            return "\n\n---\n\n".join(chunk_summaries)
        else:
            # For "summary", we summarize the summaries
            print("--- Summarizer Info: Performing Reduce step (summarizing summaries)... ---")
            combined_summaries = "\n\n".join(chunk_summaries)
            reduce_prompt = PROMPTS["summary_reduce"].format(text=combined_summaries)
            
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': reduce_prompt}]
            )
            return response['message']['content']

    except Exception as e:
        traceback.print_exc()
        return f"Error while summarizing: {e}"