"""
Bot controller for thread-safe GUI operations.
"""

import threading
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .bot import InstagramBot
from .config import get_config, ConfigManager, BotConfig
from .comment_generator import create_comment_generator, DEFAULT_AI_PROMPT, AICommentGenerator
from .engagement import EngagementManager


logger = logging.getLogger(__name__)


class BotState(Enum):
    """Bot operation states."""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class BotStatus:
    """Current bot status."""
    state: BotState = BotState.IDLE
    current_action: str = ""
    current_hashtag: str = ""
    progress: int = 0
    total: int = 0
    error_message: str = ""


class BotController:
    """
    Thread-safe controller for bot operations.
    Provides callbacks for GUI updates.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize bot controller.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config: Optional[BotConfig] = None
        self.config_manager: Optional[ConfigManager] = None
        self.bot: Optional[InstagramBot] = None
        self.engagement: Optional[EngagementManager] = None

        self.status = BotStatus()
        self._stop_flag = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._logged_in = False

        # Callbacks for GUI updates
        self._on_status_change: Optional[Callable[[BotStatus], None]] = None
        self._on_action: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_stats_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_log: Optional[Callable[[str], None]] = None
        self._on_challenge_code: Optional[Callable[[], str]] = None

    def initialize(self) -> bool:
        """
        Initialize bot components.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = get_config(self.config_path)
            self.config_manager = ConfigManager(self.config_path)
            self.config_manager.load()

            self.bot = InstagramBot(self.config, dry_run=False, challenge_code_handler=self._handle_challenge_code, stop_flag=self._stop_flag)
            comment_gen = create_comment_generator()
            self.engagement = EngagementManager(self.bot, self.config, comment_gen)

            self._log("Bot initialized successfully")
            return True

        except Exception as e:
            self._log(f"Failed to initialize bot: {e}")
            self.status.state = BotState.ERROR
            self.status.error_message = str(e)
            return False

    def login(self) -> bool:
        """
        Login to Instagram.

        Returns:
            True if successful, False otherwise
        """
        if not self.bot:
            self._log("Bot not initialized")
            return False

        try:
            self._log("Logging in...")
            if self.bot.login():
                self._log("Login successful")
                self._logged_in = True
                return True
            else:
                self._log("Login failed")
                self._logged_in = False
                return False
        except Exception as e:
            self._log(f"Login error: {e}")
            self._logged_in = False
            return False

    def start_hashtag_engagement(
        self,
        hashtag: str,
        max_posts: int = 10,
        like_posts: bool = True,
        comment_posts: bool = False
    ) -> None:
        """
        Start hashtag engagement in a background thread.

        Args:
            hashtag: Hashtag to engage with
            max_posts: Maximum posts to process
            like_posts: Whether to like posts
            comment_posts: Whether to comment on posts
        """
        if self.status.state == BotState.RUNNING:
            self._log("Bot is already running")
            return

        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run_hashtag_engagement,
            args=(hashtag, max_posts, like_posts, comment_posts),
            daemon=True
        )
        self._thread.start()

    def start_campaign(self, campaign_name: str, like_override: bool = None, comment_override: bool = None) -> None:
        """
        Start a campaign in a background thread.

        Args:
            campaign_name: Name of the campaign to run
            like_override: Override campaign's like setting with GUI value
            comment_override: Override campaign's comment setting with GUI value
        """
        if self.status.state == BotState.RUNNING:
            self._log("Bot is already running")
            return

        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run_campaign,
            args=(campaign_name, like_override, comment_override),
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the current operation."""
        if self.status.state != BotState.RUNNING:
            return

        self._log("Stopping bot...")
        self.status.state = BotState.STOPPING
        self._stop_flag.set()
        self._notify_status_change()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current bot statistics.

        Returns:
            Dictionary with stats
        """
        if not self.bot:
            return {}
        return self.bot.get_stats()

    def get_action_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent action history.

        Args:
            limit: Maximum actions to return

        Returns:
            List of recent actions
        """
        if not self.engagement:
            return []
        return self.engagement.get_action_history(limit)

    def get_campaigns(self) -> List[str]:
        """
        Get list of available campaign names.

        Returns:
            List of campaign names
        """
        if not self.config_manager:
            return []
        return self.config_manager.list_campaigns()

    def get_username(self) -> str:
        """
        Get the configured Instagram username.

        Returns:
            Username string
        """
        if self.config:
            return self.config.instagram.username
        return ""

    def is_logged_in(self) -> bool:
        """
        Check if bot is logged in with a valid session.

        Returns:
            True if logged in with valid session
        """
        if not self.bot:
            return False
        # Check if we have a valid session by checking if session file exists
        # and if we've successfully logged in during this session
        return hasattr(self, '_logged_in') and self._logged_in

    def set_ai_prompt(self, prompt: str) -> None:
        """Set a custom AI system prompt for comment generation."""
        if self.engagement and isinstance(self.engagement.comment_generator, AICommentGenerator):
            self.engagement.comment_generator.set_system_prompt(prompt)
            self._log("AI comment prompt updated")

    def get_ai_prompt(self) -> str:
        """Get the current AI system prompt."""
        if self.engagement and isinstance(self.engagement.comment_generator, AICommentGenerator):
            return self.engagement.comment_generator.system_prompt
        return DEFAULT_AI_PROMPT

    def reset_stats(self) -> None:
        """Reset daily statistics."""
        if self.bot:
            self.bot.reset_daily_stats()
            self._log("Statistics reset")
            self._notify_stats_update()

    # Callback setters
    def set_on_status_change(self, callback: Callable[[BotStatus], None]) -> None:
        """Set callback for status changes."""
        self._on_status_change = callback

    def set_on_action(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for new actions."""
        self._on_action = callback

    def set_on_stats_update(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for stats updates."""
        self._on_stats_update = callback

    def set_on_log(self, callback: Callable[[str], None]) -> None:
        """Set callback for log messages."""
        self._on_log = callback

    def set_on_challenge_code(self, callback: Callable[[], str]) -> None:
        """Set callback for challenge code input (returns code string from GUI)."""
        self._on_challenge_code = callback

    def _handle_challenge_code(self, username, choice) -> str:
        """Handle challenge code request from instagrapi."""
        self._log(f"Verification code required for @{username} (sent via {choice.name})")
        if self._on_challenge_code:
            code = self._on_challenge_code()
            if code:
                self._log(f"Verification code entered")
                return code
        self._log("No verification code provided")
        return ""

    # Private methods
    def _run_hashtag_engagement(
        self,
        hashtag: str,
        max_posts: int,
        like_posts: bool,
        comment_posts: bool
    ) -> None:
        """Run hashtag engagement (called in thread)."""
        try:
            self.status.state = BotState.RUNNING
            self.status.current_hashtag = hashtag
            self.status.current_action = f"Engaging with #{hashtag}"
            self.status.progress = 0
            self.status.total = max_posts
            self._notify_status_change()

            # Login if needed
            if not self.is_logged_in():
                if not self.login():
                    self.status.state = BotState.ERROR
                    self.status.error_message = "Login failed"
                    self._notify_status_change()
                    return

            self._log(f"Starting engagement with #{hashtag}")

            # Get posts
            medias = self.bot.get_hashtag_posts(hashtag, max_posts)

            if not medias:
                self._log(f"No posts found for #{hashtag}")
                self.status.state = BotState.IDLE
                self._notify_status_change()
                return

            self.status.total = len(medias)
            self._notify_status_change()

            # Process posts
            for i, media in enumerate(medias):
                if self._stop_flag.is_set():
                    self._log("Stopped by user")
                    break

                self.status.progress = i + 1
                self.status.current_action = f"Processing post {i+1}/{len(medias)} by @{media.user.username}"
                self._notify_status_change()

                # Engage with post
                result = self.engagement.engage_with_post(
                    media,
                    like_post=like_posts,
                    comment_post=comment_posts,
                    hashtag=hashtag
                )

                if result.get('liked'):
                    action = {
                        'timestamp': self._get_timestamp(),
                        'action': 'like',
                        'username': media.user.username,
                        'media_id': str(media.pk)
                    }
                    self._notify_action(action)

                if result.get('commented'):
                    action = {
                        'timestamp': self._get_timestamp(),
                        'action': 'comment',
                        'username': media.user.username,
                        'media_id': str(media.pk),
                        'comment': result.get('comment_text', '')
                    }
                    self._notify_action(action)

                self._notify_stats_update()

            self._log(f"Engagement complete for #{hashtag}")

        except Exception as e:
            self._log(f"Error: {e}")
            self.status.state = BotState.ERROR
            self.status.error_message = str(e)

        finally:
            if self.status.state != BotState.ERROR:
                self.status.state = BotState.IDLE
            self.status.current_action = ""
            self.status.current_hashtag = ""
            self._notify_status_change()

    def _run_campaign(self, campaign_name: str, like_override: bool = None, comment_override: bool = None) -> None:
        """Run campaign (called in thread)."""
        try:
            self.status.state = BotState.RUNNING
            self.status.current_action = f"Running campaign: {campaign_name}"
            self._notify_status_change()

            campaign = self.config_manager.get_campaign(campaign_name)
            if not campaign:
                self._log(f"Campaign '{campaign_name}' not found")
                self.status.state = BotState.IDLE
                self._notify_status_change()
                return

            # Login if needed
            if not self.is_logged_in():
                if not self.login():
                    self.status.state = BotState.ERROR
                    self.status.error_message = "Login failed"
                    self._notify_status_change()
                    return

            self._log(f"Starting campaign: {campaign_name}")

            for hashtag in campaign.hashtags:
                if self._stop_flag.is_set():
                    self._log("Campaign stopped by user")
                    break

                self.status.current_hashtag = hashtag
                self.status.current_action = f"Engaging with #{hashtag}"
                self._notify_status_change()

                # Get and process posts for this hashtag
                medias = self.bot.get_hashtag_posts(hashtag, campaign.max_posts_per_hashtag)

                if medias:
                    self.status.total = len(medias)
                    self.status.progress = 0

                    for i, media in enumerate(medias):
                        if self._stop_flag.is_set():
                            break

                        self.status.progress = i + 1
                        self._notify_status_change()

                        # Use GUI overrides if provided, otherwise use campaign settings
                        should_like = like_override if like_override is not None else campaign.like_posts
                        should_comment = comment_override if comment_override is not None else campaign.comment_posts

                        result = self.engagement.engage_with_post(
                            media,
                            like_post=should_like,
                            comment_post=should_comment,
                            hashtag=hashtag
                        )

                        if result.get('liked'):
                            action = {
                                'timestamp': self._get_timestamp(),
                                'action': 'like',
                                'username': media.user.username,
                                'media_id': str(media.pk)
                            }
                            self._notify_action(action)

                        if result.get('commented'):
                            action = {
                                'timestamp': self._get_timestamp(),
                                'action': 'comment',
                                'username': media.user.username,
                                'media_id': str(media.pk),
                                'comment': result.get('comment_text', '')
                            }
                            self._notify_action(action)

                        self._notify_stats_update()

            self._log(f"Campaign '{campaign_name}' complete")

        except Exception as e:
            self._log(f"Campaign error: {e}")
            self.status.state = BotState.ERROR
            self.status.error_message = str(e)

        finally:
            if self.status.state != BotState.ERROR:
                self.status.state = BotState.IDLE
            self.status.current_action = ""
            self.status.current_hashtag = ""
            self._notify_status_change()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _log(self, message: str) -> None:
        """Log a message and notify callback."""
        logger.info(message)
        if self._on_log:
            self._on_log(message)

    def _notify_status_change(self) -> None:
        """Notify status change callback."""
        if self._on_status_change:
            self._on_status_change(self.status)

    def _notify_action(self, action: Dict[str, Any]) -> None:
        """Notify action callback."""
        if self._on_action:
            self._on_action(action)

    def _notify_stats_update(self) -> None:
        """Notify stats update callback."""
        if self._on_stats_update:
            stats = self.get_stats()
            self._on_stats_update(stats)
