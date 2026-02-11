# Instagram Bot with Instagrapi

A production-ready Instagram automation bot built with [Instagrapi](https://github.com/subzeroid/instagrapi) for educational purposes. Features include hashtag engagement, template-based commenting, rate limiting, session persistence, and comprehensive safety measures.

---

## ⚠️ IMPORTANT LEGAL DISCLAIMER

**USE AT YOUR OWN RISK!**

- This bot automates Instagram interactions, which may violate [Instagram's Terms of Service](https://help.instagram.com/581066165581870)
- Using automation tools can result in your account being **banned, shadowbanned, or restricted**
- Instagram actively detects and penalizes automated behavior
- This project is for **educational purposes only**
- The authors are **not responsible** for any account restrictions or bans
- Always use conservative rate limits and respect Instagram's community guidelines

**By using this software, you accept full responsibility for any consequences.**

---

## Features

- **Multi-Hashtag Campaigns**: Target multiple hashtags with customizable engagement strategies
- **Template-Based Comments**: Smart comment generation with category detection and anti-spam features
- **Rate Limiting**: Configurable daily limits for likes, comments, follows, and unfollows
- **Session Persistence**: Reuses login sessions to avoid frequent re-authentication
- **Human-Like Delays**: Random delays between actions to mimic human behavior
- **Safety Filters**: Skip verified/business accounts, filter by follower count
- **Active Hours**: Only operate during specified time windows
- **Error Handling**: Automatic cooldown on rate limits and error thresholds
- **Dry-Run Mode**: Test configuration without performing actual actions
- **Rich CLI**: Beautiful command-line interface with progress indicators
- **Comprehensive Logging**: Detailed logs for actions and errors
- **Statistics Tracking**: Monitor daily actions and limits

---

## Project Structure

```
instagrapi-local-bot/
├── src/
│   ├── __init__.py
│   ├── bot.py               # Core bot implementation
│   ├── engagement.py        # Engagement logic and filtering
│   ├── comment_generator.py # Template-based comment generation
│   └── config.py            # Configuration management
├── data/
│   ├── sessions/            # Session files (auto-generated)
│   └── logs/                # Log files (auto-generated)
├── config/
│   ├── settings.yaml        # Bot configuration
│   └── templates.json       # Comment templates
├── examples/
│   ├── basic_like.py        # Example: Like posts by hashtag
│   ├── auto_comment.py      # Example: Like + comment
│   └── hashtag_engage.py    # Example: Full engagement campaign
├── requirements.txt
├── .env.example
├── .env                     # Your credentials (create this)
├── .gitignore
├── README.md
├── run_bot.py               # Main CLI interface
└── test_bot.py              # Test suite
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Instagram account (preferably a test account)

### Step 1: Clone or Download

Clone this repository or download and extract the files:

```bash
cd instagrapi-local-bot
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `instagrapi` - Instagram API wrapper
- `python-dotenv` - Environment variable management
- `pyyaml` - YAML configuration parsing
- `pydantic` - Data validation
- `rich` - Beautiful terminal output

### Step 4: Configure Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Instagram credentials:
   ```env
   INSTAGRAM_USERNAME=your_username_here
   INSTAGRAM_PASSWORD=your_password_here
   LOG_LEVEL=INFO
   DRY_RUN=false
   ```

   **Security Note**: NEVER commit `.env` to version control! It's already in `.gitignore`.

### Step 5: Customize Configuration (Optional)

Edit `config/settings.yaml` to customize:
- Campaign hashtags and targets
- Daily rate limits (start conservative!)
- Active hours
- Safety filters
- Logging preferences

Edit `config/templates.json` to customize comment templates.

---

## Usage

### CLI Commands

The main interface is `run_bot.py` with several commands:

#### 1. Test Login

Test your Instagram credentials:

```bash
python run_bot.py login
```

#### 2. Engage with Hashtag

Like posts from a specific hashtag:

```bash
python run_bot.py hashtag fitness --max 10
```

Like and comment on posts:

```bash
python run_bot.py hashtag gym --max 5 --comment
```

#### 3. Run Campaign

Run a pre-configured campaign from `settings.yaml`:

```bash
python run_bot.py campaign fitness_campaign
```

#### 4. View Statistics

Check current daily statistics:

```bash
python run_bot.py stats
```

#### 5. Reset Statistics

Reset daily counters (requires confirmation):

```bash
python run_bot.py reset --confirm
```

#### 6. Run Tests

Run test suite without API calls:

```bash
python run_bot.py test
```

### Dry-Run Mode

Test everything without performing actual actions:

```bash
python run_bot.py --dry-run hashtag fitness --max 10
```

### Advanced Options

```bash
# Custom configuration file
python run_bot.py --config custom_settings.yaml campaign test_campaign

# Verbose logging
python run_bot.py --log-level DEBUG hashtag travel --max 5

# Combine options
python run_bot.py --dry-run --log-level DEBUG hashtag food --max 3 --comment
```

---

## Examples

### Example 1: Basic Like Bot

Simple script that likes posts from a hashtag:

```bash
python examples/basic_like.py
```

See: [examples/basic_like.py](examples/basic_like.py)

### Example 2: Auto Comment Bot

Likes and comments on posts using templates:

```bash
python examples/auto_comment.py
```

See: [examples/auto_comment.py](examples/auto_comment.py)

### Example 3: Full Engagement Bot

Complete campaign with all features:

```bash
python examples/hashtag_engage.py
```

See: [examples/hashtag_engage.py](examples/hashtag_engage.py)

---

## Configuration Guide

### settings.yaml

#### Instagram Credentials
```yaml
instagram:
  username: ""  # Leave empty, uses .env
  password: ""  # Leave empty, uses .env
```

#### Campaigns
```yaml
campaigns:
  - name: "fitness_campaign"
    hashtags:
      - "fitness"
      - "gym"
      - "workout"
    max_posts_per_hashtag: 10
    like_posts: true
    comment_posts: true
```

#### Rate Limits
```yaml
limits:
  max_likes_per_day: 50      # Conservative starting point
  max_comments_per_day: 20    # Very conservative
  max_follows_per_day: 30
  max_unfollows_per_day: 30
  min_delay_seconds: 30       # Minimum delay between actions
  max_delay_seconds: 60       # Maximum delay between actions
  active_hours_start: 8       # 8 AM
  active_hours_end: 23        # 11 PM
```

**Recommended Limits for New Accounts:**
- Likes: 20-50 per day
- Comments: 10-20 per day
- Follows: 20-30 per day
- Delays: 30-60 seconds

**Recommended Limits for Established Accounts:**
- Likes: 50-100 per day
- Comments: 20-40 per day
- Follows: 30-50 per day
- Delays: 20-40 seconds

#### Safety Settings
```yaml
safety:
  skip_verified: true          # Skip verified accounts (celebrities)
  skip_business: false         # Don't skip business accounts
  min_followers: 100           # Minimum followers to engage
  max_followers: 50000         # Maximum followers to engage
  error_threshold: 3           # Errors before cooldown
  cooldown_minutes: 60         # Cooldown duration
  session_file: "data/sessions/session.json"
```

### templates.json

Comment templates organized by category (hashtag):

```json
{
  "fitness": [
    "Great workout! 💪",
    "Keep pushing! 🔥",
    "Love the dedication! 👏"
  ],
  "default": [
    "Love this! 🔥",
    "Great post! 👏",
    "Amazing! 😍"
  ]
}
```

The bot automatically:
- Detects category from hashtags
- Avoids repeating recent comments
- Falls back to "default" category if needed

---

## Safety Best Practices

### Start Small
- Begin with very conservative limits (20 likes, 10 comments per day)
- Use dry-run mode first to test configuration
- Monitor your account for any warnings

### Use Test Account
- **STRONGLY RECOMMENDED**: Test on a throwaway account first
- Never use your main/business account for initial testing
- Instagram may ban without warning

### Gradual Increase
- Increase limits slowly over weeks/months
- Mimic natural account growth
- Take breaks (don't run 24/7)

### Respect Active Hours
- Only operate during realistic hours (e.g., 8 AM - 11 PM)
- Avoid overnight automation (obvious bot behavior)

### Session Management
- The bot saves sessions to avoid frequent logins
- Don't delete session files unnecessarily
- Multiple logins per day can trigger security checks

### Monitoring
- Check `data/logs/` regularly for errors
- Watch for rate limit warnings in logs
- Monitor account health in Instagram app

### Red Flags to Avoid
- ❌ More than 100 likes per day (new accounts)
- ❌ Commenting too fast (< 30 seconds between)
- ❌ Same comment text repeatedly
- ❌ Running 24/7 without breaks
- ❌ Engaging with same accounts repeatedly
- ❌ Ignoring error messages

---

## Troubleshooting

### Login Failed

**Issue**: `Login failed` or `Challenge required`

**Solutions**:
1. Check credentials in `.env`
2. Complete any challenges in Instagram app
3. Verify account isn't locked/banned
4. Try logging in manually first
5. Wait 24 hours if too many login attempts

### Rate Limited

**Issue**: `Please wait a few minutes` or `Action blocked`

**Solutions**:
1. Stop the bot immediately
2. Wait for the cooldown period (1-24 hours)
3. Reduce rate limits in `settings.yaml`
4. Increase delays between actions
5. Don't force actions when rate limited

### Session Expired

**Issue**: `Session expired, need to login again`

**Solution**: This is normal. The bot will re-login automatically. If it happens too frequently:
1. Check if session file is being saved properly
2. Ensure `data/sessions/` directory exists
3. Don't run multiple bot instances simultaneously

### Template Not Found

**Issue**: `Category 'xyz' not found, using 'default'`

**Solution**: Add the category to `config/templates.json`:
```json
{
  "xyz": [
    "Comment 1",
    "Comment 2"
  ]
}
```

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'instagrapi'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Permission Errors

**Issue**: Can't create log files or session files

**Solution**:
```bash
# Windows
mkdir data\sessions data\logs

# Linux/Mac
mkdir -p data/sessions data/logs
```

---

## FAQ

### Q: Is this legal?

**A**: The code itself is legal, but using automation bots may violate Instagram's Terms of Service. This is for educational purposes only.

### Q: Will my account get banned?

**A**: Possibly. Instagram actively detects and penalizes automation. Use at your own risk, preferably with a test account.

### Q: What are safe limits?

**A**: There's no "safe" limit, but conservative values are:
- New accounts: 20 likes, 10 comments per day
- Established accounts: 50 likes, 20 comments per day
- Always use 30-60 second delays

### Q: Can I run this 24/7?

**A**: **Not recommended**. Use `active_hours` to limit operation to realistic times (e.g., 8 AM - 11 PM).

### Q: How do I add more comment templates?

**A**: Edit `config/templates.json` and add categories (hashtags) with comment arrays.

### Q: Can I target specific users instead of hashtags?

**A**: The current implementation focuses on hashtags. Targeting specific users would require code modifications.

### Q: Does this work with 2FA (two-factor authentication)?

**A**: Instagrapi supports 2FA, but you may need to handle the verification flow manually during first login.

### Q: Can I use proxy/VPN?

**A**: Yes, but you'll need to configure Instagrapi's client with proxy settings. See [Instagrapi documentation](https://github.com/subzeroid/instagrapi).

### Q: Where are logs stored?

**A**: `data/logs/actions.log` (all actions) and `data/logs/errors.log` (errors only).

### Q: How do I reset daily statistics?

**A**: Run `python run_bot.py reset --confirm` or wait until midnight (automatic reset).

---

## Development

### Running Tests

```bash
python test_bot.py
```

or

```bash
python run_bot.py test
```

Tests include:
- Configuration validation
- Comment generator functionality
- Bot initialization
- Dry-run mode
- File structure verification

### Code Structure

- **src/bot.py**: Core `InstagramBot` class with login, session management, and action methods
- **src/engagement.py**: `EngagementManager` for campaigns and filtering
- **src/comment_generator.py**: `TemplateCommentGenerator` for smart comments
- **src/config.py**: Configuration loading and validation with Pydantic

### Adding Features

To add new features:
1. Create methods in appropriate modules
2. Add configuration options to `settings.yaml`
3. Update CLI commands in `run_bot.py`
4. Add tests to `test_bot.py`
5. Update this README

---

## Contributing

This is an educational project. Contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

Please ensure:
- Code follows PEP 8 style guide
- All functions have docstrings
- New features include tests
- README is updated

---

## Credits

- Built with [Instagrapi](https://github.com/subzeroid/instagrapi) by subzeroid
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Inspired by Instagram automation best practices

---

## License

This project is provided "as-is" for educational purposes. See LICENSE file for details.

**Remember**: Use responsibly and ethically. Respect Instagram's Terms of Service and other users' privacy.

---

## Support

For issues:
1. Check this README and troubleshooting section
2. Review [Instagrapi documentation](https://github.com/subzeroid/instagrapi)
3. Check existing GitHub issues
4. Create new issue with detailed information

**Note**: No support for banned accounts or TOS violations.

---

## Changelog

### v1.0.0 (Initial Release)
- Core bot functionality with Instagrapi
- Multi-hashtag campaigns
- Template-based commenting
- Rate limiting and safety features
- CLI interface
- Dry-run mode
- Comprehensive logging
- Test suite

---

**Happy (responsible) botting! 🤖**
