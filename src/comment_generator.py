"""
Template-based comment generation module.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging


logger = logging.getLogger(__name__)


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
