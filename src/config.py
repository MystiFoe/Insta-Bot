"""
Configuration management module for Instagram bot.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class InstagramConfig(BaseModel):
    """Instagram account configuration."""
    username: str = ""
    password: str = ""


class CampaignConfig(BaseModel):
    """Campaign configuration."""
    name: str
    hashtags: List[str]
    max_posts_per_hashtag: int = 10
    like_posts: bool = True
    comment_posts: bool = False


class LimitsConfig(BaseModel):
    """Rate limiting configuration."""
    max_likes_per_day: int = 50
    max_comments_per_day: int = 20
    max_follows_per_day: int = 30
    max_unfollows_per_day: int = 30
    min_delay_seconds: int = 30
    max_delay_seconds: int = 60
    active_hours_start: int = 8
    active_hours_end: int = 23


class SafetyConfig(BaseModel):
    """Safety and filtering configuration."""
    skip_verified: bool = True
    skip_business: bool = False
    min_followers: int = 100
    max_followers: int = 50000
    error_threshold: int = 3
    cooldown_minutes: int = 60
    session_file: str = "data/sessions/session.json"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    console: bool = True
    file: bool = True
    actions_log: str = "data/logs/actions.log"
    errors_log: str = "data/logs/errors.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


class BotConfig(BaseModel):
    """Main bot configuration."""
    instagram: InstagramConfig
    campaigns: List[CampaignConfig]
    limits: LimitsConfig
    safety: SafetyConfig
    logging: LoggingConfig


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: str = "config/settings.yaml", env_path: str = ".env"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to YAML configuration file
            env_path: Path to .env file
        """
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)
        self.config: Optional[BotConfig] = None

    def load(self) -> BotConfig:
        """
        Load configuration from YAML and environment variables.

        Returns:
            BotConfig: Validated configuration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        # Load environment variables
        if self.env_path.exists():
            load_dotenv(self.env_path)

        # Load YAML configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Override with environment variables
        config_data['instagram']['username'] = os.getenv('INSTAGRAM_USERNAME', '')
        config_data['instagram']['password'] = os.getenv('INSTAGRAM_PASSWORD', '')

        # Override log level if set in env
        if os.getenv('LOG_LEVEL'):
            config_data['logging']['level'] = os.getenv('LOG_LEVEL')

        # Validate and create config object
        self.config = BotConfig(**config_data)

        # Validate credentials
        if not self.config.instagram.username or not self.config.instagram.password:
            raise ValueError(
                "Instagram credentials not found. "
                "Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env file"
            )

        return self.config

    def get_campaign(self, campaign_name: str) -> Optional[CampaignConfig]:
        """
        Get specific campaign configuration by name.

        Args:
            campaign_name: Name of the campaign

        Returns:
            CampaignConfig or None if not found
        """
        if not self.config:
            self.load()

        for campaign in self.config.campaigns:
            if campaign.name == campaign_name:
                return campaign

        return None

    def list_campaigns(self) -> List[str]:
        """
        List all available campaign names.

        Returns:
            List of campaign names
        """
        if not self.config:
            self.load()

        return [campaign.name for campaign in self.config.campaigns]


def get_config(config_path: str = "config/settings.yaml") -> BotConfig:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        BotConfig: Loaded configuration
    """
    manager = ConfigManager(config_path)
    return manager.load()
