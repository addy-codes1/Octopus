"""Citation extraction service for parsing references from academic papers."""
import re
from typing import Optional


class CitationExtractor:
    """Extract and parse citations from academic papers."""

    @staticmethod
    def extract_references_section(text: str) -> str:
        """Extract the references/bibliography section from paper text."""
        # Common section headers
        patterns = [
            r"(?:^|\n)\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography|WORKS CITED|Works Cited)\s*\n(.*?)(?:\n\s*(?:APPENDIX|Appendix|$))",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no clear section found, look for numbered references at the end
        lines = text.split("\n")
        ref_lines = []
        in_refs = False

        for line in reversed(lines):
            line = line.strip()
            if re.match(r"^\[\d+\]|\d+\.\s+[A-Z]", line):
                in_refs = True
            if in_refs:
                ref_lines.append(line)
                if len(ref_lines) > 200:  # Safety limit
                    break

        if ref_lines:
            return "\n".join(reversed(ref_lines))

        return ""

    @staticmethod
    def parse_references(references_text: str) -> list[dict]:
        """Parse individual references from the references section."""
        references = []

        # Split by common reference patterns
        # Pattern 1: [1] Author...
        if re.search(r"^\[\d+\]", references_text, re.MULTILINE):
            parts = re.split(r"\n(?=\[\d+\])", references_text)
        # Pattern 2: 1. Author...
        elif re.search(r"^\d+\.\s+[A-Z]", references_text, re.MULTILINE):
            parts = re.split(r"\n(?=\d+\.\s+[A-Z])", references_text)
        else:
            # Try to split by empty lines or author patterns
            parts = re.split(r"\n\n+", references_text)

        for part in parts:
            part = part.strip()
            if not part or len(part) < 20:
                continue

            ref = CitationExtractor._parse_single_reference(part)
            if ref:
                references.append(ref)

        return references

    @staticmethod
    def _parse_single_reference(text: str) -> Optional[dict]:
        """Parse a single reference entry."""
        # Clean up the text
        text = re.sub(r"^\[\d+\]|\d+\.\s+", "", text).strip()

        if not text:
            return None

        ref = {
            "raw_text": text,
            "authors": [],
            "title": "",
            "year": None,
            "doi": None,
            "journal": "",
            "volume": "",
            "pages": "",
        }

        # Extract DOI
        doi_match = re.search(r"10\.\d{4,}/[^\s]+", text)
        if doi_match:
            ref["doi"] = re.sub(r"[.,;:)\]]+$", "", doi_match.group(0))

        # Extract year (usually in parentheses or after authors)
        year_match = re.search(r"\((\d{4})\)|\b(19\d{2}|20[0-2]\d)\b", text)
        if year_match:
            ref["year"] = int(year_match.group(1) or year_match.group(2))

        # Extract authors (before year or before title)
        # Common pattern: "Author, A., Author, B., & Author, C. (Year)"
        author_match = re.match(r"^(.+?)\s*(?:\(?\d{4}\)?)", text)
        if author_match:
            authors_text = author_match.group(1)
            # Split by ", and " or " & " or ", "
            author_parts = re.split(r",\s*(?:and|&)\s*|,\s*(?=[A-Z])", authors_text)
            for author in author_parts:
                author = author.strip()
                if author and len(author) > 2:
                    ref["authors"].append(author)

        # Extract title (usually in quotes or after year)
        title_match = re.search(r'"([^"]+)"|\(?\d{4}\)?[.,]?\s*([^.]+?)(?:\.|$)', text)
        if title_match:
            ref["title"] = (title_match.group(1) or title_match.group(2) or "").strip()

        # Extract journal/venue
        journal_match = re.search(r"(?:In\s+)?([A-Z][^,]+(?:Journal|Conference|Proceedings|Review|Magazine)[^,]*)", text, re.IGNORECASE)
        if journal_match:
            ref["journal"] = journal_match.group(1).strip()

        # Extract volume and pages
        vol_match = re.search(r"(\d+)\s*[:(]\s*(\d+[-–]\d+)", text)
        if vol_match:
            ref["volume"] = vol_match.group(1)
            ref["pages"] = vol_match.group(2)

        return ref

    @staticmethod
    def extract_in_text_citations(text: str) -> list[dict]:
        """Extract in-text citations like (Author, Year) or [1]."""
        citations = []

        # Pattern 1: (Author, Year) or (Author & Author, Year)
        author_year_pattern = r"\(([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&|and)\s+[A-Z][a-z]+)*),?\s*(\d{4})\)"
        for match in re.finditer(author_year_pattern, text):
            citations.append({
                "type": "author_year",
                "authors": match.group(1),
                "year": int(match.group(2)),
                "position": match.start(),
            })

        # Pattern 2: [1] or [1, 2, 3]
        numbered_pattern = r"\[(\d+(?:\s*,\s*\d+)*)\]"
        for match in re.finditer(numbered_pattern, text):
            numbers = [int(n.strip()) for n in match.group(1).split(",")]
            citations.append({
                "type": "numbered",
                "numbers": numbers,
                "position": match.start(),
            })

        return citations

    @staticmethod
    def format_apa(ref: dict) -> str:
        """Format a reference in APA style."""
        parts = []

        # Authors
        if ref.get("authors"):
            if len(ref["authors"]) == 1:
                parts.append(ref["authors"][0])
            elif len(ref["authors"]) == 2:
                parts.append(f"{ref['authors'][0]} & {ref['authors'][1]}")
            else:
                parts.append(f"{ref['authors'][0]} et al.")

        # Year
        if ref.get("year"):
            parts.append(f"({ref['year']})")

        # Title
        if ref.get("title"):
            parts.append(ref["title"] + ".")

        # Journal
        if ref.get("journal"):
            journal_part = ref["journal"]
            if ref.get("volume"):
                journal_part += f", {ref['volume']}"
            if ref.get("pages"):
                journal_part += f", {ref['pages']}"
            parts.append(journal_part + ".")

        # DOI
        if ref.get("doi"):
            parts.append(f"https://doi.org/{ref['doi']}")

        return " ".join(parts)

    @staticmethod
    def format_bibtex(ref: dict, key: str = None) -> str:
        """Format a reference in BibTeX format."""
        if not key:
            # Generate key from first author and year
            if ref.get("authors"):
                first_author = ref["authors"][0].split(",")[0].split()[-1].lower()
            else:
                first_author = "unknown"
            year = ref.get("year", "0000")
            key = f"{first_author}{year}"

        lines = [f"@article{{{key},"]

        if ref.get("authors"):
            authors = " and ".join(ref["authors"])
            lines.append(f'  author = {{{authors}}},')

        if ref.get("title"):
            lines.append(f'  title = {{{ref["title"]}}},')

        if ref.get("year"):
            lines.append(f'  year = {{{ref["year"]}}},')

        if ref.get("journal"):
            lines.append(f'  journal = {{{ref["journal"]}}},')

        if ref.get("volume"):
            lines.append(f'  volume = {{{ref["volume"]}}},')

        if ref.get("pages"):
            lines.append(f'  pages = {{{ref["pages"]}}},')

        if ref.get("doi"):
            lines.append(f'  doi = {{{ref["doi"]}}},')

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def format_ris(ref: dict) -> str:
        """Format a reference in RIS format."""
        lines = ["TY  - JOUR"]

        for author in ref.get("authors", []):
            lines.append(f"AU  - {author}")

        if ref.get("title"):
            lines.append(f"TI  - {ref['title']}")

        if ref.get("year"):
            lines.append(f"PY  - {ref['year']}")

        if ref.get("journal"):
            lines.append(f"JO  - {ref['journal']}")

        if ref.get("volume"):
            lines.append(f"VL  - {ref['volume']}")

        if ref.get("pages"):
            pages = ref["pages"].split("-")
            if len(pages) >= 1:
                lines.append(f"SP  - {pages[0]}")
            if len(pages) >= 2:
                lines.append(f"EP  - {pages[-1]}")

        if ref.get("doi"):
            lines.append(f"DO  - {ref['doi']}")

        lines.append("ER  - ")
        return "\n".join(lines)
