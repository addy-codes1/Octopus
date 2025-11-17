"""PDF processing service for extracting text and metadata."""
import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader


class PDFProcessor:
    """Process PDF files to extract text and metadata."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract all text from a PDF file."""
        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    @staticmethod
    def get_page_count(file_path: str) -> int:
        """Get the number of pages in a PDF."""
        reader = PdfReader(file_path)
        return len(reader.pages)

    @staticmethod
    def extract_metadata(file_path: str) -> dict:
        """Extract metadata from PDF."""
        reader = PdfReader(file_path)
        metadata = reader.metadata

        result = {}
        if metadata:
            if metadata.title:
                result["title"] = str(metadata.title)
            if metadata.author:
                result["author"] = str(metadata.author)
            if metadata.subject:
                result["subject"] = str(metadata.subject)
            if metadata.creator:
                result["creator"] = str(metadata.creator)

        return result

    @staticmethod
    def extract_title_from_text(text: str) -> Optional[str]:
        """Attempt to extract title from the first page text."""
        lines = text.split("\n")
        # Usually the title is in the first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            # Title usually is a substantial line but not too long
            if 10 < len(line) < 200 and not line.startswith("http"):
                # Skip lines that look like authors or dates
                if not re.match(r"^\d{4}", line) and "@" not in line:
                    return line
        return None

    @staticmethod
    def extract_abstract(text: str) -> Optional[str]:
        """Attempt to extract abstract from the paper."""
        # Look for abstract section
        abstract_match = re.search(
            r"(?:^|\n)\s*(?:ABSTRACT|Abstract)\s*\n(.*?)(?:\n\s*(?:1\.|Introduction|INTRODUCTION|Keywords|KEYWORDS)|\Z)",
            text,
            re.DOTALL | re.IGNORECASE
        )

        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # Clean up the abstract
            abstract = re.sub(r"\s+", " ", abstract)
            # Limit length
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "..."
            return abstract

        return None

    @staticmethod
    def extract_authors_from_text(text: str) -> list[str]:
        """Attempt to extract author names from text."""
        # This is a simplified heuristic - real implementation would be more sophisticated
        lines = text.split("\n")
        authors = []

        for i, line in enumerate(lines[1:15]):  # Check lines after title
            line = line.strip()
            # Look for lines that might contain author names
            # Authors often have commas, "and", or institutional affiliations
            if line and len(line) < 200:
                # Check if line contains typical author patterns
                if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
                    # Split by common delimiters
                    potential_authors = re.split(r",\s*(?:and\s+)?|\s+and\s+", line)
                    for name in potential_authors:
                        name = name.strip()
                        # Basic validation - name should have 2-4 words
                        words = name.split()
                        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                            # Remove numbers and special characters
                            if not re.search(r"[\d@]", name):
                                authors.append(name)
                    if authors:
                        break

        return authors[:10]  # Limit to 10 authors

    @staticmethod
    def extract_doi(text: str) -> Optional[str]:
        """Extract DOI from text."""
        # DOI pattern
        doi_match = re.search(r"10\.\d{4,}/[^\s]+", text)
        if doi_match:
            doi = doi_match.group(0)
            # Clean up - remove trailing punctuation
            doi = re.sub(r"[.,;:)\]]+$", "", doi)
            return doi
        return None

    @staticmethod
    def extract_year(text: str) -> Optional[int]:
        """Extract publication year from text."""
        # Look for year patterns near the beginning
        year_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", text[:5000])
        if year_match:
            year = int(year_match.group(1))
            # Validate year is reasonable
            if 1900 <= year <= 2030:
                return year
        return None
