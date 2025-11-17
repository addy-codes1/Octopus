"""RAG service based on LangGraph for conversational question answering."""
from typing import Any, Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from ..core.config import get_settings
from .vector_store import VectorStoreService

settings = get_settings()


class TopicGrade(BaseModel):
    """Grade for topic relevance."""

    is_relevant: str = Field(description="Is the question relevant? Answer 'Yes' or 'No'")


class RelevanceGrade(BaseModel):
    """Grade for document relevance."""

    is_relevant: str = Field(description="Is the document relevant? Answer 'Yes' or 'No'")


class RAGState(TypedDict):
    """State for the RAG graph."""

    turns: list[BaseMessage]
    question: HumanMessage
    retrieved_docs: list[Document]
    topic_flag: str
    refined_query: str
    ready_for_response: bool
    refinement_attempts: int
    user_id: UUID
    paper_ids: list[UUID]
    citations: list[dict]


class ScholarRAGService:
    """RAG service for academic paper question answering."""

    def __init__(self):
        """Initialize the RAG service."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.vector_service = VectorStoreService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("rephrase_query", self._rephrase_query)
        workflow.add_node("classify_topic", self._classify_topic)
        workflow.add_node("fetch_docs", self._fetch_docs)
        workflow.add_node("evaluate_docs", self._evaluate_docs)
        workflow.add_node("create_response", self._create_response)
        workflow.add_node("tweak_question", self._tweak_question)
        workflow.add_node("fallback_response", self._fallback_response)
        workflow.add_node("reject_off_topic", self._reject_off_topic)

        # Set entry point
        workflow.set_entry_point("rephrase_query")

        # Add edges
        workflow.add_edge("rephrase_query", "classify_topic")
        workflow.add_conditional_edges(
            "classify_topic",
            self._topic_router,
            {
                "relevant": "fetch_docs",
                "not_relevant": "reject_off_topic"
            }
        )
        workflow.add_edge("fetch_docs", "evaluate_docs")
        workflow.add_conditional_edges(
            "evaluate_docs",
            self._decision_router,
            {
                "create_response": "create_response",
                "tweak_question": "tweak_question",
                "fallback_response": "fallback_response"
            }
        )
        workflow.add_edge("tweak_question", "fetch_docs")
        workflow.add_edge("create_response", END)
        workflow.add_edge("fallback_response", END)
        workflow.add_edge("reject_off_topic", END)

        return workflow.compile()

    def _rephrase_query(self, state: RAGState) -> dict[str, Any]:
        """Rephrase follow-up questions to standalone queries."""
        if len(state["turns"]) > 1:
            # Has conversation history - rephrase
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant that rephrases follow-up questions to be standalone questions.
Given the conversation history and the latest question, rephrase the question to be self-contained.
The rephrased question should include all necessary context from the conversation."""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "Latest question: {question}\n\nRephrase this to be a standalone question:")
            ])

            chain = prompt | self.llm
            response = chain.invoke({
                "chat_history": state["turns"][:-1],
                "question": state["question"].content
            })
            refined = response.content.strip()
        else:
            refined = state["question"].content

        return {"refined_query": refined}

    def _classify_topic(self, state: RAGState) -> dict[str, Any]:
        """Classify if the question is about academic research papers."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a classifier that determines if a question is about academic research, papers, or literature review.
Answer 'Yes' if the question is asking about:
- Content of research papers
- Academic concepts, findings, or methodologies
- Comparisons between papers
- Research gaps or contradictions
- Specific authors, citations, or studies
- General academic or research-related questions

Answer 'No' if the question is:
- Completely unrelated to academic research
- About personal matters
- About general knowledge not related to research

Be lenient - if there's any chance the question relates to research papers, answer 'Yes'."""),
            ("human", "Question: {question}\n\nIs this relevant to academic research?")
        ])

        structured_llm = self.llm.with_structured_output(TopicGrade)
        chain = prompt | structured_llm
        result = chain.invoke({"question": state["refined_query"]})

        return {"topic_flag": result.is_relevant.lower()}

    def _topic_router(self, state: RAGState) -> str:
        """Route based on topic classification."""
        if state["topic_flag"] == "yes":
            return "relevant"
        return "not_relevant"

    def _fetch_docs(self, state: RAGState) -> dict[str, Any]:
        """Fetch relevant documents from vector store."""
        docs = self.vector_service.search(
            user_id=state["user_id"],
            query=state["refined_query"],
            paper_ids=state["paper_ids"] if state["paper_ids"] else None,
            k=settings.VECTOR_SEARCH_K
        )
        return {"retrieved_docs": docs}

    def _evaluate_docs(self, state: RAGState) -> dict[str, Any]:
        """Evaluate relevance of retrieved documents."""
        relevant_docs = []
        citations = []

        for doc in state["retrieved_docs"]:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains any information that could help answer the question, answer 'Yes'.
Be lenient - partial relevance counts as relevant."""),
                ("human", "Document: {document}\n\nQuestion: {question}\n\nIs this document relevant?")
            ])

            structured_llm = self.llm.with_structured_output(RelevanceGrade)
            chain = prompt | structured_llm
            result = chain.invoke({
                "document": doc.page_content[:2000],
                "question": state["refined_query"]
            })

            if result.is_relevant.lower() == "yes":
                relevant_docs.append(doc)
                # Create citation entry
                citation = {
                    "paper_id": doc.metadata.get("paper_id", ""),
                    "paper_title": doc.metadata.get("paper_title", "Unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                }
                citations.append(citation)

        ready = len(relevant_docs) > 0
        return {
            "retrieved_docs": relevant_docs,
            "ready_for_response": ready,
            "citations": citations
        }

    def _decision_router(self, state: RAGState) -> str:
        """Route based on document evaluation."""
        if state["ready_for_response"]:
            return "create_response"
        elif state.get("refinement_attempts", 0) < settings.MAX_REFINEMENT_ATTEMPTS:
            return "tweak_question"
        else:
            return "fallback_response"

    def _create_response(self, state: RAGState) -> dict[str, Any]:
        """Create the final response with citations."""
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(state["retrieved_docs"], 1):
            paper_title = doc.metadata.get("paper_title", "Unknown Paper")
            context_parts.append(f"[{i}] From '{paper_title}':\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are ScholarChat, an academic research assistant helping with literature reviews.
Answer questions based on the provided research paper excerpts.
Always cite your sources using [1], [2], etc. notation matching the document numbers.
Be precise and academic in your responses.
If the information is partial, acknowledge what's known and what's not.
Format your response clearly with proper paragraphs."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """Context from research papers:
{context}

Question: {question}

Provide a well-cited answer:""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "chat_history": state["turns"][:-1] if len(state["turns"]) > 1 else [],
            "context": context,
            "question": state["refined_query"]
        })

        # Add assistant message to turns
        ai_message = AIMessage(content=response.content)
        new_turns = state["turns"] + [ai_message]

        return {"turns": new_turns}

    def _tweak_question(self, state: RAGState) -> dict[str, Any]:
        """Refine the query to improve retrieval."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are helping to refine a search query to find better results in academic papers.
The current query didn't find relevant results. Suggest a slightly different phrasing that might work better.
Consider:
- Using synonyms
- Being more specific or more general
- Using different academic terminology"""),
            ("human", "Original query: {query}\n\nProvide a refined version:")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"query": state["refined_query"]})

        attempts = state.get("refinement_attempts", 0) + 1
        return {
            "refined_query": response.content.strip(),
            "refinement_attempts": attempts
        }

    def _fallback_response(self, state: RAGState) -> dict[str, Any]:
        """Provide a fallback response when no relevant docs found."""
        message = """I couldn't find relevant information in your uploaded papers to answer this question.

This could be because:
- The specific information isn't in your uploaded papers
- Try rephrasing your question with different keywords
- Upload additional papers that might contain this information

Would you like to try asking in a different way?"""

        ai_message = AIMessage(content=message)
        new_turns = state["turns"] + [ai_message]
        return {"turns": new_turns, "citations": []}

    def _reject_off_topic(self, state: RAGState) -> dict[str, Any]:
        """Reject off-topic questions."""
        message = """I'm designed to help with questions about your research papers and academic literature review.

I can help you with:
- Finding information in your uploaded papers
- Comparing methodologies across studies
- Identifying contradictions or gaps in research
- Summarizing key findings

Please ask a question related to your research papers."""

        ai_message = AIMessage(content=message)
        new_turns = state["turns"] + [ai_message]
        return {"turns": new_turns, "citations": []}

    def process_question(
        self,
        question: str,
        user_id: UUID,
        paper_ids: Optional[list[UUID]] = None,
        conversation_history: Optional[list[dict]] = None
    ) -> dict[str, Any]:
        """
        Process a user question through the RAG pipeline.

        Args:
            question: The user's question
            user_id: User's ID
            paper_ids: Optional list of paper IDs to search within
            conversation_history: Optional previous messages in the conversation

        Returns:
            Dictionary with answer and citations
        """
        # Build conversation turns
        turns = []
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    turns.append(HumanMessage(content=msg["content"]))
                else:
                    turns.append(AIMessage(content=msg["content"]))

        # Add current question
        human_message = HumanMessage(content=question)
        turns.append(human_message)

        # Initialize state
        initial_state = {
            "turns": turns,
            "question": human_message,
            "retrieved_docs": [],
            "topic_flag": "",
            "refined_query": "",
            "ready_for_response": False,
            "refinement_attempts": 0,
            "user_id": user_id,
            "paper_ids": paper_ids or [],
            "citations": []
        }

        # Run the graph
        result = self.graph.invoke(initial_state)

        # Extract the answer
        answer = ""
        if result["turns"] and len(result["turns"]) > len(turns) - 1:
            last_message = result["turns"][-1]
            if isinstance(last_message, AIMessage):
                answer = last_message.content

        return {
            "answer": answer,
            "citations": result.get("citations", []),
            "refined_query": result.get("refined_query", question)
        }
