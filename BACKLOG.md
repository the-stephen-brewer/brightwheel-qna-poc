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
- [x] **Testing**: Validated RAG retrieval and response generation through end-to-end bug fixing.

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

- [x] **Dockerfile**: Created a multi-stage Dockerfile optimized for AWS App Runner (Python 3.11-slim).
- [x] **CI/CD Prep**: Set up GitHub Actions workflow for frontend deployments to S3.
- [x] **Validation**: Completed end-to-end bug fixing and production deployment readiness.

## Phase 6: Polish

- [x] **UI Cleanup**: make trends the first tab inbstead of knowledge base. Change resolution rate to 'AI Ticket Deflection Rate'. Change the top category box to be on its own row and show what category is getting the most questions with a question count and some sample questions from users
- [x] **Knowledge base cleanup**: The knowledge base from the PDF didn't parse super well. We should consider converting the PDF to markdown first then chunking and loading using markdown. Can then use headers and groupings to identify a category as the current knowlege base has no category settings.
- [x] **Suggestion pills**: On the parent front end change our suggested topic pills to be "Fever policy","Handling medication","Bringing sunscreen", "When is nap time?".
- [x] **Deeper responses**: Update the AI to try and do more than just search and respond with the exact policy but be a bit more helpful in the response by finding other policy details that might be helpful
- [x] **Reminder system**: Create a reminders.json file with mock data about key dates and events at the school coming up. For example, the teacher Ms Kate birthday is May 30th. Have the AI check the reminders section and provide a reminder about any upcoming events the parent might want to be informed about. Make sure to only provide the reminders once every 3 days.
