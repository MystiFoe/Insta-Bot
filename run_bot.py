#!/usr/bin/env python3
"""
Instagram Bot CLI - Main entry point for running bot commands.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from src.config import get_config, ConfigManager
from src.bot import InstagramBot
from src.comment_generator import TemplateCommentGenerator
from src.engagement import EngagementManager


console = Console(legacy_windows=False)


def setup_logging(level_name: str = "INFO", log_to_file: bool = True):
    """
    Setup logging with rich handler and file handlers.

    Args:
        level_name: Logging level name
        log_to_file: Whether to log to files
    """
    level = getattr(logging, level_name.upper(), logging.INFO)

    handlers = [RichHandler(console=console, rich_tracebacks=True)]

    if log_to_file:
        # Ensure log directory exists
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Add file handlers
        from logging.handlers import RotatingFileHandler

        actions_handler = RotatingFileHandler(
            "data/logs/actions.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        actions_handler.setLevel(logging.INFO)

        errors_handler = RotatingFileHandler(
            "data/logs/errors.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        errors_handler.setLevel(logging.ERROR)

        handlers.extend([actions_handler, errors_handler])

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def cmd_login(args):
    """Test login command."""
    console.print("[bold cyan]Testing Instagram Login[/bold cyan]\n")

    try:
        config = get_config(args.config)
        bot = InstagramBot(config, dry_run=args.dry_run)

        console.print(f"[yellow]Logging in as {config.instagram.username}...[/yellow]")

        if bot.login():
            console.print("[green]Login successful![/green]")

            # Test API call
            console.print("\n[yellow]Testing API access...[/yellow]")
            try:
                bot.client.get_timeline_feed()
                console.print("[green]API access working![/green]")
            except Exception as e:
                console.print(f"[red]API test failed: {e}[/red]")

            bot.logout()
            return 0
        else:
            console.print("[red]Login failed![/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_hashtag(args):
    """Engage with a specific hashtag."""
    console.print(f"[bold cyan]Engaging with #{args.hashtag}[/bold cyan]\n")

    try:
        config = get_config(args.config)
        bot = InstagramBot(config, dry_run=args.dry_run)
        comment_gen = TemplateCommentGenerator()
        engagement = EngagementManager(bot, config, comment_gen)

        # Login
        console.print("[yellow]Logging in...[/yellow]")
        if not bot.login():
            console.print("[red]Login failed![/red]")
            return 1

        # Engage with hashtag
        stats = engagement.engage_with_hashtag(
            hashtag=args.hashtag,
            max_posts=args.max,
            like_posts=not args.no_like,
            comment_posts=args.comment
        )

        # Display results
        console.print("\n[bold green]Results:[/bold green]")
        console.print(f"  Posts liked: {stats['posts_liked']}")
        console.print(f"  Posts commented: {stats['posts_commented']}")
        console.print(f"  Posts skipped: {stats['posts_skipped']}")
        console.print(f"  Errors: {stats['errors']}")

        # Session kept alive for reuse
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logging.exception("Command failed")
        return 1


def cmd_campaign(args):
    """Run a campaign."""
    console.print(f"[bold cyan]Running Campaign: {args.name}[/bold cyan]\n")

    try:
        config = get_config(args.config)
        config_manager = ConfigManager(args.config)
        config_manager.load()

        # Get campaign
        campaign = config_manager.get_campaign(args.name)
        if not campaign:
            console.print(f"[red]Campaign '{args.name}' not found![/red]")
            console.print("\nAvailable campaigns:")
            for camp_name in config_manager.list_campaigns():
                console.print(f"  - {camp_name}")
            return 1

        # Initialize components
        bot = InstagramBot(config, dry_run=args.dry_run)
        comment_gen = TemplateCommentGenerator()
        engagement = EngagementManager(bot, config, comment_gen)

        # Login
        console.print("[yellow]Logging in...[/yellow]")
        if not bot.login():
            console.print("[red]Login failed![/red]")
            return 1

        # Run campaign
        campaign_stats = engagement.run_campaign(campaign)

        # Display results
        table = Table(title="Campaign Results", show_header=True, header_style="bold magenta")
        table.add_column("Hashtag", style="cyan")
        table.add_column("Liked", style="green")
        table.add_column("Commented", style="blue")
        table.add_column("Skipped", style="red")

        for hashtag, stats in campaign_stats['hashtags'].items():
            table.add_row(
                f"#{hashtag}",
                str(stats['posts_liked']),
                str(stats['posts_commented']),
                str(stats['posts_skipped'])
            )

        console.print("\n")
        console.print(table)

        console.print(f"\n[bold]Total Likes:[/bold] {campaign_stats['total_likes']}")
        console.print(f"[bold]Total Comments:[/bold] {campaign_stats['total_comments']}")

        # Session kept alive for reuse
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logging.exception("Command failed")
        return 1


def cmd_stats(args):
    """Show bot statistics."""
    console.print("[bold cyan]Bot Statistics[/bold cyan]\n")

    try:
        config = get_config(args.config)
        bot = InstagramBot(config, dry_run=args.dry_run)

        stats = bot.get_stats()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Likes Today", stats['limits']['likes'])
        table.add_row("Comments Today", stats['limits']['comments'])
        table.add_row("Follows Today", stats['limits']['follows'])
        table.add_row("Unfollows Today", stats['limits']['unfollows'])
        table.add_row("Errors", str(stats['errors_count']))

        if stats['last_action_time']:
            table.add_row("Last Action", stats['last_action_time'])

        if stats['last_reset_date']:
            table.add_row("Last Reset", stats['last_reset_date'])

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_reset(args):
    """Reset daily statistics."""
    console.print("[bold yellow]Resetting daily statistics...[/bold yellow]\n")

    try:
        config = get_config(args.config)
        bot = InstagramBot(config, dry_run=args.dry_run)

        if args.confirm or args.dry_run:
            bot.reset_daily_stats()
            console.print("[green]Statistics reset successfully![/green]")
            return 0
        else:
            console.print("[red]Please use --confirm flag to reset statistics[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cmd_test(args):
    """Run tests."""
    console.print("[bold cyan]Running Bot Tests[/bold cyan]\n")

    try:
        # Import test module
        from test_bot import run_tests
        return run_tests()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Instagram Bot - Automated engagement tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_bot.py login                          # Test login
  python run_bot.py hashtag fitness --max 10       # Engage with hashtag
  python run_bot.py campaign fitness_campaign      # Run campaign
  python run_bot.py stats                          # Show statistics
  python run_bot.py reset --confirm                # Reset daily counters

For more information, see README.md
        """
    )

    parser.add_argument(
        '--config',
        default='config/settings.yaml',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - no actual actions performed'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Login command
    login_parser = subparsers.add_parser('login', help='Test Instagram login')

    # Hashtag command
    hashtag_parser = subparsers.add_parser('hashtag', help='Engage with hashtag')
    hashtag_parser.add_argument('hashtag', help='Hashtag to target (without #)')
    hashtag_parser.add_argument('--max', type=int, default=10, help='Max posts to engage with')
    hashtag_parser.add_argument('--no-like', action='store_true', help='Don\'t like posts')
    hashtag_parser.add_argument('--comment', action='store_true', help='Comment on posts')

    # Campaign command
    campaign_parser = subparsers.add_parser('campaign', help='Run campaign')
    campaign_parser.add_argument('name', help='Campaign name')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset daily statistics')
    reset_parser.add_argument('--confirm', action='store_true', help='Confirm reset')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Show warning banner
    if not args.dry_run and args.command not in ['stats', 'test']:
        console.print("\n[bold red]WARNING[/bold red]")
        console.print("[yellow]This bot performs automated actions on Instagram.[/yellow]")
        console.print("[yellow]Using automation may violate Instagram's Terms of Service.[/yellow]")
        console.print("[yellow]Your account could be banned or restricted.[/yellow]")
        console.print("[yellow]USE AT YOUR OWN RISK![/yellow]\n")

    # Execute command
    if args.command == 'login':
        return cmd_login(args)
    elif args.command == 'hashtag':
        return cmd_hashtag(args)
    elif args.command == 'campaign':
        return cmd_campaign(args)
    elif args.command == 'stats':
        return cmd_stats(args)
    elif args.command == 'reset':
        return cmd_reset(args)
    elif args.command == 'test':
        return cmd_test(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[red]Stopped by user (Ctrl+C)[/red]")
        sys.exit(130)
