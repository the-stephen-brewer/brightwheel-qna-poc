# GEMINI.md: Brightwheel "AI Front Desk" PoC Blueprint

## 1. Project Vision & Goals

The goal is to build a high-velocity, high-fidelity proof of concept (PoC) for Brightwheel's "AI Front Desk". This system aims to solve the administrator "front desk bottleneck" by instantly answering common parent inquiries while providing preschool operators with full visibility into system confidence and parent escalations.

Our keys to success are:

- Delightful experience for parents that quickly addresses their needs
- Ticket deflection by reducing the number of inquires handled by admin
- High trust by parents and admin that this system will respond with accurate information or esecalate rather than halucinate

### Key Objectives

- **Demonstrate User Empathy:** Build experiences tailored to anxious parents (clear, tone-sensitive, brief text) and busy operators (actionable, stress-free insights).
- **Speed to Market:** Focus entirely on a functional prototype within a strict 3-hour implementation window.
- **Architectural Taste:** Deploy a lightweight, containerized Python service on AWS App Runner to completely bypass serverless timeout issues, coupled with Supabase for real-time storage and vector lookups.

---

## 2. Technical Stack & Key Libraries

We are standardizing on a robust, modern Python ecosystem optimized for a long-running web server. By leveraging AWS App Runner, we bypass serverless execution constraints, allowing us to utilize LangChain to maximize development velocity.

fastapi & uvicorn: High-performance, asynchronous web framework to handle live API routing and maintain a persistent, stateful application.

langchain & langchain-community: The core orchestration layer used to streamline prompt templates, clean up context injection, and manage RAG chain states.

langchain-google-genai: Provides access to Google Gemini chat and embedding architectures via the Gemini Developer API key.

supabase: Used alongside LangChain's native vector store integrations to query pgvector datasets and asynchronously pipe real-time system logs.

pydantic: Enforces strict runtime data validation for incoming parent chat payloads and operator feedback events.

---

## 3. High-Level Architecture

The system uses a persistent container environment on AWS App Runner, enabling the use of native FastAPI background tasks for asynchronous database logging without risking execution freezes.

              ┌──────────────────────────────┐
              │   Parent & Operator Web UIs   │
              └──────────────┬───────────────┘
                             │ HTTP REST
                             ▼
                ┌──────────────────────────┐
                │      AWS App Runner      │
                │   (FastAPI Container)    │
                └───────┬──────────┬───────┘
                        │          │
     Gemini Embeddings  │          │  Postgres RPC / Log Stream
     & Chat Completions │          │  (Port 6543 Transaction Pool)
                        ▼          ▼
                  ┌──────────┐┌──────────┐
                  │  Gemini  ││ Supabase │
                  │   API    ││ (pgvector)│
                  └──────────┘└──────────┘

---

## 4. Execution Milestones & Target Roadmap

### Milestone 1: Vector Database & Seed Initialization

- Provision a Supabase instance and execute the `vector` extension schema.
- Run a local bootstrap script to create embeddings for core preschool policies (Tuition, Fever Outbreaks, Holidays, and Lunch protocols) and populate the database.
- Drive this script using files stored in an AWS S3 bucket so it can be easily updated in future for content modifications

### Milestone 2: Asynchronous Container Backend

- Implement the core FastAPI endpoints.
- Build a deterministic grounding pipeline using a Postgres cosine similarity match function.
- **Key Implementation Pattern:** Use FastAPI `BackgroundTasks` to offload database logging away from the user response thread:

```python
import os
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client, Client

app = FastAPI(title="Brightwheel AI Front Desk - App Runner Container")

# Initialize Gemini & Supabase Integrations
supabase_client: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

vector_store = SupabaseVectorStore(
    client=supabase_client,
    embedding=embeddings,
    table_name="front_desk_knowledge",
    query_name="match_front_desk"
)

# Leverage Gemini 2.5 Flash for hyper-fast, low-latency parent interactions
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def handle_parent_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    # 1. Pull relevant documents using LangChain's VectorStore abstraction
    docs = vector_store.similarity_search(req.message, k=2)
    context = "\n".join([doc.page_content for doc in docs])

    # 2. Invoke Gemini using a structured LangChain invocation pattern
    system_prompt = f"You are an assistant for a preschool. Answer based ONLY on this context:\n{context}"
    ai_msg = llm.invoke([
        ("system", system_prompt),
        ("human", req.message)
    ])
    ai_answer = ai_msg.content

    # 3. Assess if a human operator intervention or escalation is required
    needs_review = "center director" in ai_answer or not docs

    # 4. Safely pipe telemetry to Supabase using a background thread
    background_tasks.add_task(
        log_interaction_to_supabase,
        req.message, ai_answer, needs_review
    )

    return {"answer": ai_answer, "flagged": needs_review}
```

### Milestone 3: Parent client experience

Parent Experience: A clean, mobile-responsive chat widget equipped with quick-action chips for testing edge cases (e.g., "What happens if my child has a 101°F fever?"). It must feature simple binary feedback buttons (👍/👎).

##### 1. UI Foundation & Canvas Taste (The "Gemini Mobile" Approach)

The parent experience must feel like a native web app built for mobile viewing, prioritizing speed, clean micro-interactions, and a warm, calming visual aesthetic suited for anxious parents.

###### Key Visual & UX Components

- **Fixed Mobile Layout:** Constrain the maximum viewport width to `480px` centered on the screen with a clean mobile container shadow if viewed on a desktop browser.
- **The "Clean Canvas" Landing State:**
  - Header: Displays the preschool's identity ("Sunshine Early Learning Center") and a status indicator green pulse dot ("● Front Desk Active").
  - Empty Chat Slate: Instead of a blank wall, show a welcoming greeting block: _"Hi there! Ask me anything about Sunshine's schedules, tuition, meals, or health policies."_
- **Dynamic Quick-Action Chips:** Position 3 or 4 actionable text chips directly above the message input area when the chat history is short or empty. Tapping a chip immediately sends that query into the chat engine:
  - 🛑 _What is the fever policy?_
  - 🦃 _Are we open on Veterans Day?_
  - 🍏 _I forgot to pack lunch today._
- **Streaming / Visual Loading State:** Do not freeze the interface. While the API request is in flight, show a smooth, animated wave bar skeleton loader similar to Gemini's pulse animation.

---

##### 2. Conversation History & LangChain Memory Schema

Even though we are bypassing login authentication and targeting a single-parent experience for this proof of concept, maintaining short-term conversation history is essential for multi-turn questions (e.g., _Parent: "What is infant tuition?" -> AI: "$375/week." -> Parent: "Does that include formula?"_).

###### Context Pipeline Implementation

Because this app runs in a persistent container on AWS App Runner, we can manage short-term session storage directly in memory, or seamlessly attach a LangChain history buffer to the backend endpoint.

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Simple in-memory session cache to maintain state for the POC user session
SESSION_HISTORY_STORE = []

class ParentChatRequest(BaseModel):
    message: str

# Use Gemini 2.5 Flash for rapid response delivery
chat_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

@app.post("/api/parent/chat")
async def handle_parent_chat(req: ParentChatRequest, background_tasks: BackgroundTasks):
    # 1. Pull relevant grounding documentation from Supabase using the raw message
    context_docs = vector_store.similarity_search(req.message, k=2)
    grounding_matrix = "\n".join([d.page_content for d in context_docs])

    # 2. Build a history-aware Chat Prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"""You are 'Sunny', the AI Front Desk assistant for Sunshine Early Learning.
        Your job is to give busy parents fast, deeply polite, and highly accurate answers.

        CRITICAL INSTRUCTIONS:
        - Only answer using the Grounding Knowledge Matrix provided below.
        - If the answer is not present, or if it involves sensitive personal info, say exactly: 'I want to make sure you get the exact right answer for that. Let me loop in our center director right now to assist you directly.'
        - Keep answers strictly under 3 sentences. Bullet points are fine if they simplify reading on a phone.

        Grounding Knowledge Matrix:
        {grounding_matrix}"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_input}")
    ])

    # 3. Process the chain including the running session log
    chain = prompt_template | chat_llm
    response = chain.invoke({
        "history": SESSION_HISTORY_STORE,
        "user_input": req.message
    })

    ai_answer = response.content

    # 4. Append turns to memory to maintain chat context
    SESSION_HISTORY_STORE.append(HumanMessage(content=req.message))
    SESSION_HISTORY_STORE.append(AIMessage(content=ai_answer))

    # Limit memory depth to the last 6 turns to keep the prompt payload light
    if len(SESSION_HISTORY_STORE) > 6:
        SESSION_HISTORY_STORE.pop(0)
        SESSION_HISTORY_STORE.pop(0)

    # 5. Background log dispatch to Supabase for the Operator to inspect
    needs_review = "center director" in ai_answer or not context_docs
    background_tasks.add_task(log_interaction_to_supabase, req.message, ai_answer, needs_review)

    return {
        "answer": ai_answer,
        "history_depth": len(SESSION_HISTORY_STORE) // 2
    }

@app.post("/api/parent/clear")
async def clear_session():
    """Endpoint for a 'New Chat' button in the UI"""
    SESSION_HISTORY_STORE.clear()
    return {"status": "history cleared"}
```

##### 3. Inline Feedback Triage

To give the administrator dashboard actionable data, the parent chat interface must facilitate instant feedback collection:

Micro-Actions: Right below every text bubble sent by the AI, render small, subtle thumbs-up and thumbs-down icons (👍 / 👎).

Instant Submission: Clicking a feedback icon fires an immediate post to /api/feedback with the interaction identifier.

UI State Modification: If the parent clicks 👎, change the icon state to a filled icon and show a small, gentle system alert beneath it: "Got it. We've flagged this response for review by our front desk staff to improve our records." This instantly updates the Operator's dashboard in real time, demonstrating your integrated, end-to-end user loop.

This is a react-app SPA that is based in the 'parent-client' folder. Github actions will compile and deploy this spa to 'democlient.draftedge.ai' for hosting.

### Milestone 4: Administrator client experience

Operator Experience: A control panel displaying an active log feed. It must feature a "Needs Review / Parent Escalations" toggle to surface cases where the AI triggered an escalation or received a thumbs-down.

#### Local Agent Blueprint: Operator Control Center & Upsell Architecture

##### 1. UI Foundation & Layout Taste (The "Zendesk" Approach)

The administrator dashboard must feel clean, task-oriented, and structured around clearing open queues rather than looking like a passive data viewer.

###### Key Visual Components

- **The "Tri-Pane" Workflow Layout:**
  - Left pane: Collapsible vertical navigation bar (Knowledge Base, Trends, Active Alerts, Escalation Tickets).
  - Center pane: A scrollable, high-density table featuring contextual rows.
  - Right pane: A dynamic slide-out drawer panel. Clicking any row in the center table opens its full configuration, metadata, or AI action steps on the right without forcing a full page reload or breaking context.
- **Status Badge Standards:** Use strict color coding for triage velocity:
  - `Urgent / Escalated` -> Soft Crimson background, crisp red text.
  - `Pending Review` -> Soft Amber background, brown text.
  - `Resolved / Synergized` -> Soft Mint background, dark green text.

---

##### 2. Supabase Query Architecture & Component Mapping

The local agent must construct four distinct views driven directly by real-time Postgres queries.

###### Component A: Knowledge Base Explorer

- **Database Target:** `public.front_desk_knowledge`
- **Features:** A searchable directory displaying `content` and `category`. Include a button next to each entry to allow the operator to "Regenerate Embedding Vector" via LangChain if they manually edit the text.

###### Component B: Top Question Trends

- **Database Target:** Group-by analysis on `public.front_desk_logs`
- **Features:** A simple, high-impact metric card row displaying:
  1. Total Inquiries (Past 24 hours)
  2. Resolution Rate % (Logs where `needs_review = false`)
  3. A breakdown list tracking the most frequent search categories (e.g., #1: Illness, #2: Tuition Changes).

###### Component C: Live Alerts (System Friction Points)

- **Database Target:** `select * from public.front_desk_logs where feedback = 'thumbs_down'`
- **Features:** Displays parent interactions where the AI successfully answered from a technical standpoint, but the parent actively downvoted the response. This signals a gap in tone, empathy, or nuance that needs human review.

###### Component D: Escalation Tickets (Hard System Gaps)

- **Database Target:** `select * from public.front_desk_logs where needs_review = true`
- **Features:** The primary queue for cases where the Gemini model triggered a direct handoff (_"Let me loop in our center director..."_) because it hit a policy gap or a sensitive topic.

---

##### 3. "Admin Pro" AI Upsell Logic & Generation Pipeline

To create a compelling, forward-looking presentation feature, build a simulated premium layer called **Admin Pro**. This feature proactively surfaces missing documents using the underlying AI stack.

This is a react-app SPA that is based in the 'admin-client' folder. Github actions will compile and deploy this spa to 'demoadmin.draftedge.ai' for hosting.

### Milestone 5: Dockerization & AWS App Runner Deployment

Write a clean, multi-stage Dockerfile pinning Python 3.11-slim.

Push the built image to Amazon ECR.

Spin up the service via AWS App Runner connected directly to ECR

## 5. Critical Verification Checks for local AI Agents

Strict Boundary Grounding: Instruct the model's system prompt to explicitly default to human escalation ("Let me loop in our center director right now...") if the vector match metadata returns weak similarity scores.

Port Mapping Continuity: Ensure the container exposes port 8080 internally and that the Dockerfile CMD explicitly binds Uvicorn to 0.0.0.0:8080 to align perfectly with AWS App Runner’s default routing behavior.

Supabase Connection Pooling: Verify all database environment variables connect through Supabase's transaction pooler port (6543) to safely handle stateless container restarts.

## Data Design

Leverage sqlalchemy for managing the database
Get the DB_PASSWORD from ENV variable: "live_db_pass"

Key tables:

- transactions -- Store every question, response, feedback, duration, was it esecalated, is it alerted
- docs -- what documents have we processed and stored in our search database and relevant metadata
- users -- which school do they belong to, staff or parent, who are there kids, etc
