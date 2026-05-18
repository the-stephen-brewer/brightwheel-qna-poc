# Project Backlog: Brightwheel "AI Front Desk" PoC

## Phase 1: Infrastructure & Data Foundation (Milestone 1)
- [x] **Environment Setup**: Initialize Python virtual environment and `requirements.txt` with FastAPI, LangChain, Supabase, and SQLAlchemy.
- [x] **Supabase Schema**: Define and execute SQL schema for `front_desk_knowledge` (vector store) and `front_desk_logs`.
- [x] **Database Models**: Implement SQLAlchemy models for `transactions`, `docs`, and `users`.
- [x] **Seed Script**: Create a bootstrap script to embed and upload core preschool policies (Tuition, Fever, Holidays, Lunch) to Supabase.

## Phase 2: Asynchronous Backend Development (Milestone 2)
- [x] **FastAPI Scaffold**: Set up the base FastAPI server with port 8080 configuration.
- [x] **LangChain Integration**: Configure Gemini 2.5 Flash and Google Embeddings.
- [x] **Parent Chat Logic**: Implement `/api/parent/chat` with in-memory session history and context grounding.
- [x] **Feedback API**: Implement `/api/feedback` to capture parent thumbs-up/down.
- [x] **Background Telemetry**: Implement FastAPI `BackgroundTasks` to log all interactions to Supabase asynchronously.
- [ ] **Testing**: Write unit tests for RAG retrieval and response generation.

## Phase 3: Parent Client Experience (Milestone 3)
- [x] **React Scaffold**: Initialize `parent-client` using Vite/React.
- [x] **Mobile-First UI**: Implement a 480px constrained, mobile-responsive chat container.
- [x] **Quick-Action Chips**: Add interactive chips for common queries (Fever, Holidays, etc.).
- [x] **Chat Interface**: Build the message thread with AI pulse loading states and feedback icons.
- [x] **API Integration**: Connect the UI to the backend endpoints.

## Phase 4: Admin Control Center (Milestone 4)
- [x] **React Scaffold**: Initialize `admin-client` using Vite/React.
- [x] **Tri-Pane Layout**: Implement the side-nav, main table, and detail drawer layout.
- [x] **Knowledge Explorer**: Build a view to search and manage the `front_desk_knowledge` table.
- [x] **Alerts & Escalations**: Build real-time queues for `needs_review` and `thumbs_down` events.
- [x] **Trends Dashboard**: Build high-level metric cards for resolution rates and popular topics.

## Phase 5: Dockerization & Deployment (Milestone 5)
- [ ] **Dockerfile**: Create a multi-stage Dockerfile optimized for AWS App Runner (Python 3.11-slim).
- [ ] **CI/CD Prep**: Ensure environment variable handling for Supabase and Gemini API keys.
- [ ] **Validation**: Perform a full end-to-end test of the parent-to-admin feedback loop.
