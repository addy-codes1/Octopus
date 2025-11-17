# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **LangGraph-based Conversational RAG System** that implements an intelligent Retrieval-Augmented Generation pipeline with:
- Multi-turn conversation support with context preservation
- Intelligent question classification and filtering
- Automatic evaluation and refinement of search results
- Adaptive query optimization with retry logic (max 2 attempts)
- Complete dialogue memory management

The entire implementation is contained in a single file: [langgraph_rag_system.py](langgraph_rag_system.py)

## Running the System

### Setup
```bash
# Install dependencies (using uv - recommended)
uv sync

# Or using pip
pip install -r requirements.txt  # or install from pyproject.toml

# Create .env file with OpenAI API key
echo 'OPENAI_API_KEY="your-key-here"' > .env
```

### Execution
```bash
# Run the demo and interactive mode
uv run langgraph_rag_system.py

# Or with python directly
python langgraph_rag_system.py
```

The system will:
1. Run 3 demonstration scenarios automatically
2. Enter interactive mode where you can ask questions
3. Type 'quit' to exit

## Core Architecture

### State Graph Flow

The system is built as a **LangGraph StateGraph** with conditional routing. The flow is NOT linear - nodes route to different destinations based on evaluation results:

```
User Question (HumanMessage)
    ↓
[rephrase_query] → Converts follow-ups to standalone using chat history
    ↓
[classify_topic] → Determines if question is answerable
    ├─→ No → [reject_off_topic] → END
    └─→ Yes
        ↓
    [fetch_docs] → Retrieves from Chroma vector store
        ↓
    [evaluate_docs] → LLM grades each doc's relevance
        ├─→ Has relevant docs? → [create_response] → END
        ├─→ No docs & attempts < 2? → [tweak_question] → loops back to [fetch_docs]
        └─→ Max attempts reached? → [fallback_response] → END
```

### Key Implementation Details

**DialogState (TypedDict)**: The state container passed between nodes contains:
- `turns`: List[BaseMessage] - Full conversation history (HumanMessage + AIMessage)
- `retrieved_docs`: List[Document] - Current set of retrieved documents
- `topic_flag`: str - Classification result ('Yes'/'No')
- `refined_query`: str - Rewritten standalone query
- `ready_for_response`: bool - Whether we have relevant docs
- `refinement_attempts`: int - Retry counter (max 2)
- `question`: HumanMessage - Current user question

**Structured Outputs**: The system uses Pydantic models with `llm.with_structured_output()` for:
- `TopicGrade`: Ensures classification returns exactly 'Yes' or 'No'
- `RelevanceGrade`: Ensures document evaluation returns 'Yes' or 'No'

**Memory Persistence**: Uses `MemorySaver` checkpointer to maintain conversation state across questions within the same `thread_id`

### Routing Logic

**topic_router()**: Routes based on `topic_flag`
- "yes" → fetch_docs
- "no" → reject_off_topic

**decision_router()**: Routes based on evaluation results
- Has relevant docs (`ready_for_response=True`) → create_response
- No docs & attempts < 2 → tweak_question
- No docs & attempts >= 2 → fallback_response

### Document Store

- **Vector DB**: Chroma (in-memory by default)
- **Embeddings**: OpenAI's text-embedding-3-small
- **Retrieval**: Top-k=2 documents per query
- **Sample Docs**: 4 hardcoded documents about "Bella Vista" restaurant (owner, prices, hours, menus)

To replace with custom documents, modify `DocumentManager.create_sample_documents()` or use LangChain document loaders (TextLoader, PyPDFLoader, etc.)

## Important Patterns

### Multi-turn Context Handling

The `rephrase_query` node checks conversation history:
```python
if len(state["turns"]) > 1:
    # Has history - rephrase using full context
    chat_history = state["turns"][:-1]
    # Invoke LLM with history + current question
else:
    # First question - use as-is
```

### Retry Mechanism

When `evaluate_docs` finds no relevant documents:
1. First attempt: Routes to `tweak_question` → increments `refinement_attempts`
2. Second attempt: Routes to `tweak_question` again
3. Third attempt: Routes to `fallback_response` (gives up)

The `tweak_question` node asks the LLM to "slightly refine" the query to improve retrieval.

### Thread Management

Each conversation thread is isolated via `thread_id` in the graph config:
```python
result = graph.invoke(
    input={"question": HumanMessage(content=question)},
    config={"configurable": {"thread_id": thread_id}}
)
```

Different `thread_id` values maintain separate conversation histories.

## Configuration

### LLM Settings
- Model: `gpt-4o-mini`
- Temperature: `0` (deterministic responses)
- All LLM calls use the same model instance

### Customization Points

**Retrieval parameters**: Modify `DocumentManager.setup_retriever()`:
```python
retriever = db.as_retriever(search_kwargs={"k": 5})  # Increase docs
```

**Max retry attempts**: Change the hardcoded `2` in `decision_router()` and `tweak_question()`

**Topic scope**: Edit the system message in `classify_topic()` to define what's "on-topic"

**LLM model**: Change in `RAGSystem.__init__()`:
```python
self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)  # Different model/temp
```

## Dependencies

Managed via pyproject.toml:
- langchain, langchain-openai, langchain-community (core LLM framework)
- langgraph (state graph orchestration)
- chromadb (vector database)
- python-dotenv (environment variables)
- jupyter, pillow (optional for visualization)

Python version: >= 3.11 (specified in pyproject.toml)

## Testing Scenarios

The `run_demo()` method includes 3 built-in test scenarios:
1. **Off-topic question**: "How is the weather?" → Should reject
2. **Unanswerable question**: "How old is the owner?" → Should exhaust retries and give fallback
3. **Follow-up conversation**: "When does Bella Vista open?" then "Also on Sunday?" → Should use context to rephrase

These scenarios validate the core routing logic and are good smoke tests after modifications.
