"""DOI lookup service using CrossRef API."""
import httpx
from typing import Optional


class DOILookupService:
    """Service for looking up paper metadata via DOI using CrossRef API."""

    BASE_URL = "https://api.crossref.org/works"

    @staticmethod
    async def lookup_doi(doi: str) -> Optional[dict]:
        """
        Look up paper metadata by DOI.

        Args:
            doi: The DOI string (e.g., "10.1234/example")

        Returns:
            Dictionary with paper metadata or None if not found
        """
        # Clean DOI
        doi = doi.strip()
        if doi.startswith("https://doi.org/"):
            doi = doi[16:]
        elif doi.startswith("http://doi.org/"):
            doi = doi[15:]
        elif doi.startswith("doi:"):
            doi = doi[4:]

        url = f"{DOILookupService.BASE_URL}/{doi}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "ScholarChat/1.0 (Academic Research Assistant)"}
                )

                if response.status_code != 200:
                    return None

                data = response.json()
                message = data.get("message", {})

                # Extract relevant fields
                result = {
                    "doi": doi,
                    "title": "",
                    "authors": [],
                    "year": None,
                    "journal": "",
                    "volume": "",
                    "issue": "",
                    "pages": "",
                    "publisher": "",
                    "abstract": "",
                    "url": "",
                    "citations_count": 0,
                }

                # Title
                titles = message.get("title", [])
                if titles:
                    result["title"] = titles[0]

                # Authors
                for author in message.get("author", []):
                    name_parts = []
                    if author.get("given"):
                        name_parts.append(author["given"])
                    if author.get("family"):
                        name_parts.append(author["family"])
                    if name_parts:
                        result["authors"].append(" ".join(name_parts))

                # Year
                published = message.get("published-print") or message.get("published-online") or message.get("created")
                if published and "date-parts" in published:
                    date_parts = published["date-parts"][0]
                    if date_parts:
                        result["year"] = date_parts[0]

                # Journal
                container = message.get("container-title", [])
                if container:
                    result["journal"] = container[0]

                # Volume & Issue
                result["volume"] = message.get("volume", "")
                result["issue"] = message.get("issue", "")

                # Pages
                result["pages"] = message.get("page", "")

                # Publisher
                result["publisher"] = message.get("publisher", "")

                # Abstract
                result["abstract"] = message.get("abstract", "")

                # URL
                result["url"] = message.get("URL", f"https://doi.org/{doi}")

                # Citation count
                result["citations_count"] = message.get("is-referenced-by-count", 0)

                return result

        except Exception as e:
            print(f"DOI lookup error: {e}")
            return None

    @staticmethod
    async def search_by_title(title: str, limit: int = 5) -> list[dict]:
        """
        Search for papers by title.

        Args:
            title: Paper title to search for
            limit: Maximum number of results

        Returns:
            List of paper metadata dictionaries
        """
        url = f"{DOILookupService.BASE_URL}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    params={
                        "query.title": title,
                        "rows": limit,
                        "select": "DOI,title,author,published-print,container-title"
                    },
                    headers={"User-Agent": "ScholarChat/1.0 (Academic Research Assistant)"}
                )

                if response.status_code != 200:
                    return []

                data = response.json()
                items = data.get("message", {}).get("items", [])

                results = []
                for item in items:
                    result = {
                        "doi": item.get("DOI", ""),
                        "title": item.get("title", [""])[0] if item.get("title") else "",
                        "authors": [],
                        "year": None,
                    }

                    # Authors
                    for author in item.get("author", []):
                        name_parts = []
                        if author.get("given"):
                            name_parts.append(author["given"])
                        if author.get("family"):
                            name_parts.append(author["family"])
                        if name_parts:
                            result["authors"].append(" ".join(name_parts))

                    # Year
                    published = item.get("published-print")
                    if published and "date-parts" in published:
                        date_parts = published["date-parts"][0]
                        if date_parts:
                            result["year"] = date_parts[0]

                    results.append(result)

                return results

        except Exception as e:
            print(f"Title search error: {e}")
            return []
