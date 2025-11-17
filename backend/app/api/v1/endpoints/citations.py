"""Citation management and export endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....models.paper import Paper
from ....models.user import User
from ....services.citation_extractor import CitationExtractor
from ....services.doi_lookup import DOILookupService
from ....services.pdf_processor import PDFProcessor
from ...deps import get_current_user

router = APIRouter()


@router.get("/{paper_id}")
def get_paper_citations(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Extract citations from a paper."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    if not paper.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper has no associated file"
        )

    # Extract text from PDF
    try:
        text = PDFProcessor.extract_text(paper.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read paper: {str(e)}"
        )

    # Extract references section
    extractor = CitationExtractor()
    refs_section = extractor.extract_references_section(text)
    references = extractor.parse_references(refs_section)

    # Extract in-text citations
    in_text = extractor.extract_in_text_citations(text)

    return {
        "paper_id": str(paper_id),
        "paper_title": paper.title,
        "references": references,
        "in_text_citations": in_text[:100],  # Limit to first 100
        "total_references": len(references),
        "total_in_text": len(in_text),
    }


@router.post("/lookup-doi")
async def lookup_doi(
    doi: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Look up paper metadata by DOI."""
    result = await DOILookupService.lookup_doi(doi)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DOI not found or service unavailable"
        )

    return result


@router.post("/search")
async def search_papers_by_title(
    title: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Search for papers by title using CrossRef."""
    results = await DOILookupService.search_by_title(title, limit)
    return results


@router.get("/export/bibtex", response_class=PlainTextResponse)
def export_bibtex(
    paper_ids: str = Query(..., description="Comma-separated paper IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    """Export papers in BibTeX format."""
    ids = [uuid.UUID(pid.strip()) for pid in paper_ids.split(",")]

    papers = db.query(Paper).filter(
        Paper.id.in_(ids),
        Paper.user_id == current_user.id
    ).all()

    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No papers found"
        )

    bibtex_entries = []
    for paper in papers:
        # Create reference dict from paper
        ref = {
            "authors": paper.authors or [],
            "title": paper.title,
            "year": paper.year,
            "journal": paper.metadata.get("journal", ""),
            "volume": paper.metadata.get("volume", ""),
            "pages": paper.metadata.get("pages", ""),
            "doi": paper.doi,
        }

        # Generate key
        if ref["authors"]:
            first_author = ref["authors"][0].split()[-1].lower()
        else:
            first_author = "unknown"
        key = f"{first_author}{ref['year'] or '0000'}"

        bibtex_entries.append(CitationExtractor.format_bibtex(ref, key))

    return "\n\n".join(bibtex_entries)


@router.get("/export/ris", response_class=PlainTextResponse)
def export_ris(
    paper_ids: str = Query(..., description="Comma-separated paper IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    """Export papers in RIS format."""
    ids = [uuid.UUID(pid.strip()) for pid in paper_ids.split(",")]

    papers = db.query(Paper).filter(
        Paper.id.in_(ids),
        Paper.user_id == current_user.id
    ).all()

    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No papers found"
        )

    ris_entries = []
    for paper in papers:
        ref = {
            "authors": paper.authors or [],
            "title": paper.title,
            "year": paper.year,
            "journal": paper.metadata.get("journal", ""),
            "volume": paper.metadata.get("volume", ""),
            "pages": paper.metadata.get("pages", ""),
            "doi": paper.doi,
        }
        ris_entries.append(CitationExtractor.format_ris(ref))

    return "\n\n".join(ris_entries)


@router.get("/export/apa", response_class=PlainTextResponse)
def export_apa(
    paper_ids: str = Query(..., description="Comma-separated paper IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    """Export papers in APA format."""
    ids = [uuid.UUID(pid.strip()) for pid in paper_ids.split(",")]

    papers = db.query(Paper).filter(
        Paper.id.in_(ids),
        Paper.user_id == current_user.id
    ).all()

    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No papers found"
        )

    apa_entries = []
    for paper in papers:
        ref = {
            "authors": paper.authors or [],
            "title": paper.title,
            "year": paper.year,
            "journal": paper.metadata.get("journal", ""),
            "volume": paper.metadata.get("volume", ""),
            "pages": paper.metadata.get("pages", ""),
            "doi": paper.doi,
        }
        apa_entries.append(CitationExtractor.format_apa(ref))

    return "\n\n".join(apa_entries)
