"""
Core Instagram bot implementation using Instagrapi.
"""

import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes,
)

from .config import BotConfig


logger = logging.getLogger(__name__)


@dataclass
class ActionStats:
    """Statistics for bot actions."""
    likes_today: int = 0
    comments_today: int = 0
    follows_today: int = 0
    unfollows_today: int = 0
    errors_count: int = 0
    last_action_time: Optional[str] = None
    last_reset_date: Optional[str] = None


class InstagramBot:
    """Main Instagram bot class with session management and rate limiting."""

    def __init__(self, config: BotConfig, dry_run: bool = False, challenge_code_handler=None):
        """
        Initialize Instagram bot.

        Args:
            config: Bot configuration object
            dry_run: If True, don't perform actual actions (testing mode)
            challenge_code_handler: Callback function(username, choice) that returns verification code
        """
        self.config = config
        self.dry_run = dry_run
        self.client = Client()
        self.stats = ActionStats()
        self.session_file = Path(config.safety.session_file)
        self.stats_file = Path(config.safety.session_file).parent / "stats.json"

        # Set updated device settings (default instagrapi version is outdated)
        self.client.set_device({
            "app_version": "357.0.0.25.107",
            "android_version": 34,
            "android_release": "14",
            "dpi": "480dpi",
            "resolution": "1080x2400",
            "manufacturer": "Samsung",
            "device": "dm1q",
            "model": "SM-S911B",
            "cpu": "qcom",
            "version_code": "596729402",
        })
        self.client.set_user_agent()

        # Set challenge code handler for verification
        if challenge_code_handler:
            self.client.challenge_code_handler = challenge_code_handler

        # Initialize client settings
        self.client.delay_range = [
            config.limits.min_delay_seconds,
            config.limits.max_delay_seconds
        ]

        # Load existing stats
        self._load_stats()

        # Reset daily counters if needed
        self._check_daily_reset()

        if dry_run:
            logger.warning("DRY RUN MODE: No actual actions will be performed")

    def login(self) -> bool:
        """
        Login to Instagram with session persistence.

        Returns:
            True if login successful, False otherwise
        """
        try:
            # Try to load existing session
            if self.session_file.exists():
                logger.info("Loading existing session...")
                self.client.load_settings(self.session_file)

                try:
                    # Verify session is still valid
                    self.client.get_timeline_feed()
                    logger.info("Session is valid, logged in successfully")
                    return True
                except LoginRequired:
                    logger.warning("Session expired, need to login again")

            # Perform fresh login
            logger.info(f"Logging in as {self.config.instagram.username}...")
            self.client.login(
                self.config.instagram.username,
                self.config.instagram.password
            )

            # Save session
            self.save_session()
            logger.info("Login successful, session saved")
            return True

        except ChallengeRequired as e:
            logger.warning(f"Challenge required: {e}")
            try:
                logger.info("Attempting to resolve challenge...")
                self.client.challenge_resolve(self.client.last_json)
                # If challenge resolved, try login flow again
                self.client.login_flow()
                self.save_session()
                logger.info("Challenge resolved, login successful")
                return True
            except Exception as ce:
                logger.error(f"Challenge resolution failed: {ce}")
                return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return False

    def logout(self) -> None:
        """Logout and clear session."""
        try:
            logger.info("Logging out...")
            self.client.logout()
            logger.info("Logged out successfully")
        except Exception as e:
            logger.warning(f"Logout error (may be already logged out): {e}")

    def save_session(self) -> None:
        """Save current session to file."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(self.session_file)
            logger.debug(f"Session saved to {self.session_file}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def get_hashtag_posts(self, hashtag: str, amount: int = 10) -> List[Any]:
        """
        Get recent posts for a hashtag.

        Args:
            hashtag: Hashtag to search (without #)
            amount: Number of posts to retrieve

        Returns:
            List of media objects
        """
        try:
            logger.info(f"Fetching {amount} posts for #{hashtag}...")
            medias = self.client.hashtag_medias_recent(hashtag, amount)
            logger.info(f"Found {len(medias)} posts for #{hashtag}")
            return medias

        except Exception as e:
            logger.error(f"Failed to fetch hashtag posts: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return []

    def like_post(self, media_id: str) -> bool:
        """
        Like a post.

        Args:
            media_id: Media ID to like

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would like post {media_id}")
            return True

        if not self.check_daily_limits('likes'):
            logger.warning("Daily like limit reached")
            return False

        try:
            self.human_delay()
            self.client.media_like(media_id)
            self.stats.likes_today += 1
            self.stats.last_action_time = datetime.now().isoformat()
            self._save_stats()
            logger.info(f"Liked post {media_id} (Total today: {self.stats.likes_today})")
            return True

        except FeedbackRequired as e:
            logger.error(f"Action blocked by Instagram: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return False

        except PleaseWaitFewMinutes as e:
            logger.error(f"Rate limited by Instagram: {e}")
            logger.info(f"Waiting {self.config.safety.cooldown_minutes} minutes...")
            self.stats.errors_count += 1
            self._save_stats()
            time.sleep(self.config.safety.cooldown_minutes * 60)
            return False

        except Exception as e:
            logger.error(f"Failed to like post: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return False

    def comment_post(self, media_id: str, text: str) -> bool:
        """
        Comment on a post.

        Args:
            media_id: Media ID to comment on
            text: Comment text

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would comment on post {media_id}: {text}")
            return True

        if not self.check_daily_limits('comments'):
            logger.warning("Daily comment limit reached")
            return False

        try:
            self.human_delay()
            self.client.media_comment(media_id, text)
            self.stats.comments_today += 1
            self.stats.last_action_time = datetime.now().isoformat()
            self._save_stats()
            logger.info(f"Commented on post {media_id}: {text} (Total today: {self.stats.comments_today})")
            return True

        except FeedbackRequired as e:
            logger.error(f"Action blocked by Instagram: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return False

        except PleaseWaitFewMinutes as e:
            logger.error(f"Rate limited by Instagram: {e}")
            logger.info(f"Waiting {self.config.safety.cooldown_minutes} minutes...")
            self.stats.errors_count += 1
            self._save_stats()
            time.sleep(self.config.safety.cooldown_minutes * 60)
            return False

        except Exception as e:
            logger.error(f"Failed to comment on post: {e}")
            self.stats.errors_count += 1
            self._save_stats()
            return False

    def check_daily_limits(self, action_type: str = None) -> bool:
        """
        Check if daily limits allow more actions.

        Args:
            action_type: Type of action ('likes', 'comments', 'follows', 'unfollows')

        Returns:
            True if action is allowed, False if limit reached
        """
        limits_map = {
            'likes': (self.stats.likes_today, self.config.limits.max_likes_per_day),
            'comments': (self.stats.comments_today, self.config.limits.max_comments_per_day),
            'follows': (self.stats.follows_today, self.config.limits.max_follows_per_day),
            'unfollows': (self.stats.unfollows_today, self.config.limits.max_unfollows_per_day),
        }

        if action_type and action_type in limits_map:
            current, limit = limits_map[action_type]
            return current < limit

        # Check if any limit is reached (for general check)
        return all(current < limit for current, limit in limits_map.values())

    def human_delay(self, min_seconds: Optional[int] = None, max_seconds: Optional[int] = None) -> None:
        """
        Add human-like delay between actions.

        Args:
            min_seconds: Minimum delay (uses config if None)
            max_seconds: Maximum delay (uses config if None)
        """
        if min_seconds is None:
            min_seconds = self.config.limits.min_delay_seconds
        if max_seconds is None:
            max_seconds = self.config.limits.max_delay_seconds

        delay = random.randint(min_seconds, max_seconds)
        logger.debug(f"Waiting {delay} seconds...")
        time.sleep(delay)

    def is_active_hours(self) -> bool:
        """
        Check if current time is within active hours.

        Returns:
            True if within active hours, False otherwise
        """
        current_hour = datetime.now().hour
        start = self.config.limits.active_hours_start
        end = self.config.limits.active_hours_end

        if start <= end:
            return start <= current_hour < end
        else:
            # Handle cases where active hours span midnight
            return current_hour >= start or current_hour < end

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current bot statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            **asdict(self.stats),
            'limits': {
                'likes': f"{self.stats.likes_today}/{self.config.limits.max_likes_per_day}",
                'comments': f"{self.stats.comments_today}/{self.config.limits.max_comments_per_day}",
                'follows': f"{self.stats.follows_today}/{self.config.limits.max_follows_per_day}",
                'unfollows': f"{self.stats.unfollows_today}/{self.config.limits.max_unfollows_per_day}",
            }
        }

    def reset_daily_stats(self) -> None:
        """Reset daily statistics counters."""
        logger.info("Resetting daily statistics...")
        self.stats.likes_today = 0
        self.stats.comments_today = 0
        self.stats.follows_today = 0
        self.stats.unfollows_today = 0
        self.stats.errors_count = 0
        self.stats.last_reset_date = datetime.now().date().isoformat()
        self._save_stats()

    def _check_daily_reset(self) -> None:
        """Check if daily stats need to be reset."""
        if not self.stats.last_reset_date:
            self.reset_daily_stats()
            return

        last_reset = datetime.fromisoformat(self.stats.last_reset_date).date()
        today = datetime.now().date()

        if today > last_reset:
            self.reset_daily_stats()

    def _load_stats(self) -> None:
        """Load statistics from file."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.stats = ActionStats(**data)
                logger.info("Loaded existing statistics")
            except Exception as e:
                logger.warning(f"Failed to load stats: {e}")

    def _save_stats(self) -> None:
        """Save statistics to file."""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(asdict(self.stats), f, indent=2)
            logger.debug("Statistics saved")
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
