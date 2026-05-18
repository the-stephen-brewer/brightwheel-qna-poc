import os
import asyncio
from google import genai
from google.genai import types
from pypdf import PdfReader
import google.auth
from dotenv import load_dotenv

load_dotenv()

async def convert_to_md():
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, project = google.auth.default(scopes=scopes)
    
    client = genai.Client(
        vertexai=True,
        project="betterai",
        location="us-central1",
        credentials=credentials
    )

    PDF_FILE = "2019-division-of-child-and-family-development-family-handbook-final.pdf"
    reader = PdfReader(PDF_FILE)
    total_pages = len(reader.pages)
    
    print(f"📄 Total pages to convert: {total_pages}")
    
    batch_size = 5
    all_markdown = ""

    for i in range(0, total_pages, batch_size):
        batch_end = min(i + batch_size, total_pages)
        print(f"⏳ Converting pages {i+1} to {batch_end}...")
        
        batch_text = ""
        for page_num in range(i, batch_end):
            batch_text += f"--- PAGE {page_num + 1} ---\n" + reader.pages[page_num].extract_text() + "\n"

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            #model="gemini-2.0-flash-001",
            contents=[
                "Convert the following batch of extracted PDF pages into a well-structured Markdown document. "
                "Use # for main sections, ## for sub-sections. Clean up spacing and OCR errors. "
                "Ensure ALL policies are preserved. Do not summarize. "
                "Output ONLY the markdown content, no extra talk.",
                batch_text
            ]
        )
        
        batch_md = response.text.replace("```markdown", "").replace("```", "").strip()
        all_markdown += batch_md + "\n\n"

    with open("backend/handbook.md", "w") as f:
        f.write(all_markdown.strip())
    
    print(f"✅ Full conversion complete. Saved to backend/handbook.md")

if __name__ == "__main__":
    asyncio.run(convert_to_md())
