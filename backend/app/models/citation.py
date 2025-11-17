"""Citation database model."""
import uuid

from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base import Base


class Citation(Base):
    """Citation model for tracking paper references."""

    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False)
    cited_paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True)
    citation_text = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)

    # Relationships
    source_paper = relationship("Paper", foreign_keys=[paper_id], back_populates="citing_papers")
    cited_paper = relationship("Paper", foreign_keys=[cited_paper_id], back_populates="cited_papers")
