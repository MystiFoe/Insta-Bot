"""
Engagement logic for Instagram bot.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .bot import InstagramBot
from .config import BotConfig, CampaignConfig
from .comment_generator import TemplateCommentGenerator


logger = logging.getLogger(__name__)


class EngagementManager:
    """Manages engagement campaigns with filtering and safety checks."""

    def __init__(self, bot: InstagramBot, config: BotConfig, comment_generator: TemplateCommentGenerator):
        """
        Initialize engagement manager.

        Args:
            bot: InstagramBot instance
            config: Bot configuration
            comment_generator: Comment generator instance
        """
        self.bot = bot
        self.config = config
        self.comment_generator = comment_generator
        self.action_history: List[Dict[str, Any]] = []

    def engage_with_hashtag(
        self,
        hashtag: str,
        max_posts: int = 10,
        like_posts: bool = True,
        comment_posts: bool = False
    ) -> Dict[str, int]:
        """
        Engage with posts from a specific hashtag.

        Args:
            hashtag: Hashtag to target (without #)
            max_posts: Maximum number of posts to engage with
            like_posts: Whether to like posts
            comment_posts: Whether to comment on posts

        Returns:
            Dictionary with engagement statistics
        """
        logger.info(f"Starting engagement with #{hashtag} (max: {max_posts} posts)")

        stats = {
            'posts_processed': 0,
            'posts_liked': 0,
            'posts_commented': 0,
            'posts_skipped': 0,
            'errors': 0
        }

        # Check if within active hours
        if not self.bot.is_active_hours():
            logger.warning("Outside active hours, skipping engagement")
            return stats

        # Fetch posts
        medias = self.bot.get_hashtag_posts(hashtag, max_posts)

        if not medias:
            logger.warning(f"No posts found for #{hashtag}")
            return stats

        # Process each post
        for media in medias:
            if not self.bot.check_daily_limits():
                logger.info("Daily limits reached, stopping engagement")
                break

            stats['posts_processed'] += 1

            # Check if post is eligible
            if not self.check_post_eligibility(media):
                stats['posts_skipped'] += 1
                logger.info(f"Skipped post {media.pk} (failed eligibility check)")
                continue

            # Engage with post
            success = self.engage_with_post(
                media,
                like_post=like_posts,
                comment_post=comment_posts,
                hashtag=hashtag
            )

            if success.get('liked'):
                stats['posts_liked'] += 1

            if success.get('commented'):
                stats['posts_commented'] += 1

            if success.get('error'):
                stats['errors'] += 1

                # Check error threshold
                if self.bot.stats.errors_count >= self.config.safety.error_threshold:
                    logger.error(f"Error threshold reached ({self.config.safety.error_threshold}), stopping")
                    break

        logger.info(
            f"Engagement complete for #{hashtag}: "
            f"{stats['posts_liked']} likes, {stats['posts_commented']} comments, "
            f"{stats['posts_skipped']} skipped, {stats['errors']} errors"
        )

        return stats

    def engage_with_post(
        self,
        media: Any,
        like_post: bool = True,
        comment_post: bool = False,
        hashtag: str = ""
    ) -> Dict[str, bool]:
        """
        Engage with a single post.

        Args:
            media: Media object from Instagrapi
            like_post: Whether to like the post
            comment_post: Whether to comment on the post
            hashtag: Source hashtag (for comment generation)

        Returns:
            Dictionary with action results
        """
        result = {'liked': False, 'commented': False, 'comment_text': '', 'error': False}

        media_id = str(media.pk)
        logger.info(f"Engaging with post {media_id} by @{media.user.username}")

        try:
            # Like post
            if like_post:
                if self.bot.like_post(media_id):
                    result['liked'] = True
                    self.track_action('like', media_id, media.user.username)
                else:
                    result['error'] = True

            # Comment on post
            if comment_post and result['liked']:  # Only comment if like was successful
                # Generate appropriate comment
                caption = getattr(media, 'caption_text', '')
                hashtags = self._extract_hashtags(caption)

                # Use source hashtag as category hint
                comment_text = self.comment_generator.get_comment(
                    category=hashtag if hashtag else None,
                    caption=caption,
                    hashtags=hashtags
                )

                if self.bot.comment_post(media_id, comment_text):
                    result['commented'] = True
                    result['comment_text'] = comment_text
                    self.track_action('comment', media_id, media.user.username, comment_text)
                else:
                    result['error'] = True

        except Exception as e:
            logger.error(f"Error engaging with post {media_id}: {e}")
            result['error'] = True

        return result

    def check_post_eligibility(self, media: Any) -> bool:
        """
        Check if a post is eligible for engagement based on safety rules.

        Args:
            media: Media object from Instagrapi

        Returns:
            True if eligible, False otherwise
        """
        try:
            user = media.user

            # Skip if already engaged
            if media.has_liked:
                logger.debug(f"Post {media.pk} already liked")
                return False

            # Skip verified accounts if configured
            if self.config.safety.skip_verified and getattr(user, 'is_verified', False):
                logger.debug(f"Skipping verified account @{user.username}")
                return False

            # Skip business accounts if configured
            if self.config.safety.skip_business and getattr(user, 'is_business', False):
                logger.debug(f"Skipping business account @{user.username}")
                return False

            # Check follower count limits
            follower_count = getattr(user, 'follower_count', 0) or 0

            if follower_count < self.config.safety.min_followers:
                logger.debug(
                    f"Skipping @{user.username} "
                    f"(followers: {follower_count} < {self.config.safety.min_followers})"
                )
                return False

            if follower_count > self.config.safety.max_followers:
                logger.debug(
                    f"Skipping @{user.username} "
                    f"(followers: {follower_count} > {self.config.safety.max_followers})"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking post eligibility: {e}")
            return False

    def run_campaign(self, campaign: CampaignConfig) -> Dict[str, Any]:
        """
        Run a complete engagement campaign.

        Args:
            campaign: Campaign configuration

        Returns:
            Dictionary with campaign statistics
        """
        logger.info(f"Starting campaign: {campaign.name}")
        logger.info(f"Hashtags: {', '.join(campaign.hashtags)}")

        campaign_stats = {
            'campaign_name': campaign.name,
            'start_time': datetime.now().isoformat(),
            'hashtags': {},
            'total_likes': 0,
            'total_comments': 0,
            'total_skipped': 0,
            'total_errors': 0
        }

        for hashtag in campaign.hashtags:
            if not self.bot.check_daily_limits():
                logger.info("Daily limits reached, stopping campaign")
                break

            if not self.bot.is_active_hours():
                logger.info("Outside active hours, pausing campaign")
                break

            # Engage with hashtag
            stats = self.engage_with_hashtag(
                hashtag=hashtag,
                max_posts=campaign.max_posts_per_hashtag,
                like_posts=campaign.like_posts,
                comment_posts=campaign.comment_posts
            )

            campaign_stats['hashtags'][hashtag] = stats
            campaign_stats['total_likes'] += stats['posts_liked']
            campaign_stats['total_comments'] += stats['posts_commented']
            campaign_stats['total_skipped'] += stats['posts_skipped']
            campaign_stats['total_errors'] += stats['errors']

            # Add delay between hashtags
            if hashtag != campaign.hashtags[-1]:  # Not the last hashtag
                logger.info("Waiting before next hashtag...")
                self.bot.human_delay(min_seconds=60, max_seconds=120)

        campaign_stats['end_time'] = datetime.now().isoformat()

        logger.info(
            f"Campaign '{campaign.name}' complete: "
            f"{campaign_stats['total_likes']} likes, "
            f"{campaign_stats['total_comments']} comments, "
            f"{campaign_stats['total_skipped']} skipped"
        )

        return campaign_stats

    def track_action(
        self,
        action_type: str,
        media_id: str,
        username: str,
        comment_text: str = ""
    ) -> None:
        """
        Track an action in history.

        Args:
            action_type: Type of action ('like', 'comment', 'follow', etc.)
            media_id: Media ID
            username: Target username
            comment_text: Comment text if applicable
        """
        action = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type,
            'media_id': media_id,
            'username': username,
            'comment': comment_text
        }

        self.action_history.append(action)

        # Keep only last 1000 actions to prevent memory issues
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]

        logger.debug(f"Tracked {action_type} action on post {media_id} by @{username}")

    def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent action history.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of recent actions
        """
        return self.action_history[-limit:]

    def _extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from text.

        Args:
            text: Text containing hashtags

        Returns:
            List of hashtags (without #)
        """
        if not text:
            return []

        import re
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags
