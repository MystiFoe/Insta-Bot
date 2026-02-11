"""
Test suite for Instagram bot.
Tests configuration, comment generation, and bot components without making actual API calls.
"""

import os
import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.config import get_config, ConfigManager
from src.bot import InstagramBot
from src.comment_generator import TemplateCommentGenerator


console = Console()
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_test(self, name: str, passed: bool, message: str = ""):
        """Add test result."""
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def display(self):
        """Display test results."""
        table = Table(title="Test Results", show_header=True, header_style="bold magenta")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Message", style="yellow")

        for test in self.tests:
            status = "[green]✓ PASS[/green]" if test['passed'] else "[red]✗ FAIL[/red]"
            table.add_row(test['name'], status, test['message'])

        console.print("\n")
        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {self.passed + self.failed} tests")
        console.print(f"[green]Passed:[/green] {self.passed}")
        console.print(f"[red]Failed:[/red] {self.failed}")

        return self.failed == 0


def test_configuration(results: TestResults):
    """Test configuration loading."""
    console.print("\n[bold]Testing Configuration...[/bold]")

    # Test 1: Load config file
    try:
        config = get_config()
        results.add_test(
            "Load configuration file",
            True,
            f"Loaded {len(config.campaigns)} campaigns"
        )
    except Exception as e:
        results.add_test("Load configuration file", False, str(e))
        return

    # Test 2: Validate credentials
    has_credentials = bool(config.instagram.username and config.instagram.password)
    results.add_test(
        "Instagram credentials",
        has_credentials,
        "Found in .env" if has_credentials else "Missing in .env"
    )

    # Test 3: Validate campaigns
    has_campaigns = len(config.campaigns) > 0
    results.add_test(
        "Campaign configuration",
        has_campaigns,
        f"Found {len(config.campaigns)} campaigns" if has_campaigns else "No campaigns"
    )

    # Test 4: Check rate limits
    valid_limits = (
        config.limits.max_likes_per_day > 0 and
        config.limits.max_comments_per_day > 0
    )
    results.add_test(
        "Rate limits configured",
        valid_limits,
        f"Likes: {config.limits.max_likes_per_day}, Comments: {config.limits.max_comments_per_day}"
    )

    # Test 5: Validate active hours
    valid_hours = (
        0 <= config.limits.active_hours_start < 24 and
        0 <= config.limits.active_hours_end <= 24
    )
    results.add_test(
        "Active hours valid",
        valid_hours,
        f"{config.limits.active_hours_start}:00 - {config.limits.active_hours_end}:00"
    )


def test_comment_generator(results: TestResults):
    """Test comment generation."""
    console.print("\n[bold]Testing Comment Generator...[/bold]")

    # Test 1: Load templates
    try:
        gen = TemplateCommentGenerator()
        results.add_test(
            "Load comment templates",
            True,
            f"Loaded {len(gen.templates)} categories"
        )
    except Exception as e:
        results.add_test("Load comment templates", False, str(e))
        return

    # Test 2: Category detection
    try:
        category = gen.detect_category("Great workout today!", ["fitness", "gym"])
        is_fitness = category in ['fitness', 'gym']
        results.add_test(
            "Category detection",
            is_fitness,
            f"Detected: {category}"
        )
    except Exception as e:
        results.add_test("Category detection", False, str(e))

    # Test 3: Generate comment
    try:
        comment = gen.get_comment(category='fitness')
        is_valid = len(comment) > 0
        results.add_test(
            "Generate comment",
            is_valid,
            f"Generated: {comment}"
        )
    except Exception as e:
        results.add_test("Generate comment", False, str(e))

    # Test 4: Validate templates
    try:
        warnings = gen.validate_templates()
        has_issues = len(warnings) > 0
        results.add_test(
            "Template validation",
            not has_issues,
            f"{len(warnings)} categories with warnings" if has_issues else "All templates valid"
        )
    except Exception as e:
        results.add_test("Template validation", False, str(e))

    # Test 5: Test avoid duplicates
    try:
        comments = set()
        for _ in range(10):
            comment = gen.get_comment(category='fitness', avoid_recent=True)
            comments.add(comment)

        variety = len(comments) > 1
        results.add_test(
            "Comment variety",
            variety,
            f"{len(comments)} unique comments from 10 generations"
        )
    except Exception as e:
        results.add_test("Comment variety", False, str(e))


def test_bot_initialization(results: TestResults):
    """Test bot initialization (without login)."""
    console.print("\n[bold]Testing Bot Initialization...[/bold]")

    # Test 1: Initialize bot
    try:
        config = get_config()
        bot = InstagramBot(config, dry_run=True)
        results.add_test(
            "Initialize bot",
            True,
            "Bot created in dry-run mode"
        )
    except Exception as e:
        results.add_test("Initialize bot", False, str(e))
        return

    # Test 2: Check session file path
    try:
        session_path = Path(config.safety.session_file)
        parent_exists = session_path.parent.exists()
        results.add_test(
            "Session directory",
            parent_exists,
            f"Path: {session_path.parent}" if parent_exists else "Directory missing"
        )
    except Exception as e:
        results.add_test("Session directory", False, str(e))

    # Test 3: Check stats file
    try:
        stats_file = Path(config.safety.session_file).parent / "stats.json"
        stats_dir_exists = stats_file.parent.exists()
        results.add_test(
            "Stats directory",
            stats_dir_exists,
            f"Path: {stats_file.parent}"
        )
    except Exception as e:
        results.add_test("Stats directory", False, str(e))

    # Test 4: Test rate limiting check
    try:
        can_act = bot.check_daily_limits('likes')
        results.add_test(
            "Rate limit check",
            True,
            f"Can perform likes: {can_act}"
        )
    except Exception as e:
        results.add_test("Rate limit check", False, str(e))

    # Test 5: Test active hours check
    try:
        is_active = bot.is_active_hours()
        results.add_test(
            "Active hours check",
            True,
            f"Currently active: {is_active}"
        )
    except Exception as e:
        results.add_test("Active hours check", False, str(e))


def test_file_structure(results: TestResults):
    """Test file and directory structure."""
    console.print("\n[bold]Testing File Structure...[/bold]")

    required_files = [
        "config/settings.yaml",
        "config/templates.json",
        ".env.example",
        "requirements.txt",
        "src/__init__.py",
        "src/bot.py",
        "src/config.py",
        "src/engagement.py",
        "src/comment_generator.py",
    ]

    required_dirs = [
        "data/sessions",
        "data/logs",
        "examples",
    ]

    # Check files
    for file_path in required_files:
        exists = Path(file_path).exists()
        results.add_test(
            f"File: {file_path}",
            exists,
            "Found" if exists else "Missing"
        )

    # Check directories
    for dir_path in required_dirs:
        exists = Path(dir_path).is_dir()
        results.add_test(
            f"Directory: {dir_path}",
            exists,
            "Found" if exists else "Missing"
        )


def test_dry_run(results: TestResults):
    """Test dry-run mode."""
    console.print("\n[bold]Testing Dry-Run Mode...[/bold]")

    try:
        config = get_config()
        bot = InstagramBot(config, dry_run=True)

        # Test dry-run like
        result = bot.like_post("test_media_id_12345")
        results.add_test(
            "Dry-run like post",
            result,
            "Simulated successfully"
        )

        # Test dry-run comment
        result = bot.comment_post("test_media_id_12345", "Test comment")
        results.add_test(
            "Dry-run comment post",
            result,
            "Simulated successfully"
        )

        # Verify no stats were incremented
        stats = bot.get_stats()
        no_actions = stats['likes_today'] == 0 and stats['comments_today'] == 0
        results.add_test(
            "Dry-run doesn't affect stats",
            no_actions,
            "Stats remain at 0" if no_actions else "Stats were modified!"
        )

    except Exception as e:
        results.add_test("Dry-run mode", False, str(e))


def run_tests():
    """Run all tests."""
    console.print("[bold cyan]=" * 30)
    console.print("[bold cyan]INSTAGRAM BOT TEST SUITE")
    console.print("[bold cyan]=" * 30)

    results = TestResults()

    # Run test suites
    test_file_structure(results)
    test_configuration(results)
    test_comment_generator(results)
    test_bot_initialization(results)
    test_dry_run(results)

    # Display results
    success = results.display()

    if success:
        console.print("\n[bold green]✓ All tests passed![/bold green]")
        return 0
    else:
        console.print("\n[bold red]✗ Some tests failed![/bold red]")
        return 1


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.WARNING)
    return run_tests()


if __name__ == "__main__":
    sys.exit(main())
