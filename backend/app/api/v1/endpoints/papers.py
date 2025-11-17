"""Paper management endpoints."""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session

from ....core.config import get_settings
from ....db.session import get_db
from ....models.paper import Paper
from ....models.user import User
from ....schemas.paper import PaperResponse, PaperList, PaperCreate
from ....services.pdf_processor import PDFProcessor
from ....services.vector_store import VectorStoreService
from ...deps import get_current_user

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paper:
    """Upload a PDF paper and process it."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
        )

    # Create user upload directory
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)

    # Save file
    paper_id = uuid.uuid4()
    file_path = os.path.join(user_upload_dir, f"{paper_id}.pdf")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Process PDF
    try:
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(file_path)
        page_count = pdf_processor.get_page_count(file_path)
        pdf_metadata = pdf_processor.extract_metadata(file_path)

        # Extract information from text
        title = pdf_metadata.get("title") or pdf_processor.extract_title_from_text(text) or file.filename
        abstract = pdf_processor.extract_abstract(text)
        authors = pdf_processor.extract_authors_from_text(text)
        doi = pdf_processor.extract_doi(text)
        year = pdf_processor.extract_year(text)

        # Create paper record
        paper = Paper(
            id=paper_id,
            user_id=current_user.id,
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            abstract=abstract,
            file_path=file_path,
            file_size=file_size,
            page_count=page_count,
            metadata=pdf_metadata,
        )
        db.add(paper)
        db.commit()

        # Add to vector store
        try:
            vector_service = VectorStoreService()
            num_chunks = vector_service.add_paper(
                user_id=current_user.id,
                paper_id=paper_id,
                title=title,
                text=text,
                metadata={
                    "authors": ", ".join(authors) if authors else "",
                    "year": year or "",
                    "doi": doi or "",
                }
            )
            paper.chroma_collection_id = f"{num_chunks}_chunks"
            db.commit()
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Warning: Failed to add to vector store: {e}")

        db.refresh(paper)
        return paper

    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.get("", response_model=PaperList)
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List user's papers with pagination."""
    query = db.query(Paper).filter(Paper.user_id == current_user.id)

    if search:
        query = query.filter(
            Paper.title.ilike(f"%{search}%") |
            Paper.abstract.ilike(f"%{search}%")
        )

    total = query.count()
    papers = (
        query
        .order_by(Paper.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paper:
    """Get a specific paper."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
def update_paper(
    paper_id: uuid.UUID,
    paper_data: PaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paper:
    """Update paper metadata."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    paper.title = paper_data.title
    paper.authors = paper_data.authors
    paper.year = paper_data.year
    paper.doi = paper_data.doi
    paper.abstract = paper_data.abstract

    db.commit()
    db.refresh(paper)
    return paper


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(
    paper_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a paper."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    # Delete from vector store
    try:
        vector_service = VectorStoreService()
        vector_service.delete_paper(current_user.id, paper_id)
    except Exception as e:
        print(f"Warning: Failed to delete from vector store: {e}")

    # Delete file
    if paper.file_path and os.path.exists(paper.file_path):
        try:
            os.remove(paper.file_path)
        except Exception as e:
            print(f"Warning: Failed to delete file: {e}")

    # Delete from database
    db.delete(paper)
    db.commit()
