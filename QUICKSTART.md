# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Edit `.env` file and add your Instagram credentials:

```env
INSTAGRAM_USERNAME=your_real_username
INSTAGRAM_PASSWORD=your_real_password
LOG_LEVEL=INFO
DRY_RUN=false
```

**IMPORTANT**: Use a test account first! Not your main account.

### 3. Test Login

```bash
python run_bot.py login
```

If successful, you should see "✓ Login successful!"

### 4. Run Your First Test (Dry Run)

Test without performing actual actions:

```bash
python run_bot.py --dry-run hashtag fitness --max 5
```

### 5. Run Basic Example

Like 10 posts from #fitness:

```bash
python examples/basic_like.py
```

### 6. Run Full Campaign

Edit `config/settings.yaml` to customize, then:

```bash
python examples/hashtag_engage.py
```

---

## Common Commands

```bash
# Test login
python run_bot.py login

# Like posts from hashtag
python run_bot.py hashtag fitness --max 10

# Like and comment
python run_bot.py hashtag gym --max 5 --comment

# Run campaign
python run_bot.py campaign fitness_campaign

# View statistics
python run_bot.py stats

# Reset daily counters
python run_bot.py reset --confirm

# Dry run (testing only)
python run_bot.py --dry-run hashtag travel --max 5
```

---

## Safety Checklist

Before running the bot:

- [ ] Using a test account (NOT your main account)
- [ ] Set conservative rate limits in `config/settings.yaml`:
  - `max_likes_per_day: 20-50`
  - `max_comments_per_day: 10-20`
- [ ] Set realistic delays:
  - `min_delay_seconds: 30`
  - `max_delay_seconds: 60`
- [ ] Set active hours (e.g., 8 AM - 11 PM)
- [ ] Read and understand the legal disclaimer in README.md
- [ ] Test with `--dry-run` first

---

## Troubleshooting

### Login Fails
- Check credentials in `.env`
- Complete any challenges in Instagram app
- Wait 24 hours if too many login attempts

### "Challenge Required"
- Open Instagram app
- Complete the challenge manually
- Try logging in again

### "Action Blocked"
- Stop the bot immediately
- You've been rate limited
- Wait 24 hours
- Reduce rate limits in config

### Import Errors
```bash
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ **Read the full [README.md](README.md)** for detailed documentation
2. ✅ **Customize** `config/settings.yaml` for your needs
3. ✅ **Add comment templates** in `config/templates.json`
4. ✅ **Monitor logs** in `data/logs/`
5. ✅ **Start small** and increase gradually

---

## File Overview

- **run_bot.py** - Main CLI interface
- **config/settings.yaml** - Bot configuration
- **config/templates.json** - Comment templates
- **.env** - Your credentials (never commit!)
- **examples/** - Ready-to-run examples
- **data/logs/** - Action and error logs
- **data/sessions/** - Session files

---

**Remember**: Instagram automation violates ToS. Use at your own risk!
