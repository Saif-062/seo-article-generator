"""Mock LLM provider for testing without API keys."""

from __future__ import annotations

import json
from typing import Any

from app.providers.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider that returns realistic fixture data.

    Use this for:
    - Testing without consuming API credits
    - Running the demo without API keys
    - Deterministic test scenarios
    """

    def __init__(self):
        self._model = "mock-llm"

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        """Generate mock response based on prompt content."""
        prompt_lower = prompt.lower()

        # Detect what kind of content is being requested
        # Note: Order matters - more specific checks first
        if "seo metadata" in prompt_lower or "title_tag" in prompt_lower:
            return self._generate_metadata_response(prompt)
        elif "internal link" in prompt_lower:
            return self._generate_internal_links_response(prompt)
        elif "external" in prompt_lower and "source" in prompt_lower:
            return self._generate_external_refs_response(prompt)
        elif "serp data" in prompt_lower or "search results for the topic" in prompt_lower:
            return self._generate_theme_response(prompt)
        elif "revise" in prompt_lower or "fix these seo" in prompt_lower:
            return self._generate_revision_response(prompt)
        elif "outline" in prompt_lower and "create" in prompt_lower:
            return self._generate_outline_response(prompt)
        elif "write" in prompt_lower and "article" in prompt_lower:
            return self._generate_article_response(prompt)
        else:
            return "Mock response for testing purposes."

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Generate structured mock JSON response."""
        response = await self.generate(prompt, system_prompt, temperature, max_tokens, True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Return a basic structure if parsing fails
            return {"content": response, "mock": True}

    def _generate_theme_response(self, prompt: str) -> str:
        """Generate mock theme analysis."""
        return json.dumps({
            "search_intent": "informational",
            "primary_themes": [
                "Tool comparison and reviews",
                "Best practices and tips",
                "Getting started guides",
                "Cost and pricing analysis",
                "Integration and workflow optimization",
            ],
            "common_sections": [
                "Introduction",
                "What are [topic]",
                "Benefits of [topic]",
                "Top [topic] options",
                "How to choose",
                "Best practices",
                "Common mistakes",
                "FAQ",
                "Conclusion",
            ],
            "content_gaps": [
                "Specific use case examples",
                "ROI calculations",
                "Implementation timelines",
            ],
            "suggested_angles": [
                "Focus on practical implementation",
                "Include real-world case studies",
                "Provide actionable checklists",
            ],
            "faq_questions": [
                "What is the best option for beginners?",
                "How much does it typically cost?",
                "What are the most common mistakes to avoid?",
                "How long does it take to see results?",
            ],
        })

    def _generate_outline_response(self, prompt: str) -> str:
        """Generate mock article outline."""
        return json.dumps({
            "title": "The Complete Guide to Productivity Tools for Remote Teams",
            "sections": [
                {
                    "heading": "Introduction: Why Remote Teams Need Specialized Tools",
                    "level": 2,
                    "target_words": 150,
                    "key_points": [
                        "The rise of remote work",
                        "Unique challenges of distributed teams",
                        "How the right tools make a difference",
                    ],
                },
                {
                    "heading": "Understanding Different Types of Productivity Tools",
                    "level": 2,
                    "target_words": 200,
                    "key_points": [
                        "Communication tools",
                        "Project management tools",
                        "Time tracking tools",
                        "Collaboration tools",
                    ],
                },
                {
                    "heading": "Top 10 Productivity Tools for Remote Teams",
                    "level": 2,
                    "target_words": 400,
                    "subsections": [
                        {"heading": "Communication: Slack vs Teams", "level": 3, "target_words": 100},
                        {"heading": "Project Management: Asana vs Monday", "level": 3, "target_words": 100},
                        {"heading": "Documentation: Notion vs Confluence", "level": 3, "target_words": 100},
                    ],
                },
                {
                    "heading": "How to Choose the Right Tools for Your Team",
                    "level": 2,
                    "target_words": 200,
                    "key_points": [
                        "Assess your team's needs",
                        "Consider integration requirements",
                        "Evaluate pricing and scalability",
                    ],
                },
                {
                    "heading": "Best Practices for Tool Implementation",
                    "level": 2,
                    "target_words": 200,
                    "key_points": [
                        "Start with core tools",
                        "Train your team properly",
                        "Monitor adoption and adjust",
                    ],
                },
                {
                    "heading": "Common Mistakes to Avoid",
                    "level": 2,
                    "target_words": 150,
                    "key_points": [
                        "Tool overload",
                        "Lack of standardization",
                        "Ignoring team feedback",
                    ],
                },
                {
                    "heading": "Frequently Asked Questions",
                    "level": 2,
                    "target_words": 150,
                },
                {
                    "heading": "Conclusion",
                    "level": 2,
                    "target_words": 100,
                },
            ],
            "faq_questions": [
                "What is the best productivity tool for small remote teams?",
                "How much should a company budget for productivity tools?",
                "Can free tools be effective for remote team productivity?",
                "How do I get my team to actually use new tools?",
            ],
            "total_target_words": 1500,
        })

    def _generate_article_response(self, prompt: str) -> str:
        """Generate mock article content."""
        return """# The Complete Guide to Productivity Tools for Remote Teams

Remote work has transformed how teams collaborate, and the right productivity tools can make the difference between a thriving distributed team and one that struggles with communication gaps and inefficiency.

## Introduction: Why Remote Teams Need Specialized Tools

The shift to remote work has created unique challenges that traditional office tools weren't designed to address. Remote teams need solutions that bridge physical distances, maintain team cohesion, and ensure everyone stays aligned on goals and deadlines.

When teams work across different time zones and locations, the importance of having robust, integrated productivity tools becomes paramount. These tools serve as the digital workspace where collaboration happens, decisions are made, and projects move forward.

## Understanding Different Types of Productivity Tools

Before diving into specific recommendations, it's essential to understand the categories of tools available:

### Communication Tools
Real-time messaging, video conferencing, and async communication platforms form the backbone of remote team communication. Tools like Slack, Microsoft Teams, and Zoom have become essential for daily operations.

### Project Management Tools
These platforms help teams organize work, track progress, and meet deadlines. Popular options include Asana, Monday.com, Trello, and Jira.

### Documentation and Knowledge Management
Centralized documentation tools ensure team knowledge is captured and accessible. Notion, Confluence, and Coda excel in this category.

### Time Tracking and Focus Tools
For teams that need to track billable hours or want to improve productivity, tools like Toggl, Clockify, and Focus@Will can be valuable additions.

## Top 10 Productivity Tools for Remote Teams

### 1. Slack - Best for Team Communication
Slack remains the gold standard for team messaging. Its channel-based organization, extensive integrations, and powerful search make it ideal for remote teams of any size.

**Key Features:**
- Organized channels for different projects and topics
- Thread replies to keep conversations focused
- Over 2,000 app integrations
- Huddles for quick voice conversations

### 2. Asana - Best for Project Management
Asana offers the perfect balance of simplicity and power. Its multiple view options (list, board, timeline, calendar) accommodate different working styles.

**Key Features:**
- Flexible project views
- Automation rules to reduce manual work
- Goals tracking for alignment
- Workload management to prevent burnout

### 3. Notion - Best for Documentation
Notion has revolutionized team documentation with its flexible, block-based approach. It can replace multiple tools, serving as a wiki, project tracker, and database.

**Key Features:**
- Customizable templates
- Powerful database functionality
- Team spaces and permissions
- API for custom integrations

### 4. Zoom - Best for Video Conferencing
Despite increased competition, Zoom remains the most reliable option for video meetings. Its stability and feature set make it the preferred choice for important meetings.

### 5. Loom - Best for Async Video
Loom enables teams to communicate complex ideas through quick video recordings, reducing the need for meetings while maintaining personal connection.

## How to Choose the Right Tools for Your Team

Selecting the right productivity stack requires careful consideration of several factors:

**Assess Your Team's Needs**
Start by identifying pain points in your current workflow. Are communication delays causing problems? Is project visibility lacking? Understanding your challenges helps prioritize solutions.

**Consider Integration Requirements**
The best productivity suite is one where tools work together seamlessly. Check that prospective tools integrate with your existing stack.

**Evaluate Total Cost of Ownership**
Free tiers are great for starting out, but consider long-term costs as your team scales. Factor in training time and potential productivity gains.

## Best Practices for Tool Implementation

Successfully adopting new tools requires more than just signing up:

1. **Start Small**: Begin with one or two core tools and master them before adding more
2. **Create Standards**: Document how each tool should be used to ensure consistency
3. **Train Thoroughly**: Invest time in proper onboarding so team members feel confident
4. **Gather Feedback**: Regularly check in with the team about what's working and what isn't
5. **Iterate**: Be willing to adjust your toolkit as needs evolve

## Common Mistakes to Avoid

**Tool Overload**
Adding too many tools creates confusion and context-switching overhead. Aim for a minimal, integrated toolkit.

**Lack of Clear Guidelines**
Without documented standards, teams create inconsistent workflows that reduce the tools' effectiveness.

**Ignoring Team Preferences**
Forcing tools on unwilling team members leads to low adoption. Include the team in tool selection decisions.

## Frequently Asked Questions

**What is the best productivity tool for small remote teams?**
For small teams, Notion combined with Slack provides an excellent foundation. Both offer generous free tiers and can scale as you grow.

**How much should a company budget for productivity tools?**
Budget $20-50 per user per month for a comprehensive stack. This typically includes communication, project management, and documentation tools.

**Can free tools be effective for remote team productivity?**
Many tools offer robust free tiers that work well for small teams. Slack, Asana, Notion, and Trello all have free options that provide substantial value.

**How do I get my team to actually use new tools?**
Success requires clear communication about why the change is happening, thorough training, and patience during the transition period. Leading by example also helps.

## Conclusion

Building an effective remote productivity stack is essential for distributed teams to thrive. By thoughtfully selecting tools that address your specific challenges, implementing them with clear guidelines, and remaining open to iteration, your team can achieve the collaboration and efficiency that makes remote work successful.

Start with the fundamentals—communication and project management—then expand your toolkit as needs become clear. Remember that the best tools are the ones your team will actually use consistently."""

    def _generate_revision_response(self, prompt: str) -> str:
        """Generate mock revision (same as original with minor improvements)."""
        # For mock purposes, return the same article
        return self._generate_article_response(prompt)

    def _generate_metadata_response(self, prompt: str) -> str:
        """Generate mock SEO metadata."""
        return json.dumps({
            "title_tag": "Best Productivity Tools for Remote Teams in 2025 | Complete Guide",
            "meta_description": "Discover the top productivity tools that help remote teams collaborate effectively. Compare features, pricing, and find the perfect fit for your distributed team.",
            "slug": "best-productivity-tools-remote-teams",
            "primary_keyword": "productivity tools for remote teams",
            "secondary_keywords": ["remote work tools", "team collaboration software", "project management"],
        })

    def _generate_internal_links_response(self, prompt: str) -> str:
        """Generate mock internal link suggestions."""
        return json.dumps([
            {
                "anchor_text": "project management software",
                "target_topic": "project management guide",
                "placement_hint": "tools comparison section",
            },
            {
                "anchor_text": "remote team communication",
                "target_topic": "communication best practices",
                "placement_hint": "communication tools section",
            },
            {
                "anchor_text": "team collaboration",
                "target_topic": "collaboration strategies guide",
                "placement_hint": "introduction section",
            },
            {
                "anchor_text": "video conferencing",
                "target_topic": "video meeting tips",
                "placement_hint": "Zoom section",
            },
        ])

    def _generate_external_refs_response(self, prompt: str) -> str:
        """Generate mock external reference suggestions."""
        return json.dumps([
            {
                "url": "https://hbr.org/remote-work-study",
                "source_name": "Harvard Business Review",
                "why_authoritative": "Leading business publication with research-backed insights on workplace productivity",
                "placement_hint": "introduction section",
            },
            {
                "url": "https://www.gartner.com/remote-work-report",
                "source_name": "Gartner Research",
                "why_authoritative": "Industry-leading research firm with comprehensive workplace technology analysis",
                "placement_hint": "statistics section",
            },
            {
                "url": "https://buffer.com/state-of-remote-work",
                "source_name": "Buffer State of Remote Work",
                "why_authoritative": "Annual survey with data from thousands of remote workers worldwide",
                "placement_hint": "best practices section",
            },
        ])
