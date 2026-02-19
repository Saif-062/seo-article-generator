"""Mock SERP provider for testing without API keys."""

from app.models.serp import PeopleAlsoAsk, SerpData, SerpResult
from app.providers.serp.base import BaseSerpProvider


class MockSerpProvider(BaseSerpProvider):
    """
    Mock SERP provider that returns realistic fixture data.

    Use this for:
    - Testing without consuming API credits
    - Running the demo without API keys
    - Deterministic test scenarios
    """

    @property
    def name(self) -> str:
        return "mock"

    async def search(self, query: str, num_results: int = 10) -> SerpData:
        """Return mock SERP data based on query."""
        # Generate realistic mock data
        results = self._generate_results(query, num_results)
        paa = self._generate_paa(query)
        related = self._generate_related(query)

        return SerpData(
            query=query,
            results=results,
            people_also_ask=paa,
            related_searches=related,
        )

    def _generate_results(self, query: str, num_results: int) -> list[SerpResult]:
        """Generate mock search results."""
        # Create topic-aware mock results
        topic_words = query.lower().split()

        templates = [
            {
                "title": f"The Ultimate Guide to {query.title()} in 2025",
                "snippet": f"Discover everything you need to know about {query}. Our comprehensive guide covers best practices, tools, and expert tips for success.",
                "domain": "expertguide.com",
            },
            {
                "title": f"15 Best {query.title()} - Expert Picks & Reviews",
                "snippet": f"We tested and reviewed the top {query} to help you choose the right one. Compare features, pricing, and user ratings.",
                "domain": "techreviews.com",
            },
            {
                "title": f"{query.title()}: Complete Beginner's Guide [2025]",
                "snippet": f"New to {query}? This beginner-friendly guide walks you through everything from basics to advanced strategies.",
                "domain": "learnhub.io",
            },
            {
                "title": f"How to Master {query.title()} - Step by Step",
                "snippet": f"Follow our proven step-by-step process to master {query}. Includes templates, examples, and common mistakes to avoid.",
                "domain": "skillmaster.com",
            },
            {
                "title": f"{query.title()} vs Alternatives: Detailed Comparison",
                "snippet": f"Comparing {query} with popular alternatives. See features side-by-side and find the best option for your needs.",
                "domain": "comparetools.net",
            },
            {
                "title": f"Why {query.title()} Matters for Your Business",
                "snippet": f"Learn how {query} can transform your business operations. Real case studies and ROI data included.",
                "domain": "businessinsider.com",
            },
            {
                "title": f"{query.title()} Tips from Industry Experts",
                "snippet": f"Industry leaders share their top tips for {query}. Exclusive insights you won't find anywhere else.",
                "domain": "industrynews.com",
            },
            {
                "title": f"Common {query.title()} Mistakes and How to Avoid Them",
                "snippet": f"Don't make these costly {query} mistakes. Learn what experts do differently and save time and money.",
                "domain": "protips.io",
            },
            {
                "title": f"The Future of {query.title()}: Trends to Watch",
                "snippet": f"Stay ahead of the curve with emerging {query} trends. What's changing in 2025 and beyond.",
                "domain": "futurereport.com",
            },
            {
                "title": f"{query.title()} Case Studies: Real Success Stories",
                "snippet": f"See how companies achieved success with {query}. Detailed case studies with metrics and strategies.",
                "domain": "casestudyhub.com",
            },
        ]

        results = []
        for i, template in enumerate(templates[:num_results]):
            results.append(
                SerpResult(
                    rank=i + 1,
                    url=f"https://{template['domain']}/{query.lower().replace(' ', '-')}",
                    title=template["title"],
                    snippet=template["snippet"],
                )
            )

        return results

    def _generate_paa(self, query: str) -> list[PeopleAlsoAsk]:
        """Generate mock People Also Ask questions."""
        question_templates = [
            f"What is the best {query}?",
            f"How do I get started with {query}?",
            f"Is {query} worth it?",
            f"What are the benefits of {query}?",
            f"How much does {query} cost?",
            f"What are common {query} mistakes?",
        ]

        return [
            PeopleAlsoAsk(
                question=q,
                snippet=f"According to experts, {q.lower().replace('?', '')} depends on several factors including your specific needs and goals.",
            )
            for q in question_templates[:4]
        ]

    def _generate_related(self, query: str) -> list[str]:
        """Generate mock related searches."""
        return [
            f"{query} for beginners",
            f"best {query} 2025",
            f"{query} vs alternatives",
            f"{query} reviews",
            f"how to use {query}",
            f"{query} pricing",
        ]
