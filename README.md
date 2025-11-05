AuraOS Core (Aura)
AuraOS Core is a local-first, AI-driven automation engine. It uses a "Foreman" (a ReAct agent powered by a local LLM like Ollama) to understand high-level natural language goals, create dynamic plans, and delegate tasks to a suite of specialized Python "Apprentices."

This is not just a simple script; it's an autonomous agent framework that can reason, observe, and execute complex, multi-step workflows like data analysis, report generation, and system management.

🚀 Key Features
Aura can read, write, and create complex professional documents and presentations. Its capabilities are broken down into specialized apprentices:

1. The "Big 3" Content Creators
📄 doc_creator: Creates advanced Word documents with headers, footers, native page numbers, tables of contents (TOCs), rich-text paragraphs (mixed formatting), styled tables, native lists, hyperlinks, and imported Markdown.

💹 spreadsheet_creator: Creates multi-sheet Excel reports with named styles (e.g., "header", "currency"), inline cell formatting, native formulas (like =SUM(...)), custom column widths, and frozen panes.

🖥️ slide_creator: Creates complex PowerPoint presentations using templates, supporting multiple slide layouts, rich text, speaker notes, and precise image/table placement.

2. Advanced Data Input
📊 chart_creator: Generates matplotlib charts (bar, line, pie) from data and saves them as images, ready for reports.

📑 spreadsheet_reader: Reads .xlsx files and returns data as a list of lists, a list of dictionaries (using the header row), or a full workbook dump.

📰 pdf_reader: Reads text from any PDF, automatically using OCR (Optical Character Recognition) for scanned, image-based documents.

🌐 web_researcher: A powerful scraper that uses playwright to render JavaScript-heavy sites and trafilatura to extract the main article content, stripping ads and boilerplate.

🔗 doc_reader: Extracts all text from .docx files, including paragraphs and tables.

3. Core System & File Tools
🧠 foreman (The Brain): A ReAct Agent that runs in a loop (Reason, Act, Observe) to build and execute plans dynamically, handling errors and using the output from one step to inform the next.

🗃️ file_manager: A robust tool to list, info, copy, move, rename, delete, mkdir, and perform batch operations with wildcards (glob_delete *.tmp).

🤐 archiver: Creates, lists, and extracts zip files, including password-protected archives and extracting specific files.

🖼️ image_finder: Searches the web for images with advanced filters for size, license, and type.

⚙️ How to Use
Aura is run from the command line. You provide a high-level goal, and the Foreman takes over.

(Make sure your ollama local LLM is running.)

Bash

# Activate your environment
.\venv\Scripts\Activate.ps1

# Run a prompt
python -m aura_core.cli "Your natural language prompt here"
✨ Example Prompts
Example 1: Simple Task (Web Research)
This will use the web_searcher to get a list of results, then pass the first URL ($STEP1_OUTPUT[0]["href"]) to the web_researcher, and finally save the article text.

Bash

python -m aura_core.cli "Search for 'latest AI developments', get the main article text from the first result, and save it to 'ai_news.txt'."
Example 2: Complex Multi-Step Report Generation
This prompt demonstrates the full power of the agent. It uses 4 different apprentices and passes the output from the first two steps into the final one.

Bash

python -m aura_core.cli "First, create a 'bar' chart titled 'Sales Data' and save it as 'sales_chart.png'. The data is [['Q1', 500], ['Q2', 750]]. Set the y-axis label to 'Revenue ($M)'. Second, find an image for 'company meeting' and save it as 'meeting.png'. Finally, create a document 'sales_report.docx' with header 'Q4 Sales Report' and footer with page number. Add a heading 1 'Quarterly Sales Figures', then insert the 'sales_chart.png' image, centered. After that, add a heading 2 'Next Steps', a bullet point 'Review Q4 performance', and insert the 'meeting.png' image with 10cm width."
🚧 Work in Progress & Future Vision
This project is in active development. The goal is to create a fully autonomous professional assistant.

Phase 1: Agent Brain (Complete) - The core foreman.py is now a ReAct agent.

Phase 2: Advanced Apprentices (Complete) - The core tools for data I/O and content creation are built.

Phase 3: Real-World Integrations (In Progress)

email_sender / email_reader (To send results and receive tasks via email).

calendar_reader (To read meeting agendas from Google/Outlook).

slack_poster (To post results directly to team channels).

Phase 4: Style & Persona (Future)

Copycat Feature: Analyze a user's existing .docx or .pptx files to learn their personal style and automatically apply it to new documents.

Phase 5: Interface (Future)

Voice/Video: Add a voice interface using a speech-to-text library.

Web UI: Build a simple streamlit or gradio web page to interact with the agent.
