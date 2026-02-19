"""SERP (Search Engine Results Page) data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SerpResult(BaseModel):
    """A single search result from SERP."""

    rank: int = Field(..., ge=1, le=100, description="Position in search results")
    url: str = Field(..., description="URL of the result")
    title: str = Field(..., description="Title of the result")
    snippet: str = Field(default="", description="Snippet/description text")


class PeopleAlsoAsk(BaseModel):
    """A 'People Also Ask' question from SERP."""

    question: str
    snippet: str = ""


class SerpData(BaseModel):
    """Complete SERP data for a query."""

    query: str = Field(..., description="The search query used")
    results: list[SerpResult] = Field(default_factory=list, description="Top search results")
    people_also_ask: list[PeopleAlsoAsk] = Field(
        default_factory=list, description="Related questions"
    )
    related_searches: list[str] = Field(default_factory=list, description="Related search queries")

    @property
    def top_10(self) -> list[SerpResult]:
        """Get top 10 results."""
        return self.results[:10]


class PageSignals(BaseModel):
    """SEO signals extracted from a competitor page."""

    url: str
    title: str = ""
    meta_description: str = ""
    h1: str = ""
    h2_headings: list[str] = Field(default_factory=list)
    h3_headings: list[str] = Field(default_factory=list)
    word_count: int = 0
    fetch_success: bool = True
    error: str | None = None
