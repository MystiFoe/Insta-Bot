"""
Comment generation module with AI (OpenAI) primary and template fallback.
"""

import json
import os
import random
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

from openai import OpenAI


logger = logging.getLogger(__name__)


DEFAULT_AI_PROMPT = (
    "You are an Instagram user leaving a genuine comment on a post. "
    "Rules:\n"
    "- Write ONLY the comment text, nothing else\n"
    "- Keep it short: 3-8 words max\n"
    "- Sound casual and authentic like a real person\n"
    "- Use 1 emoji maximum\n"
    "- Never use hashtags in comments\n"
    "- Never repeat yourself - vary your style\n"
    "- Don't be overly generic - reference the content\n"
    "- Don't use quotes around the comment\n"
    "- Always write comments in English regardless of the post language"
)


class AICommentGenerator:
    """Generates contextual comments using OpenAI API."""

    def __init__(self, api_key: str, fallback: 'TemplateCommentGenerator'):
        self.client = OpenAI(api_key=api_key)
        self.fallback = fallback
        self.used_comments: Set[str] = set()
        self.system_prompt: str = DEFAULT_AI_PROMPT
        logger.info("AI comment generator initialized")

    def set_system_prompt(self, prompt: str) -> None:
        """Set a custom system prompt for AI comment generation."""
        self.system_prompt = prompt
        logger.info("Custom AI prompt set")

    def get_comment(
        self,
        category: Optional[str] = None,
        caption: str = "",
        hashtags: List[str] = None,
        avoid_recent: bool = True
    ) -> str:
        try:
            context_parts = []
            if category:
                context_parts.append(f"Topic: {category}")
            if caption:
                # Truncate long captions
                short_caption = caption[:200] if len(caption) > 200 else caption
                context_parts.append(f"Caption: {short_caption}")
            if hashtags:
                context_parts.append(f"Hashtags: {', '.join(hashtags[:5])}")

            context = "\n".join(context_parts) if context_parts else "A general Instagram post"

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Write a comment for this Instagram post:\n{context}"
                    }
                ],
                max_tokens=30,
                temperature=0.9,
            )

            comment = response.choices[0].message.content.strip().strip('"\'')

            # Avoid repeating AI comments too
            if avoid_recent and comment in self.used_comments:
                # Try once more with higher temperature
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an Instagram user. Write a very short, unique comment "
                                "(3-8 words, 1 emoji max). Just the comment text, nothing else."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Comment on this post:\n{context}"
                        }
                    ],
                    max_tokens=30,
                    temperature=1.0,
                )
                comment = response.choices[0].message.content.strip().strip('"\'')

            self.used_comments.add(comment)
            if len(self.used_comments) > 100:
                self.used_comments = set(list(self.used_comments)[-50:])

            logger.info(f"AI generated comment: {comment}")
            return comment

        except Exception as e:
            logger.warning(f"AI comment generation failed: {e}, using template fallback")
            return self.fallback.get_comment(
                category=category, caption=caption,
                hashtags=hashtags, avoid_recent=avoid_recent
            )


def create_comment_generator(templates_path: str = "config/templates.json") -> 'TemplateCommentGenerator':
    """Factory: creates AICommentGenerator (primary) with TemplateCommentGenerator (fallback).
    Returns an object with get_comment() method."""
    fallback = TemplateCommentGenerator(templates_path)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        logger.info("OpenAI API key found - using AI comment generation (templates as fallback)")
        return AICommentGenerator(api_key, fallback)
    else:
        logger.info("No OpenAI API key - using template comments only")
        return fallback


class TemplateCommentGenerator:
    """Generates comments from templates with anti-spam features."""

    def __init__(self, templates_path: str = "config/templates.json"):
        """
        Initialize comment generator.

        Args:
            templates_path: Path to JSON file containing comment templates
        """
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, List[str]] = {}
        self.used_comments: Set[str] = set()
        self.load_templates()

    def load_templates(self) -> None:
        """
        Load comment templates from JSON file.

        Raises:
            FileNotFoundError: If templates file doesn't exist
            json.JSONDecodeError: If templates file is invalid JSON
        """
        if not self.templates_path.exists():
            raise FileNotFoundError(f"Templates file not found: {self.templates_path}")

        with open(self.templates_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)

        logger.info(f"Loaded {len(self.templates)} template categories")
        for category, comments in self.templates.items():
            logger.debug(f"Category '{category}': {len(comments)} templates")

    def detect_category(self, caption: str, hashtags: List[str]) -> str:
        """
        Detect content category from caption and hashtags.

        Args:
            caption: Post caption text
            hashtags: List of hashtags in the post

        Returns:
            Category name or 'default' if no match
        """
        caption_lower = caption.lower() if caption else ""
        hashtags_lower = [h.lower().replace('#', '') for h in hashtags]

        # Check hashtags first (more reliable)
        for hashtag in hashtags_lower:
            if hashtag in self.templates:
                logger.debug(f"Detected category '{hashtag}' from hashtag")
                return hashtag

        # Check caption for category keywords
        for category in self.templates.keys():
            if category != 'default' and category in caption_lower:
                logger.debug(f"Detected category '{category}' from caption")
                return category

        logger.debug("No specific category detected, using 'default'")
        return 'default'

    def get_comment(
        self,
        category: Optional[str] = None,
        caption: str = "",
        hashtags: List[str] = None,
        avoid_recent: bool = True
    ) -> str:
        """
        Get a random comment from templates.

        Args:
            category: Specific category to use (auto-detected if None)
            caption: Post caption for category detection
            hashtags: List of hashtags for category detection
            avoid_recent: Avoid recently used comments

        Returns:
            Random comment text
        """
        if hashtags is None:
            hashtags = []

        # Auto-detect category if not provided
        if category is None:
            category = self.detect_category(caption, hashtags)

        # Fallback to default if category not found
        if category not in self.templates:
            logger.warning(f"Category '{category}' not found, using 'default'")
            category = 'default'

        # Get available comments
        available_comments = self.templates[category].copy()

        # Filter out recently used comments if requested
        if avoid_recent and self.used_comments:
            filtered_comments = [c for c in available_comments if c not in self.used_comments]
            if filtered_comments:
                available_comments = filtered_comments
            else:
                # If all comments were used, reset the used set
                logger.info("All comments used, resetting used comments tracker")
                self.used_comments.clear()

        # Select random comment
        comment = random.choice(available_comments)

        # Track usage
        self.used_comments.add(comment)

        # Reset tracker if it gets too large (prevent memory issues)
        if len(self.used_comments) > 100:
            logger.debug("Used comments tracker exceeded 100, clearing oldest half")
            # Keep only the last 50 used comments
            self.used_comments = set(list(self.used_comments)[-50:])

        logger.debug(f"Generated comment from category '{category}': {comment}")
        return comment

    def get_random_comment(self) -> str:
        """
        Get a completely random comment from all categories.

        Returns:
            Random comment text
        """
        all_comments = []
        for comments in self.templates.values():
            all_comments.extend(comments)

        return random.choice(all_comments)

    def add_template(self, category: str, comment: str) -> None:
        """
        Add a new comment template to a category.

        Args:
            category: Category name
            comment: Comment text to add
        """
        if category not in self.templates:
            self.templates[category] = []

        if comment not in self.templates[category]:
            self.templates[category].append(comment)
            logger.info(f"Added new template to category '{category}': {comment}")
        else:
            logger.warning(f"Template already exists in category '{category}': {comment}")

    def save_templates(self) -> None:
        """Save current templates to file."""
        with open(self.templates_path, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved templates to {self.templates_path}")

    def list_categories(self) -> List[str]:
        """
        Get list of all available categories.

        Returns:
            List of category names
        """
        return list(self.templates.keys())

    def get_category_count(self, category: str) -> int:
        """
        Get number of templates in a category.

        Args:
            category: Category name

        Returns:
            Number of templates in category (0 if not found)
        """
        return len(self.templates.get(category, []))

    def validate_templates(self) -> Dict[str, List[str]]:
        """
        Validate templates for common issues.

        Returns:
            Dictionary of warnings by category
        """
        warnings = {}

        for category, comments in self.templates.items():
            category_warnings = []

            # Check for duplicates
            if len(comments) != len(set(comments)):
                category_warnings.append("Contains duplicate comments")

            # Check for very short comments
            short_comments = [c for c in comments if len(c) < 3]
            if short_comments:
                category_warnings.append(f"Contains {len(short_comments)} very short comments")

            # Check for minimum variety
            if len(comments) < 5:
                category_warnings.append(f"Only {len(comments)} templates (recommend at least 5)")

            if category_warnings:
                warnings[category] = category_warnings

        return warnings
