"""
Example 2: Auto Comment Bot
Likes and comments on posts using template-based comments.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.bot import InstagramBot
from src.comment_generator import TemplateCommentGenerator


def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("AUTO COMMENT BOT EXAMPLE")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()

        # Initialize bot
        logger.info("Initializing bot...")
        bot = InstagramBot(config, dry_run=False)

        # Initialize comment generator
        logger.info("Loading comment templates...")
        comment_gen = TemplateCommentGenerator()

        # Login
        logger.info("Logging in...")
        if not bot.login():
            logger.error("Login failed!")
            return

        # Define target hashtag
        hashtag = "gym"
        max_posts = 5  # Fewer posts since we're commenting

        logger.info(f"Fetching {max_posts} posts from #{hashtag}...")
        medias = bot.get_hashtag_posts(hashtag, max_posts)

        if not medias:
            logger.warning("No posts found!")
            return

        logger.info(f"Found {len(medias)} posts. Starting engagement...")

        # Engage with each post
        liked_count = 0
        commented_count = 0

        for i, media in enumerate(medias, 1):
            if not bot.check_daily_limits():
                logger.warning("Daily limits reached!")
                break

            logger.info(f"\nPost {i}/{len(medias)}: @{media.user.username}")

            # Like the post
            if bot.like_post(str(media.pk)):
                liked_count += 1
                logger.info(f"✓ Liked post {i}")

                # Generate and post comment
                caption = getattr(media, 'caption_text', '')
                comment_text = comment_gen.get_comment(
                    category=hashtag,
                    caption=caption
                )

                logger.info(f"Generated comment: {comment_text}")

                if bot.comment_post(str(media.pk), comment_text):
                    commented_count += 1
                    logger.info(f"✓ Commented on post {i}")
                else:
                    logger.warning(f"✗ Failed to comment on post {i}")
            else:
                logger.warning(f"✗ Failed to like post {i}")

        # Show statistics
        logger.info("\n" + "=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Posts liked: {liked_count}/{len(medias)}")
        logger.info(f"Posts commented: {commented_count}/{len(medias)}")

        stats = bot.get_stats()
        logger.info(f"Today's likes: {stats['limits']['likes']}")
        logger.info(f"Today's comments: {stats['limits']['comments']}")

        # Logout
        logger.info("\nLogging out...")
        bot.logout()
        logger.info("Done!")

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
