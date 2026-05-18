# Brightwheel "AI Front Desk" PoC

A high-velocity, high-fidelity proof of concept for Brightwheel's **AI Front Desk**. This system streamlines preschool operations by instantly answering parent inquiries using Retrieval-Augmented Generation (RAG) while providing operators with full visibility into system performance and escalations.

---

## 🚀 Hosted URLs

- **Parent Experience**: [https://democlient.draftedge.ai](https://democlient.draftedge.ai)
  - _Clean, mobile-first chat interface for parents._
- **Admin Control Center**: [https://demoadmin.draftedge.ai](https://demoadmin.draftedge.ai)
  - _Zendesk-style dashboard for preschool directors to manage escalations and review AI logs._
- **API Backend**: [https://service.draftedge.ai/api](https://service.draftedge.ai/api)
  - _Interactive documentation available at `/docs`._

---

## 🧠 High-Level Design Philosophy

The PoC is built on three core pillars:

1.  **User Empathy**: The parent interface is optimized for speed and clarity, recognizing the anxiety of busy parents. The AI ("Sunny") uses a polite, brief tone and strictly adheres to the center's handbook.
2.  **Trust & Grounding**: Using a strict RAG pipeline, the system only answers from the provided grounding matrix (currently the **Family Handbook PDF**). If the answer isn't found or is sensitive, it proactively escalates to a human director.
3.  **Actionable Insights**: The Admin UI is task-oriented, surfacing parent feedback (👍/👎) and AI escalations in real-time, allowing staff to close gaps in the knowledge base instantly.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.11 with **FastAPI**, containerized via Docker and running on **AWS ECS (Express Mode)**.
- **AI/LLM**: Google **Gemini 3.1 Flash Lite** and **Gemini Embedding 001** via the Vertex AI SDK.
- **Database**: **Supabase (PostgreSQL)** with the `pgvector` extension for semantic search and interaction logging.
- **Frontend**: Two **React (TypeScript)** Single Page Applications built with **Vite** and styled with Vanilla CSS for maximum performance.
- **Deployment**: **GitHub Actions** for frontend deployments to AWS S3/CloudFront and OIDC-based AWS authentication.

---

## 🧪 How to Test

### 1. The Parent Loop

- Open the [Parent Client](https://democlient.draftedge.ai).
- Use the **Quick-Action Chips** (e.g., "🛑 What is the fever policy?") or ask a question from the handbook.
- Click the **Thumbs Down (👎)** on a response to simulate a parent needing clarification.

### 2. The Admin Loop

- Open the [Admin Dashboard](https://demoadmin.draftedge.ai).
- Navigate to **Live Alerts** to see the downvoted message.
- Navigate to **Escalation Tickets** to see messages where the AI triggered a human handoff.
- Click **"Mark as Resolved"** in the detail drawer to clear the queue.

### 3. Knowledge Base
- In the Admin UI, view the **Knowledge Base** section to see the high-quality text chunks extracted via a **Gemini-powered Markdown conversion** of the **Family Handbook PDF**.
- Chunks are now categorized by their original handbook headers for better context.

---

## 💎 Phase 6: Polish Features

- **AI Ticket Deflection Rate**: Real-time tracking of inquiries successfully handled by AI without escalation.
- **Dynamic Trend Analysis**: Visualization of the most frequent inquiry categories and sample user questions.
- **Intelligent Reminder System**: The AI proactively provides reminders about upcoming school events (e.g., staff development days, birthdays) once every 3 days.
- **Holistic Grounding**: Enhanced RAG pipeline that provides more comprehensive, helpful responses by connecting related policy details.


### Prerequisites

- Python 3.11+
- Node.js 20+
- A `.env` file with the following:
  ```bash
  live_db_pass=YOUR_SUPABASE_PASSWORD
  GOOGLE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
  ```

### Run Backend

```bash
python3 backend/main.py
```

### Run Frontends

```bash
cd parent-client && npm run dev
cd admin-client && npm run dev
```
