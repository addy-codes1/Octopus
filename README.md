# ScholarChat - Academic Research RAG Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18.3-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-teal.svg)

**An affordable, beautiful literature review assistant for PhD students and researchers.**

ScholarChat is a self-hosted RAG (Retrieval-Augmented Generation) chatbot optimized for academic research, supporting 500+ papers at minimal cost.

## The Problem

- PhD students spend 10+ hours/week manually reviewing papers
- NVivo costs $800-1,400/year
- NotebookLM crashes with 100+ documents
- No affordable tool for conversational Q&A over large paper collections

## Features

- **PDF Upload**: Drag-and-drop with automatic metadata extraction
- **Conversational Q&A**: Multi-turn conversations with source citations
- **Academic Analysis**: Find contradictions, compare methodologies, identify gaps
- **Smart Citations**: Every answer cites specific papers [1], [2], [3]
- **Export**: BibTeX, RIS, APA bibliography formats
- **Beautiful UI**: Dark-themed interface optimized for researchers

## Quick Start

### Docker (Recommended)

```bash
# Clone and configure
git clone <repo-url>
cd scholarchat
cp backend/.env.example backend/.env
# Edit backend/.env with your OPENAI_API_KEY

# Start services
docker-compose up -d

# API: http://localhost:8000/docs
# Frontend: npm run dev in frontend/
```

### Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
createdb scholarchat
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   React UI      │────▶│   FastAPI        │────▶│  PostgreSQL │
│   (Vite+TS)     │     │   (LangGraph)    │     │  + Chroma   │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

### RAG Pipeline (LangGraph)

1. **Rephrase** → Convert follow-ups to standalone questions
2. **Classify** → Is this research-related?
3. **Retrieve** → Semantic search in Chroma (top-k=5)
4. **Evaluate** → Grade document relevance
5. **Generate** → Create cited response with academic prompts
6. **Retry** → Refine query if no relevant docs (max 2 attempts)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + LangGraph + LangChain |
| Database | PostgreSQL + Chroma (vectors) |
| LLM | OpenAI GPT-4o-mini |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS + shadcn/ui |
| State | Zustand + React Query |
| Auth | JWT tokens |

## API Endpoints

```
POST /api/v1/auth/register     - Create account
POST /api/v1/auth/login        - Get JWT tokens
POST /api/v1/papers/upload     - Upload PDF
GET  /api/v1/papers            - List papers
POST /api/v1/chat/query        - Ask question
GET  /api/v1/citations/export  - Export bibliography
```

## Project Structure

```
scholarchat/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # REST endpoints
│   │   ├── services/
│   │   │   ├── rag_service.py          # LangGraph pipeline
│   │   │   ├── pdf_processor.py        # PDF extraction
│   │   │   ├── citation_extractor.py   # Parse references
│   │   │   └── academic_prompts.py     # Specialized prompts
│   │   └── models/            # SQLAlchemy models
│   ├── alembic/               # Migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/             # Login, Dashboard, Papers
│   │   ├── components/        # UI components
│   │   └── lib/api.ts         # API client
│   └── vercel.json            # Deployment
└── docker-compose.yml
```

## Configuration

Key environment variables (backend/.env):

```env
OPENAI_API_KEY=sk-...           # Required
DATABASE_URL=postgresql://...
SECRET_KEY=your-jwt-secret
CHUNK_SIZE=1000                 # Text chunking
VECTOR_SEARCH_K=5               # Documents to retrieve
```

## Deployment

- **Frontend**: Vercel (free tier)
- **Backend**: Render.com (free tier)
- **Database**: Neon PostgreSQL (free tier)

**Cost**: ~$15/month at scale (mostly OpenAI API)

## Academic Features

Ask questions like:
- "What contradictions exist across these papers?"
- "Compare the methodologies used in these studies"
- "What research gaps are identified?"
- "Summarize key findings from all papers"

The system uses specialized prompts for academic analysis, providing structured, cited responses.

## Development

```bash
# Backend tests
cd backend && pytest

# Frontend lint
cd frontend && npm run lint

# CI/CD
GitHub Actions automatically runs tests and builds on push
```

## Roadmap

- [x] Core RAG pipeline with citations
- [x] PDF processing and metadata extraction
- [x] React frontend with dark theme
- [x] JWT authentication
- [x] BibTeX/RIS export
- [ ] Real-time SSE streaming
- [ ] Collaborative workspaces
- [ ] ArXiv/PubMed integration
- [ ] Citation graph visualization

## License

MIT License

---

**Built for researchers who deserve better tools.**

Based on the LangGraph RAG system pattern - see `/langgraph_rag_system.py` for the original implementation.
