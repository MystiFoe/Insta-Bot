#!/usr/bin/env python3
"""
Instagram Bot Desktop GUI - Modern UI
A professional Tkinter-based interface for controlling the Instagram bot.
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import sys
import os
import ctypes

# Enable DPI awareness for sharp rendering on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bot_controller import BotController, BotState, BotStatus


# Modern Color Palette
COLORS = {
    'bg': '#F8FAFC',
    'card': '#FFFFFF',
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_dark': '#1E40AF',
    'text': '#1E293B',
    'text_secondary': '#64748B',
    'text_muted': '#94A3B8',
    'success': '#10B981',
    'success_bg': '#D1FAE5',
    'error': '#EF4444',
    'error_bg': '#FEE2E2',
    'warning': '#F59E0B',
    'warning_bg': '#FEF3C7',
    'border': '#E2E8F0',
    'input_bg': '#F1F5F9',
    'progress_likes': '#10B981',
    'progress_comments': '#3B82F6',
    'progress_follows': '#F59E0B',
}


class ModernButton(tk.Canvas):
    """Modern styled button with hover effects."""

    def __init__(self, parent, text, command=None, style='primary', width=140, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, bg=COLORS['card'],
                        highlightthickness=0, **kwargs)

        self.command = command
        self.style = style
        self.text = text
        self.width = width
        self.height = height
        self._enabled = True

        # Colors based on style
        if style == 'primary':
            self.bg_color = COLORS['primary']
            self.hover_color = COLORS['primary_hover']
            self.text_color = '#FFFFFF'
        elif style == 'danger':
            self.bg_color = COLORS['error']
            self.hover_color = '#DC2626'
            self.text_color = '#FFFFFF'
        elif style == 'secondary':
            self.bg_color = COLORS['input_bg']
            self.hover_color = COLORS['border']
            self.text_color = COLORS['text']
        else:
            self.bg_color = COLORS['primary']
            self.hover_color = COLORS['primary_hover']
            self.text_color = '#FFFFFF'

        self.current_color = self.bg_color
        self._draw()

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

    def _draw(self):
        self.delete('all')
        radius = 8

        # Draw rounded rectangle
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius,
                                fill=self.current_color, outline='')

        # Draw text
        self.create_text(self.width//2, self.height//2, text=self.text,
                        fill=self.text_color if self._enabled else COLORS['text_muted'],
                        font=('Segoe UI', 10, 'bold'))

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, event):
        if self._enabled:
            self.current_color = self.hover_color
            self._draw()
            self.config(cursor='hand2')

    def _on_leave(self, event):
        if self._enabled:
            self.current_color = self.bg_color
            self._draw()

    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()

    def set_enabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self.current_color = self.bg_color
        else:
            self.current_color = COLORS['border']
        self._draw()


class ModernProgressBar(tk.Canvas):
    """Modern styled progress bar."""

    def __init__(self, parent, width=200, height=8, color='#10B981', **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=COLORS['card'], highlightthickness=0, **kwargs)
        self.bar_width = width
        self.bar_height = height
        self.color = color
        self.value = 0
        self._draw()

    def _draw(self):
        self.delete('all')
        radius = self.bar_height // 2

        # Background track
        self._rounded_rect(0, 0, self.bar_width, self.bar_height, radius,
                          fill=COLORS['input_bg'])

        # Progress fill
        if self.value > 0:
            fill_width = max(self.bar_height, (self.value / 100) * self.bar_width)
            self._rounded_rect(0, 0, fill_width, self.bar_height, radius,
                              fill=self.color)

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def set_value(self, value):
        self.value = min(100, max(0, value))
        self._draw()


class StatusBadge(tk.Frame):
    """Modern status badge with colored dot."""

    def __init__(self, parent, text='Ready', status='success', **kwargs):
        super().__init__(parent, bg=COLORS['card'], **kwargs)

        self.status_colors = {
            'success': (COLORS['success'], COLORS['success_bg']),
            'error': (COLORS['error'], COLORS['error_bg']),
            'warning': (COLORS['warning'], COLORS['warning_bg']),
            'running': (COLORS['primary'], '#DBEAFE'),
        }

        self.dot = tk.Canvas(self, width=10, height=10, bg=COLORS['card'],
                            highlightthickness=0)
        self.dot.pack(side='left', padx=(0, 6))

        self.label = tk.Label(self, text=text, font=('Segoe UI', 9, 'bold'),
                             bg=COLORS['card'], fg=COLORS['text'])
        self.label.pack(side='left')

        self.set_status(status, text)

    def set_status(self, status, text=None):
        color, bg = self.status_colors.get(status, self.status_colors['success'])

        self.dot.delete('all')
        self.dot.create_oval(1, 1, 9, 9, fill=color, outline='')

        if text:
            self.label.config(text=text, fg=color)


class Card(tk.Frame):
    """Modern card container with shadow effect."""

    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, bg=COLORS['card'], **kwargs)

        self.config(highlightbackground=COLORS['border'], highlightthickness=1)

        if title:
            title_frame = tk.Frame(self, bg=COLORS['card'])
            title_frame.pack(fill='x', padx=20, pady=(16, 8))

            tk.Label(title_frame, text=title, font=('Segoe UI', 12, 'bold'),
                    bg=COLORS['card'], fg=COLORS['text']).pack(anchor='w')

        self.content = tk.Frame(self, bg=COLORS['card'])
        self.content.pack(fill='both', expand=True, padx=20, pady=(8, 16))


class BotGUI:
    """Main GUI application for the Instagram bot."""

    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Instagram Bot Control Panel")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLORS['bg'])

        # Set custom fonts
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family='Segoe UI', size=10)

        # Configure ttk styles
        self._configure_styles()

        # Initialize controller
        self.controller = BotController()
        self.controller.set_on_status_change(self._on_status_change)
        self.controller.set_on_action(self._on_action)
        self.controller.set_on_stats_update(self._on_stats_update)
        self.controller.set_on_log(self._on_log)
        self.controller.set_on_challenge_code(self._on_challenge_code)

        # State variables
        self.is_initialized = False
        self.polling_active = False

        # Build UI
        self._create_widgets()

        # Initialize bot
        self.root.after(100, self._initialize_bot)

    def _configure_styles(self):
        """Configure ttk styles for modern look."""
        style = ttk.Style()

        # Entry style
        style.configure('Modern.TEntry',
                       fieldbackground=COLORS['input_bg'],
                       borderwidth=0,
                       relief='flat')

        # Checkbutton style
        style.configure('Modern.TCheckbutton',
                       background=COLORS['card'],
                       font=('Segoe UI', 10))

        # Combobox style
        style.configure('Modern.TCombobox',
                       fieldbackground=COLORS['input_bg'],
                       background=COLORS['input_bg'])

        # Spinbox style
        style.configure('Modern.TSpinbox',
                       fieldbackground=COLORS['input_bg'],
                       background=COLORS['input_bg'])

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        self.main_frame = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_frame.pack(fill='both', expand=True, padx=24, pady=20)

        # Header section
        self._create_header()

        # Content section (controls + activity)
        self._create_content()

        # Footer section
        self._create_footer()

    def _create_header(self):
        """Create the header section."""
        header = tk.Frame(self.main_frame, bg=COLORS['bg'])
        header.pack(fill='x', pady=(0, 20))

        # Left side - App title and account
        left = tk.Frame(header, bg=COLORS['bg'])
        left.pack(side='left')

        tk.Label(left, text="Instagram Bot", font=('Segoe UI', 20, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')

        self.account_label = tk.Label(left, text="@loading...",
                                      font=('Segoe UI', 11),
                                      bg=COLORS['bg'], fg=COLORS['text_secondary'])
        self.account_label.pack(anchor='w', pady=(2, 0))

        # Right side - Status badges
        right = tk.Frame(header, bg=COLORS['bg'])
        right.pack(side='right')

        self.status_badge = StatusBadge(right, text='Initializing', status='warning')
        self.status_badge.pack(side='right')
        self.status_badge.config(bg=COLORS['bg'])
        self.status_badge.dot.config(bg=COLORS['bg'])
        self.status_badge.label.config(bg=COLORS['bg'])

    def _create_content(self):
        """Create the main content area."""
        content = tk.Frame(self.main_frame, bg=COLORS['bg'])
        content.pack(fill='both', expand=True)

        # Left column - Controls
        left_col = tk.Frame(content, bg=COLORS['bg'], width=280)
        left_col.pack(side='left', fill='y', padx=(0, 16))
        left_col.pack_propagate(False)

        self._create_controls(left_col)

        # Right column - Activity Monitor
        right_col = tk.Frame(content, bg=COLORS['bg'])
        right_col.pack(side='left', fill='both', expand=True)

        self._create_activity_monitor(right_col)

    def _create_controls(self, parent):
        """Create the controls panel."""
        # Engagement Card
        card = Card(parent, title="Engagement Settings")
        card.pack(fill='x', pady=(0, 16))

        # Hashtag input
        tk.Label(card.content, text="Hashtag", font=('Segoe UI', 9),
                bg=COLORS['card'], fg=COLORS['text_secondary']).pack(anchor='w')

        self.hashtag_var = tk.StringVar(value="travel")
        hashtag_frame = tk.Frame(card.content, bg=COLORS['input_bg'],
                                highlightbackground=COLORS['border'],
                                highlightthickness=1)
        hashtag_frame.pack(fill='x', pady=(4, 12))

        tk.Label(hashtag_frame, text="#", font=('Segoe UI', 11),
                bg=COLORS['input_bg'], fg=COLORS['text_muted']).pack(side='left', padx=(10, 0))

        self.hashtag_entry = tk.Entry(hashtag_frame, textvariable=self.hashtag_var,
                                      font=('Segoe UI', 11), bg=COLORS['input_bg'],
                                      fg=COLORS['text'], relief='flat', width=20)
        self.hashtag_entry.pack(side='left', fill='x', expand=True, padx=(4, 10), pady=10)

        # Max posts
        tk.Label(card.content, text="Maximum Posts", font=('Segoe UI', 9),
                bg=COLORS['card'], fg=COLORS['text_secondary']).pack(anchor='w')

        self.max_posts_var = tk.StringVar(value="10")
        posts_frame = tk.Frame(card.content, bg=COLORS['input_bg'],
                              highlightbackground=COLORS['border'],
                              highlightthickness=1)
        posts_frame.pack(fill='x', pady=(4, 12))

        self.max_posts_spin = tk.Spinbox(posts_frame, from_=1, to=50,
                                         textvariable=self.max_posts_var,
                                         font=('Segoe UI', 11), bg=COLORS['input_bg'],
                                         fg=COLORS['text'], relief='flat', width=10,
                                         buttonbackground=COLORS['input_bg'])
        self.max_posts_spin.pack(fill='x', padx=10, pady=10)

        # Options
        options_frame = tk.Frame(card.content, bg=COLORS['card'])
        options_frame.pack(fill='x', pady=(4, 12))

        self.like_var = tk.BooleanVar(value=True)
        self.like_check = tk.Checkbutton(options_frame, text="Like Posts",
                                         variable=self.like_var,
                                         font=('Segoe UI', 10),
                                         bg=COLORS['card'], fg=COLORS['text'],
                                         activebackground=COLORS['card'],
                                         selectcolor=COLORS['input_bg'])
        self.like_check.pack(anchor='w')

        self.comment_var = tk.BooleanVar(value=False)
        self.comment_check = tk.Checkbutton(options_frame, text="Comment on Posts",
                                            variable=self.comment_var,
                                            font=('Segoe UI', 10),
                                            bg=COLORS['card'], fg=COLORS['text'],
                                            activebackground=COLORS['card'],
                                            selectcolor=COLORS['input_bg'])
        self.comment_check.pack(anchor='w')

        # Campaign Card
        campaign_card = Card(parent, title="Campaign")
        campaign_card.pack(fill='x', pady=(0, 16))

        tk.Label(campaign_card.content, text="Select Campaign", font=('Segoe UI', 9),
                bg=COLORS['card'], fg=COLORS['text_secondary']).pack(anchor='w')

        self.campaign_var = tk.StringVar(value="")
        campaign_frame = tk.Frame(campaign_card.content, bg=COLORS['input_bg'],
                                 highlightbackground=COLORS['border'],
                                 highlightthickness=1)
        campaign_frame.pack(fill='x', pady=(4, 0))

        self.campaign_combo = ttk.Combobox(campaign_frame, textvariable=self.campaign_var,
                                          state='readonly', font=('Segoe UI', 10))
        self.campaign_combo.pack(fill='x', padx=8, pady=8)

        # AI Prompt Card
        prompt_card = Card(parent, title="AI Comment Prompt")
        prompt_card.pack(fill='x', pady=(0, 16))

        tk.Label(prompt_card.content, text="Customize the prompt sent to AI\nfor generating comments.",
                font=('Segoe UI', 8), bg=COLORS['card'],
                fg=COLORS['text_muted'], justify='left').pack(anchor='w')

        self.edit_prompt_btn = ModernButton(prompt_card.content, text="Edit Prompt",
                                            command=self._open_prompt_editor, style='secondary',
                                            width=240, height=36)
        self.edit_prompt_btn.pack(fill='x', pady=(8, 0))

        # Action Buttons
        buttons_frame = tk.Frame(parent, bg=COLORS['bg'])
        buttons_frame.pack(fill='x', pady=(8, 0))

        self.start_btn = ModernButton(buttons_frame, text="▶  Start Bot",
                                      command=self._start_bot, style='primary',
                                      width=240, height=44)
        self.start_btn.pack(fill='x', pady=(0, 8))

        self.stop_btn = ModernButton(buttons_frame, text="■  Stop",
                                     command=self._stop_bot, style='secondary',
                                     width=240, height=44)
        self.stop_btn.pack(fill='x')
        self.stop_btn.set_enabled(False)

    def _create_activity_monitor(self, parent):
        """Create the activity monitor panel."""
        # Stats Card
        stats_card = Card(parent, title="Daily Statistics")
        stats_card.pack(fill='x', pady=(0, 16))

        # Stats grid
        stats_grid = tk.Frame(stats_card.content, bg=COLORS['card'])
        stats_grid.pack(fill='x')

        # Likes stat
        self._create_stat_item(stats_grid, 0, "Likes", "0/50", COLORS['progress_likes'])
        self.likes_progress = self.stat_progress
        self.likes_label = self.stat_label

        # Comments stat
        self._create_stat_item(stats_grid, 1, "Comments", "0/20", COLORS['progress_comments'])
        self.comments_progress = self.stat_progress
        self.comments_label = self.stat_label

        # Follows stat
        self._create_stat_item(stats_grid, 2, "Follows", "0/30", COLORS['progress_follows'])
        self.follows_progress = self.stat_progress
        self.follows_label = self.stat_label

        # Info row
        info_frame = tk.Frame(stats_card.content, bg=COLORS['card'])
        info_frame.pack(fill='x', pady=(16, 0))

        self.last_action_label = tk.Label(info_frame, text="Last Action: Never",
                                          font=('Segoe UI', 9),
                                          bg=COLORS['card'], fg=COLORS['text_secondary'])
        self.last_action_label.pack(side='left')

        self.errors_label = tk.Label(info_frame, text="Errors: 0/3",
                                     font=('Segoe UI', 9),
                                     bg=COLORS['card'], fg=COLORS['text_secondary'])
        self.errors_label.pack(side='right')

        # Current status
        self.current_action_label = tk.Label(stats_card.content, text="Status: Idle",
                                             font=('Segoe UI', 10, 'bold'),
                                             bg=COLORS['card'], fg=COLORS['text_muted'])
        self.current_action_label.pack(anchor='w', pady=(12, 0))

        # Action Log Card
        log_card = Card(parent, title="Activity Log")
        log_card.pack(fill='both', expand=True)

        # Log container with scrollbar
        log_container = tk.Frame(log_card.content, bg=COLORS['input_bg'],
                                highlightbackground=COLORS['border'],
                                highlightthickness=1)
        log_container.pack(fill='both', expand=True)

        # Custom scrollbar
        scrollbar = tk.Scrollbar(log_container, bg=COLORS['input_bg'],
                                troughcolor=COLORS['input_bg'],
                                activebackground=COLORS['text_muted'])
        scrollbar.pack(side='right', fill='y')

        self.log_text = tk.Text(log_container, font=('Segoe UI', 9),
                               bg=COLORS['input_bg'], fg=COLORS['text'],
                               relief='flat', wrap='word',
                               yscrollcommand=scrollbar.set,
                               padx=12, pady=12)
        self.log_text.pack(fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configure text tags for colored logs
        self.log_text.tag_configure('time', foreground=COLORS['text_muted'])
        self.log_text.tag_configure('like', foreground=COLORS['success'])
        self.log_text.tag_configure('comment', foreground=COLORS['primary'])
        self.log_text.tag_configure('error', foreground=COLORS['error'])
        self.log_text.tag_configure('info', foreground=COLORS['text_secondary'])

        self.log_text.config(state='disabled')

    def _create_stat_item(self, parent, row, label, value, color):
        """Create a stat item row."""
        frame = tk.Frame(parent, bg=COLORS['card'])
        frame.pack(fill='x', pady=6)

        # Label
        tk.Label(frame, text=label, font=('Segoe UI', 10),
                bg=COLORS['card'], fg=COLORS['text']).pack(side='left')

        # Value
        self.stat_label = tk.Label(frame, text=value, font=('Segoe UI', 10, 'bold'),
                                   bg=COLORS['card'], fg=COLORS['text'])
        self.stat_label.pack(side='right')

        # Progress bar
        self.stat_progress = ModernProgressBar(frame, width=180, height=6, color=color)
        self.stat_progress.pack(side='right', padx=(0, 12))

    def _create_footer(self):
        """Create the footer section."""
        footer = tk.Frame(self.main_frame, bg=COLORS['bg'])
        footer.pack(fill='x', pady=(16, 0))

        # Left buttons
        left = tk.Frame(footer, bg=COLORS['bg'])
        left.pack(side='left')

        self.view_logs_btn = ModernButton(left, text="View Logs",
                                          command=self._view_logs, style='secondary',
                                          width=100, height=36)
        self.view_logs_btn.pack(side='left', padx=(0, 8))

        self.reset_btn = ModernButton(left, text="Reset Stats",
                                      command=self._reset_stats, style='secondary',
                                      width=100, height=36)
        self.reset_btn.pack(side='left')

        # Right - Dry run toggle
        right = tk.Frame(footer, bg=COLORS['bg'])
        right.pack(side='right')

        self.dry_run_var = tk.BooleanVar(value=False)
        self.dry_run_check = tk.Checkbutton(right, text="Dry Run (Test Mode)",
                                            variable=self.dry_run_var,
                                            font=('Segoe UI', 9),
                                            bg=COLORS['bg'], fg=COLORS['text_secondary'],
                                            activebackground=COLORS['bg'],
                                            selectcolor=COLORS['input_bg'])
        self.dry_run_check.pack()

    def _initialize_bot(self):
        """Initialize the bot controller."""
        self._log_message("Initializing bot...", 'info')

        if self.controller.initialize():
            self.is_initialized = True
            self._update_account_info()
            self._load_campaigns()
            self._update_stats()
            self.status_badge.set_status('success', 'Ready')
            self._log_message("Bot ready!", 'info')
        else:
            self.status_badge.set_status('error', 'Error')
            self._log_message("Failed to initialize bot", 'error')
            messagebox.showerror(
                "Initialization Error",
                "Failed to initialize the bot. Check your configuration."
            )

    def _update_account_info(self):
        """Update the account info display."""
        username = self.controller.get_username()
        self.account_label.config(text=f"@{username}")

    def _load_campaigns(self):
        """Load available campaigns into dropdown."""
        campaigns = self.controller.get_campaigns()
        self.campaign_combo['values'] = [''] + campaigns
        self.campaign_var.set('')

    def _update_stats(self):
        """Update the stats display."""
        if not self.is_initialized:
            return

        stats = self.controller.get_stats()
        if not stats:
            return

        # Parse limits
        limits = stats.get('limits', {})

        # Likes
        likes_str = limits.get('likes', '0/50')
        current, max_val = self._parse_limit(likes_str)
        self.likes_progress.set_value((current / max_val * 100) if max_val > 0 else 0)
        self.likes_label.config(text=likes_str)

        # Comments
        comments_str = limits.get('comments', '0/20')
        current, max_val = self._parse_limit(comments_str)
        self.comments_progress.set_value((current / max_val * 100) if max_val > 0 else 0)
        self.comments_label.config(text=comments_str)

        # Follows
        follows_str = limits.get('follows', '0/30')
        current, max_val = self._parse_limit(follows_str)
        self.follows_progress.set_value((current / max_val * 100) if max_val > 0 else 0)
        self.follows_label.config(text=follows_str)

        # Last action
        last_action = stats.get('last_action_time', 'Never')
        if last_action and last_action != 'Never':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_action)
                last_action = dt.strftime("%H:%M:%S")
            except:
                pass
        self.last_action_label.config(text=f"Last Action: {last_action}")

        # Errors
        errors = stats.get('errors_count', 0)
        error_color = COLORS['error'] if errors > 0 else COLORS['text_secondary']
        self.errors_label.config(text=f"Errors: {errors}/3", fg=error_color)

    def _parse_limit(self, limit_str: str) -> tuple:
        """Parse a limit string like '10/50' into (current, max)."""
        try:
            parts = limit_str.split('/')
            return int(parts[0]), int(parts[1])
        except:
            return 0, 100

    def _start_bot(self):
        """Start the bot operation."""
        if not self.is_initialized:
            messagebox.showwarning("Not Ready", "Bot is not initialized yet.")
            return

        # Check if campaign is selected
        campaign = self.campaign_var.get()
        if campaign:
            like_posts = self.like_var.get()
            comment_posts = self.comment_var.get()
            self.controller.start_campaign(campaign, like_override=like_posts, comment_override=comment_posts)
            self._log_message(f"Starting campaign: {campaign}", 'info')
        else:
            # Use hashtag
            hashtag = self.hashtag_var.get().strip()
            if not hashtag:
                messagebox.showwarning("Input Required", "Please enter a hashtag or select a campaign.")
                return

            hashtag = hashtag.lstrip('#')
            max_posts = int(self.max_posts_var.get())
            like_posts = self.like_var.get()
            comment_posts = self.comment_var.get()

            self.controller.start_hashtag_engagement(
                hashtag=hashtag,
                max_posts=max_posts,
                like_posts=like_posts,
                comment_posts=comment_posts
            )
            self._log_message(f"Starting engagement with #{hashtag}", 'info')

        # Update UI state
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)

        # Start polling for updates
        self._start_polling()

    def _stop_bot(self):
        """Stop the bot operation."""
        self.controller.stop()
        self._log_message("Stopping bot...", 'info')

    def _start_polling(self):
        """Start polling for stats updates."""
        self.polling_active = True
        self._poll_updates()

    def _stop_polling(self):
        """Stop polling for updates."""
        self.polling_active = False

    def _poll_updates(self):
        """Poll for updates periodically."""
        if not self.polling_active:
            return

        self._update_stats()
        self.root.after(2000, self._poll_updates)

    def _reset_stats(self):
        """Reset daily statistics."""
        if messagebox.askyesno("Confirm Reset", "Reset all daily statistics?"):
            self.controller.reset_stats()
            self._update_stats()
            self._log_message("Statistics reset", 'info')

    def _view_logs(self):
        """Open the logs directory."""
        import subprocess
        log_path = os.path.join(os.path.dirname(__file__), "data", "logs")
        if os.path.exists(log_path):
            subprocess.Popen(f'explorer "{log_path}"')
        else:
            messagebox.showinfo("No Logs", "Log directory does not exist yet.")

    def _log_message(self, message: str, tag: str = 'info'):
        """Add a message to the log display."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] ", 'time')
        self.log_text.insert('end', f"{message}\n", tag)
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    # Callback handlers
    def _on_status_change(self, status: BotStatus):
        """Handle status change from controller."""
        self.root.after(0, lambda: self._update_status_ui(status))

    def _update_status_ui(self, status: BotStatus):
        """Update UI based on status."""
        if status.state == BotState.RUNNING:
            self.current_action_label.config(text=f"Status: {status.current_action}",
                                            fg=COLORS['primary'])
            self.status_badge.set_status('running', 'Running')
        elif status.state == BotState.STOPPING:
            self.current_action_label.config(text="Status: Stopping...",
                                            fg=COLORS['warning'])
            self.status_badge.set_status('warning', 'Stopping')
        elif status.state == BotState.ERROR:
            self.current_action_label.config(text=f"Status: Error - {status.error_message}",
                                            fg=COLORS['error'])
            self.status_badge.set_status('error', 'Error')
            self.start_btn.set_enabled(True)
            self.stop_btn.set_enabled(False)
            self._stop_polling()
        else:  # IDLE
            self.current_action_label.config(text="Status: Idle",
                                            fg=COLORS['text_muted'])
            self.status_badge.set_status('success', 'Ready')
            self.start_btn.set_enabled(True)
            self.stop_btn.set_enabled(False)
            self._stop_polling()

    def _on_action(self, action: dict):
        """Handle new action from controller."""
        self.root.after(0, lambda: self._add_action_to_log(action))

    def _add_action_to_log(self, action: dict):
        """Add an action to the log."""
        action_type = action.get('action', 'unknown')
        username = action.get('username', '')

        if action_type == 'like':
            self._log_message(f"Liked @{username}", 'like')
        elif action_type == 'comment':
            comment_text = action.get('comment', '')
            if comment_text:
                self._log_message(f"Commented on @{username}: \"{comment_text}\"", 'comment')
            else:
                self._log_message(f"Commented on @{username}", 'comment')
        else:
            self._log_message(f"{action_type} @{username}", 'info')

    def _on_stats_update(self, stats: dict):
        """Handle stats update from controller."""
        self.root.after(0, self._update_stats)

    def _on_log(self, message: str):
        """Handle log message from controller."""
        self.root.after(0, lambda: self._log_message(message, 'info'))

    def _open_prompt_editor(self):
        """Open a dialog to edit the AI comment generation prompt."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit AI Comment Prompt")
        dialog.geometry("560x420")
        dialog.configure(bg=COLORS['bg'])
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 560) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 420) // 2
        dialog.geometry(f"+{x}+{y}")

        # Title
        tk.Label(dialog, text="AI System Prompt",
                 font=('Segoe UI', 14, 'bold'), bg=COLORS['bg'],
                 fg=COLORS['text']).pack(pady=(16, 4), padx=20, anchor='w')

        tk.Label(dialog, text="This prompt instructs the AI how to generate comments.\nEdit it to change the tone, style, or rules.",
                 font=('Segoe UI', 9), bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(padx=20, anchor='w', pady=(0, 10))

        # Buttons (pack FIRST so they're always visible at bottom)
        btn_frame = tk.Frame(dialog, bg=COLORS['bg'])
        btn_frame.pack(side='bottom', fill='x', padx=20, pady=(10, 16))

        def save_prompt():
            new_prompt = prompt_text.get('1.0', 'end-1c').strip()
            if new_prompt:
                self.controller.set_ai_prompt(new_prompt)
                self._log_message("AI prompt updated", 'info')
            dialog.destroy()

        def reset_prompt():
            from src.comment_generator import DEFAULT_AI_PROMPT
            prompt_text.delete('1.0', 'end')
            prompt_text.insert('1.0', DEFAULT_AI_PROMPT)

        reset_btn = tk.Button(btn_frame, text="Reset Default", command=reset_prompt,
                             font=('Segoe UI', 10), bg=COLORS['input_bg'],
                             fg=COLORS['text'], relief='flat', padx=16, pady=8,
                             cursor='hand2', activebackground=COLORS['border'])
        reset_btn.pack(side='left')

        save_btn = tk.Button(btn_frame, text="Save", command=save_prompt,
                            font=('Segoe UI', 10, 'bold'), bg=COLORS['primary'],
                            fg='#FFFFFF', relief='flat', padx=24, pady=8,
                            cursor='hand2', activebackground=COLORS['primary_hover'])
        save_btn.pack(side='right')

        # Text editor (pack AFTER buttons so it fills remaining space)
        text_frame = tk.Frame(dialog, bg=COLORS['border'])
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 0))

        prompt_text = tk.Text(text_frame, font=('Segoe UI', 10),
                             bg=COLORS['input_bg'], fg=COLORS['text'],
                             relief='flat', wrap='word', padx=12, pady=12)
        prompt_text.pack(fill='both', expand=True, padx=1, pady=1)

        # Load current prompt
        current_prompt = self.controller.get_ai_prompt()
        prompt_text.insert('1.0', current_prompt)

    def _on_challenge_code(self) -> str:
        """Show dialog to get verification code from user. Called from bot thread."""
        result = {'code': ''}
        event = threading.Event()

        def show_dialog():
            dialog = tk.Toplevel(self.root)
            dialog.title("Instagram Verification")
            dialog.geometry("400x220")
            dialog.configure(bg=COLORS['bg'])
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()

            # Center on parent
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
            dialog.geometry(f"+{x}+{y}")

            # Title
            tk.Label(dialog, text="Verification Required",
                     font=('Segoe UI', 14, 'bold'), bg=COLORS['bg'],
                     fg=COLORS['text']).pack(pady=(20, 5))

            # Message
            tk.Label(dialog, text="Instagram sent a verification code to your\nemail or phone. Enter it below:",
                     font=('Segoe UI', 10), bg=COLORS['bg'],
                     fg=COLORS['text_secondary']).pack(pady=(0, 15))

            # Code entry
            code_var = tk.StringVar()
            entry = tk.Entry(dialog, textvariable=code_var, font=('Segoe UI', 18),
                           justify='center', width=10, relief='solid', bd=1)
            entry.pack(pady=(0, 15))
            entry.focus_set()

            def submit(event=None):
                result['code'] = code_var.get().strip()
                dialog.destroy()

            entry.bind('<Return>', submit)

            ModernButton(dialog, text="Verify", command=submit,
                        style='primary', width=120, height=36).pack()

            dialog.protocol("WM_DELETE_WINDOW", lambda: (dialog.destroy(), event.set()))
            dialog.wait_window()
            event.set()

        self.root.after(0, show_dialog)
        event.wait(timeout=120)
        return result['code']

    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    app = BotGUI()
    app.run()


if __name__ == "__main__":
    main()
