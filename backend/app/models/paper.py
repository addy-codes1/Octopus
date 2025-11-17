"""Paper database model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from ..db.base import Base


class Paper(Base):
    """Paper model for storing uploaded academic papers."""

    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(String), default=[])
    year = Column(Integer, nullable=True)
    doi = Column(String(255), nullable=True)
    abstract = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    page_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})

    # Vector store reference
    chroma_collection_id = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="papers")
    citing_papers = relationship(
        "Citation",
        foreign_keys="Citation.paper_id",
        back_populates="source_paper",
        cascade="all, delete-orphan"
    )
    cited_papers = relationship(
        "Citation",
        foreign_keys="Citation.cited_paper_id",
        back_populates="cited_paper",
        cascade="all, delete-orphan"
    )
