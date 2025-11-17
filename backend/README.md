# ScholarChat Backend

FastAPI backend for ScholarChat - Academic Research RAG Assistant.

## Features

- **JWT Authentication**: Register, login, and refresh tokens
- **Paper Management**: Upload PDFs, extract metadata, manage library
- **Conversational RAG**: Question answering with source citations
- **Vector Search**: Chroma-based semantic search across papers
- **SSE Streaming**: Real-time chat responses

## Quick Start

### Using Docker (Recommended)

```bash
# From project root
docker-compose up -d

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Local Development

1. **Set up PostgreSQL**:
```bash
# Create database
createdb scholarchat
```

2. **Configure Environment**:
```bash
cd backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
# Or using uv from project root:
uv sync
```

4. **Run Migrations**:
```bash
cd backend
alembic upgrade head
```

5. **Start Server**:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile

### Papers
- `POST /api/v1/papers/upload` - Upload PDF paper
- `GET /api/v1/papers` - List user's papers
- `GET /api/v1/papers/{id}` - Get paper details
- `PUT /api/v1/papers/{id}` - Update paper metadata
- `DELETE /api/v1/papers/{id}` - Delete paper

### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation with messages
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### Chat
- `POST /api/v1/chat` - Chat with SSE streaming
- `POST /api/v1/chat/query` - Chat without streaming

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (auth)
│   │   └── v1/
│   │       ├── endpoints/       # API endpoints
│   │       │   ├── auth.py
│   │       │   ├── papers.py
│   │       │   ├── conversations.py
│   │       │   └── chat.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py            # Settings
│   │   └── security.py          # JWT & password hashing
│   ├── db/
│   │   ├── base.py              # SQLAlchemy base
│   │   └── session.py           # Database session
│   ├── models/                  # Database models
│   │   ├── user.py
│   │   ├── paper.py
│   │   ├── conversation.py
│   │   └── citation.py
│   ├── schemas/                 # Pydantic schemas
│   │   ├── user.py
│   │   ├── paper.py
│   │   └── conversation.py
│   ├── services/                # Business logic
│   │   ├── pdf_processor.py     # PDF text extraction
│   │   ├── vector_store.py      # Chroma operations
│   │   └── rag_service.py       # LangGraph RAG pipeline
│   └── main.py                  # FastAPI app
├── alembic/                     # Database migrations
├── tests/                       # Unit tests
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── .env.example
```

## RAG Pipeline

The RAG service uses LangGraph for conversational question answering:

1. **Rephrase Query**: Convert follow-ups to standalone questions
2. **Classify Topic**: Ensure question is research-related
3. **Fetch Documents**: Retrieve from Chroma vector store
4. **Evaluate Relevance**: Grade each document
5. **Generate Response**: Create cited answer
6. **Retry Logic**: Refine query if no relevant docs found

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `SECRET_KEY` | JWT signing key | Change in production |
| `CHUNK_SIZE` | Text chunk size for embeddings | 1000 |
| `VECTOR_SEARCH_K` | Number of documents to retrieve | 5 |

## Testing

```bash
cd backend
pytest
```

## Next Steps (Week 2)

- [ ] Citation extraction from papers
- [ ] DOI lookup integration
- [ ] BibTeX/RIS export
- [ ] Academic-specific prompts (contradictions, gaps)
