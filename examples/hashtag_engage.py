"""
Example 3: Full Hashtag Engagement Bot
Complete bot with multi-hashtag support, rate limiting, and safety features.
"""

import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.bot import InstagramBot
from src.comment_generator import TemplateCommentGenerator
from src.engagement import EngagementManager


console = Console()


def setup_logging(level=logging.INFO):
    """Setup rich logging."""
    logging.basicConfig(
        level=level,
        format='%(message)s',
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


def display_config(config):
    """Display configuration in a nice table."""
    table = Table(title="Bot Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Username", config.instagram.username)
    table.add_row("Max Likes/Day", str(config.limits.max_likes_per_day))
    table.add_row("Max Comments/Day", str(config.limits.max_comments_per_day))
    table.add_row("Delay Range", f"{config.limits.min_delay_seconds}-{config.limits.max_delay_seconds}s")
    table.add_row("Active Hours", f"{config.limits.active_hours_start}:00 - {config.limits.active_hours_end}:00")
    table.add_row("Skip Verified", "Yes" if config.safety.skip_verified else "No")
    table.add_row("Follower Range", f"{config.safety.min_followers} - {config.safety.max_followers}")

    console.print(table)


def display_results(campaign_stats):
    """Display campaign results."""
    table = Table(title="Campaign Results", show_header=True, header_style="bold magenta")
    table.add_column("Hashtag", style="cyan")
    table.add_column("Processed", style="yellow")
    table.add_column("Liked", style="green")
    table.add_column("Commented", style="blue")
    table.add_column("Skipped", style="red")

    for hashtag, stats in campaign_stats['hashtags'].items():
        table.add_row(
            f"#{hashtag}",
            str(stats['posts_processed']),
            str(stats['posts_liked']),
            str(stats['posts_commented']),
            str(stats['posts_skipped'])
        )

    # Add total row
    table.add_row(
        "[bold]TOTAL[/bold]",
        "[bold]-[/bold]",
        f"[bold]{campaign_stats['total_likes']}[/bold]",
        f"[bold]{campaign_stats['total_comments']}[/bold]",
        f"[bold]{campaign_stats['total_skipped']}[/bold]",
        style="bold"
    )

    console.print(table)


def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    console.print("\n[bold cyan]=" * 30)
    console.print("[bold cyan]FULL HASHTAG ENGAGEMENT BOT")
    console.print("[bold cyan]=" * 30 + "\n")

    try:
        # Load configuration
        console.print("[yellow]Loading configuration...[/yellow]")
        config = get_config()
        display_config(config)

        # Initialize components
        console.print("\n[yellow]Initializing bot components...[/yellow]")
        bot = InstagramBot(config, dry_run=False)
        comment_gen = TemplateCommentGenerator()
        engagement = EngagementManager(bot, config, comment_gen)

        # Display available campaigns
        console.print(f"\n[cyan]Available campaigns:[/cyan]")
        for i, campaign in enumerate(config.campaigns, 1):
            console.print(
                f"  {i}. [bold]{campaign.name}[/bold] - "
                f"{len(campaign.hashtags)} hashtags, "
                f"max {campaign.max_posts_per_hashtag} posts/hashtag"
            )

        # Select campaign (using first one for this example)
        selected_campaign = config.campaigns[0]
        console.print(f"\n[green]Selected campaign: {selected_campaign.name}[/green]")

        # Show safety warning
        console.print("\n[bold red]⚠️  SAFETY WARNING ⚠️[/bold red]")
        console.print("[yellow]This bot will perform actions on your Instagram account.[/yellow]")
        console.print("[yellow]Using automation may violate Instagram's Terms of Service.[/yellow]")
        console.print("[yellow]Use at your own risk![/yellow]\n")

        response = input("Type 'YES' to continue: ")
        if response != "YES":
            console.print("[red]Aborted by user[/red]")
            return

        # Login
        console.print("\n[yellow]Logging in...[/yellow]")
        if not bot.login():
            console.print("[red]Login failed![/red]")
            return

        console.print("[green]✓ Logged in successfully[/green]")

        # Show current stats
        stats = bot.get_stats()
        console.print(f"\n[cyan]Current Daily Stats:[/cyan]")
        console.print(f"  Likes: {stats['limits']['likes']}")
        console.print(f"  Comments: {stats['limits']['comments']}")

        # Check if within active hours
        if not bot.is_active_hours():
            console.print(
                f"\n[red]Outside active hours "
                f"({config.limits.active_hours_start}:00 - {config.limits.active_hours_end}:00)[/red]"
            )
            console.print("[yellow]Continuing anyway for demo purposes...[/yellow]")

        # Run campaign
        console.print(f"\n[bold green]Starting campaign: {selected_campaign.name}[/bold green]")
        console.print(f"[cyan]Hashtags: {', '.join(['#' + h for h in selected_campaign.hashtags])}[/cyan]\n")

        campaign_stats = engagement.run_campaign(selected_campaign)

        # Display results
        console.print(f"\n[bold green]Campaign Complete![/bold green]\n")
        display_results(campaign_stats)

        # Show final stats
        final_stats = bot.get_stats()
        console.print(f"\n[cyan]Final Daily Stats:[/cyan]")
        console.print(f"  Likes: {final_stats['limits']['likes']}")
        console.print(f"  Comments: {final_stats['limits']['comments']}")
        console.print(f"  Errors: {final_stats['errors_count']}")

        # Logout
        console.print("\n[yellow]Logging out...[/yellow]")
        bot.logout()
        console.print("[green]✓ Done![/green]\n")

    except KeyboardInterrupt:
        console.print("\n[red]Stopped by user (Ctrl+C)[/red]")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
