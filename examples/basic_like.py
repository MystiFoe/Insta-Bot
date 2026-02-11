"""
Example 1: Basic Like Bot
Simple example that logs in and likes posts from a hashtag.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.bot import InstagramBot


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
    logger.info("BASIC LIKE BOT EXAMPLE")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()

        # Initialize bot
        logger.info("Initializing bot...")
        bot = InstagramBot(config, dry_run=False)

        # Login
        logger.info("Logging in...")
        if not bot.login():
            logger.error("Login failed!")
            return

        # Define target hashtag
        hashtag = "fitness"
        max_posts = 10

        logger.info(f"Fetching {max_posts} posts from #{hashtag}...")
        medias = bot.get_hashtag_posts(hashtag, max_posts)

        if not medias:
            logger.warning("No posts found!")
            return

        logger.info(f"Found {len(medias)} posts. Starting to like them...")

        # Like each post
        liked_count = 0
        for i, media in enumerate(medias, 1):
            if not bot.check_daily_limits('likes'):
                logger.warning("Daily like limit reached!")
                break

            logger.info(f"Post {i}/{len(medias)}: @{media.user.username}")

            if bot.like_post(str(media.pk)):
                liked_count += 1
                logger.info(f"✓ Liked post {i}")
            else:
                logger.warning(f"✗ Failed to like post {i}")

        # Show statistics
        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Posts liked: {liked_count}/{len(medias)}")

        stats = bot.get_stats()
        logger.info(f"Today's likes: {stats['limits']['likes']}")
        logger.info(f"Today's comments: {stats['limits']['comments']}")

        # Logout
        logger.info("Logging out...")
        bot.logout()
        logger.info("Done!")

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
