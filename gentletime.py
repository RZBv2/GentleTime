"""
GentleTime ✦
A professional productivity timer application with themes, custom tasks, and voice announcements.
Version: 2.0.0
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import threading
import random
import math
import datetime
import os
import sys
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Third-party imports with graceful fallback
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# Configuration & Constants

class AppConfig:
    """Application configuration constants"""
    APP_NAME = "GentleTime"
    APP_VERSION = "1.0.0"
    WINDOW_WIDTH = 480
    WINDOW_HEIGHT = 670
    DEFAULT_THEME = "pookie"
    SUPPORTED_THEMES = ["pookie", "light", "dark", "devil"]
    
    # File paths
    DATA_DIR = Path.home() / ".gentletime"
    USER_FILE = DATA_DIR / "user.json"
    HISTORY_FILE = DATA_DIR / "daily_history.json"
    THEME_FILE = DATA_DIR / "theme.txt"
    TASKS_FILE = DATA_DIR / "custom_tasks.json"
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure data directory exists"""
        cls.DATA_DIR.mkdir(exist_ok=True)


class TimerType(Enum):
    """Timer type enumeration"""
    STUDY = "study"
    EYE_REST = "eye_rest"
    NAP = "nap"
    EXERCISE = "exercise"
    CUSTOM = "custom"
    USER_TASK = "user_task"


@dataclass
class CustomTask:
    """Custom task data structure"""
    name: str
    duration_minutes: int
    created_at: str
    icon: str = "⭐"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomTask':
        return cls(**data)


@dataclass
class DailyActivity:
    """Daily activity record"""
    date: str
    user: str
    activities: List[Dict[str, Any]]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DailyActivity':
        return cls(**data)


# Sound & Speech Manager

class SpeechManager:
    """Manages text-to-speech functionality"""
    
    def __init__(self):
        self._engine = None
        self._initialized = False
        self._init_engine()
    
    def _init_engine(self) -> None:
        """Initialize TTS engine with error handling"""
        if not TTS_AVAILABLE:
            return
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 150)
            self._engine.setProperty('volume', 0.9)
            self._initialized = True
        except Exception as e:
            print(f"TTS initialization failed: {e}", file=sys.stderr)
            self._initialized = False
    
    def speak(self, text: str) -> None:
        """Speak text asynchronously"""
        if not self._initialized:
            return
        
        def _speak():
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}", file=sys.stderr)
        
        threading.Thread(target=_speak, daemon=True).start()


# =============================================================================
# Data Persistence Manager
# =============================================================================

class DataManager:
    """Manages all data persistence operations"""
    
    def __init__(self):
        AppConfig.ensure_data_dir()
        self._lock = threading.Lock()
    
    # User Management
    def save_user(self, user_name: str) -> bool:
        """Save user name"""
        try:
            with self._lock:
                data = {
                    "name": user_name,
                    "first_seen": datetime.datetime.now().isoformat(),
                    "last_seen": datetime.datetime.now().isoformat()
                }
                with open(AppConfig.USER_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save user: {e}", file=sys.stderr)
            return False
    
    def load_user(self) -> Optional[str]:
        """Load saved user name"""
        try:
            if AppConfig.USER_FILE.exists():
                with open(AppConfig.USER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("name")
        except Exception as e:
            print(f"Failed to load user: {e}", file=sys.stderr)
        return None
    
    def update_last_seen(self, user_name: str) -> None:
        """Update user's last seen timestamp"""
        try:
            with self._lock:
                if AppConfig.USER_FILE.exists():
                    with open(AppConfig.USER_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data["last_seen"] = datetime.datetime.now().isoformat()
                    with open(AppConfig.USER_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to update last seen: {e}", file=sys.stderr)
    
    # Theme Management
    def save_theme(self, theme_name: str) -> bool:
        """Save current theme preference"""
        try:
            with self._lock:
                with open(AppConfig.THEME_FILE, 'w', encoding='utf-8') as f:
                    f.write(theme_name)
            return True
        except Exception as e:
            print(f"Failed to save theme: {e}", file=sys.stderr)
            return False
    
    def load_theme(self) -> str:
        """Load saved theme preference"""
        try:
            if AppConfig.THEME_FILE.exists():
                with open(AppConfig.THEME_FILE, 'r', encoding='utf-8') as f:
                    theme = f.read().strip()
                    if theme in AppConfig.SUPPORTED_THEMES:
                        return theme
            return AppConfig.DEFAULT_THEME
        except Exception:
            return AppConfig.DEFAULT_THEME
    
    # Custom Tasks Management
    def save_custom_tasks(self, tasks: List[CustomTask]) -> bool:
        """Save custom tasks to file"""
        try:
            with self._lock:
                data = [task.to_dict() for task in tasks]
                with open(AppConfig.TASKS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save tasks: {e}", file=sys.stderr)
            return False
    
    def load_custom_tasks(self) -> List[CustomTask]:
        """Load custom tasks from file"""
        try:
            if AppConfig.TASKS_FILE.exists():
                with open(AppConfig.TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [CustomTask.from_dict(item) for item in data]
        except Exception as e:
            print(f"Failed to load tasks: {e}", file=sys.stderr)
        return []
    
    # Daily History Management
    def log_daily_activity(self, user: str, activity: str, duration: str, duration_minutes: int) -> None:
        """Log daily activity"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            with self._lock:
                # Load existing history
                history = self.load_daily_history()
                
                # Find or create today's record
                today_record = None
                for record in history:
                    if record.date == today and record.user == user:
                        today_record = record
                        break
                
                if today_record is None:
                    today_record = DailyActivity(date=today, user=user, activities=[])
                    history.append(today_record)
                
                # Add activity
                activity_record = {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "activity": activity,
                    "duration": duration,
                    "duration_minutes": duration_minutes
                }
                today_record.activities.append(activity_record)
                
                # Save back
                with open(AppConfig.HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([record.to_dict() for record in history], f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"Failed to log daily activity: {e}", file=sys.stderr)
    
    def load_daily_history(self) -> List[DailyActivity]:
        """Load daily activity history"""
        try:
            if AppConfig.HISTORY_FILE.exists():
                with open(AppConfig.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [DailyActivity.from_dict(item) for item in data]
        except Exception as e:
            print(f"Failed to load daily history: {e}", file=sys.stderr)
        return []
    
    def get_today_activities(self, user: str) -> List[Dict]:
        """Get today's activities for a user"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        history = self.load_daily_history()
        
        for record in history:
            if record.date == today and record.user == user:
                return record.activities
        return []
    
    def get_weekly_summary(self, user: str) -> Dict:
        """Get weekly summary of activities"""
        history = self.load_daily_history()
        last_7_days = []
        
        today = datetime.datetime.now()
        for i in range(7):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            last_7_days.append(date)
        
        weekly_data = {}
        total_minutes = 0
        total_sessions = 0
        
        for record in history:
            if record.date in last_7_days and record.user == user:
                day_minutes = sum(act.get("duration_minutes", 0) for act in record.activities)
                weekly_data[record.date] = {
                    "activities": len(record.activities),
                    "total_minutes": day_minutes
                }
                total_minutes += day_minutes
                total_sessions += len(record.activities)
        
        return {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "daily_data": weekly_data
        }


# Theme Manager

class ThemeManager:
    """Manages application themes and colors"""
    
    THEMES = {
        "pookie": {
            "bg_start": (180, 165, 240),
            "bg_mid": (200, 185, 248),
            "bg_end": (220, 210, 255),
            "ground1": "#9b8fd4",
            "ground2": "#b0a0e0",
            "grass": "#7060b8",
            "frame_bg": "#f0ecff",
            "frame_border": "#a78bfa",
            "text_primary": "#5b21b6",
            "text_secondary": "#7c3aed",
            "text_soft": "#6d28d9",
            "entry_bg": "#ede9fe",
            "entry_fg": "#4c1d95",
            "placeholder_fg": "#aaaaaa",
            "btn_primary": "#c4b5fd",
            "btn_secondary": "#bfdbfe",
            "btn_tertiary": "#ddd6fe",
            "btn_accent": "#e9d5ff",
            "btn_stop": "#fca5a5",
            "btn_text": "#3b0764",
            "cloud_color": "#eeeaff",
        },
        "light": {
            "bg_start": (245, 245, 255),
            "bg_mid": (250, 250, 255),
            "bg_end": (255, 255, 255),
            "ground1": "#d4d4e8",
            "ground2": "#e8e8f5",
            "grass": "#a0a0c0",
            "frame_bg": "#ffffff",
            "frame_border": "#c0c0e0",
            "text_primary": "#4a4a8a",
            "text_secondary": "#6666aa",
            "text_soft": "#8888bb",
            "entry_bg": "#f8f8ff",
            "entry_fg": "#333366",
            "placeholder_fg": "#ccccdd",
            "btn_primary": "#d8d8f0",
            "btn_secondary": "#e0e0f5",
            "btn_tertiary": "#e8e8fa",
            "btn_accent": "#f0f0ff",
            "btn_stop": "#ffe0e0",
            "btn_text": "#4a4a8a",
            "cloud_color": "#f0f0ff",
        },
        "dark": {
            "bg_start": (20, 20, 35),
            "bg_mid": (30, 30, 45),
            "bg_end": (40, 40, 55),
            "ground1": "#1a1a2e",
            "ground2": "#252540",
            "grass": "#3a3a5a",
            "frame_bg": "#1e1e2e",
            "frame_border": "#4a4a6a",
            "text_primary": "#a8a8d8",
            "text_secondary": "#9898c8",
            "text_soft": "#8888b8",
            "entry_bg": "#2a2a3a",
            "entry_fg": "#c8c8e8",
            "placeholder_fg": "#6a6a8a",
            "btn_primary": "#3a3a5a",
            "btn_secondary": "#404060",
            "btn_tertiary": "#4a4a6a",
            "btn_accent": "#505070",
            "btn_stop": "#7a3a3a",
            "btn_text": "#c8c8e8",
            "cloud_color": "#2a2a40",
        },
        "devil": {
            "bg_start": (30, 10, 10),
            "bg_mid": (50, 15, 15),
            "bg_end": (70, 20, 20),
            "ground1": "#2a0a0a",
            "ground2": "#3a1515",
            "grass": "#5a2525",
            "frame_bg": "#2a0a0a",
            "frame_border": "#8a2020",
            "text_primary": "#ff6666",
            "text_secondary": "#ff4444",
            "text_soft": "#cc4444",
            "entry_bg": "#3a1515",
            "entry_fg": "#ff8888",
            "placeholder_fg": "#aa5555",
            "btn_primary": "#6a2020",
            "btn_secondary": "#7a2828",
            "btn_tertiary": "#8a3030",
            "btn_accent": "#9a3838",
            "btn_stop": "#cc3333",
            "btn_text": "#ffaaaa",
            "cloud_color": "#3a1515",
        }
    }
    
    def __init__(self):
        self.current_theme = AppConfig.DEFAULT_THEME
    
    def get_theme(self, theme_name: str) -> Dict:
        """Get theme configuration"""
        return self.THEMES.get(theme_name, self.THEMES[AppConfig.DEFAULT_THEME])
    
    def get_color(self, theme_name: str, color_key: str) -> str:
        """Get specific color from theme"""
        return self.get_theme(theme_name).get(color_key, "#000000")


# Timer Manager

class TimerManager:
    """Manages timer operations"""
    
    def __init__(self, callback_on_tick: callable, callback_on_complete: callable):
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._is_running = False
        self._current_seconds = 0
        self._callback_tick = callback_on_tick
        self._callback_complete = callback_on_complete
        self._lock = threading.Lock()
    
    def start(self, seconds: int) -> bool:
        """Start a new timer"""
        with self._lock:
            if self._is_running:
                return False
            self._is_running = True
            self._stop_event.clear()
            self._pause_event.clear()
            self._current_seconds = seconds
        
        threading.Thread(target=self._run_timer, args=(seconds,), daemon=True).start()
        return True
    
    def _run_timer(self, seconds: int) -> None:
        """Internal timer execution"""
        remaining = seconds
        
        while remaining > 0 and not self._stop_event.is_set():
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.1)
            
            if self._stop_event.is_set():
                break
            
            remaining -= 1
            self._current_seconds = remaining
            
            if self._callback_tick:
                self._callback_tick(remaining)
            
            time.sleep(1)
        
        with self._lock:
            self._is_running = False
        
        if not self._stop_event.is_set() and self._callback_complete:
            self._callback_complete()
    
    def stop(self) -> None:
        """Stop the current timer"""
        with self._lock:
            if self._is_running:
                self._stop_event.set()
                self._pause_event.clear()
    
    def pause(self) -> None:
        """Pause the current timer"""
        with self._lock:
            if self._is_running and not self._pause_event.is_set():
                self._pause_event.set()
    
    def resume(self) -> None:
        """Resume the paused timer"""
        with self._lock:
            if self._is_running and self._pause_event.is_set():
                self._pause_event.clear()
    
    def toggle_pause(self) -> bool:
        """Toggle pause state, return current paused state"""
        with self._lock:
            if not self._is_running:
                return False
            if self._pause_event.is_set():
                self._pause_event.clear()
                return False
            else:
                self._pause_event.set()
                return True
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()
    
    @property
    def remaining_seconds(self) -> int:
        return self._current_seconds


# Main Application Class

class GentleTimeApp:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{AppConfig.APP_NAME} ✦ v{AppConfig.APP_VERSION}")
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initialize managers
        self.data_manager = DataManager()
        self.theme_manager = ThemeManager()
        self.speech_manager = SpeechManager()
        
        # Load data
        saved_user = self.data_manager.load_user()
        if saved_user:
            self.user_name = saved_user
            self.data_manager.update_last_seen(self.user_name)
        else:
            self.user_name = self._get_user_name()
            self.data_manager.save_user(self.user_name)
        
        self.current_theme = self.data_manager.load_theme()
        self.custom_tasks = self.data_manager.load_custom_tasks()
        
        # Timer variables
        self.current_timer_name = ""
        self.current_timer_duration_minutes = 0
        self.current_timer_announcement = ""
        
        # Initialize timer manager
        self.timer_manager = TimerManager(self._on_timer_tick, self._on_timer_complete)
        
        # UI state
        self.dropdown = None
        self.custom_tasks_frame = None
        
        # Setup UI
        self._setup_ui()
        self._apply_theme(self.current_theme)
        self._refresh_custom_tasks()
        
        # Start animations
        self._animation_counter = 0
        self._animate()
    
    def _get_user_name(self) -> str:
        """Get or create user name"""
        self.root.withdraw()
        name = simpledialog.askstring(
            "Welcome to GentleTime ✦",
            "What's your name?\n\n(This will be used for personalized messages)",
            parent=self.root
        )
        self.root.deiconify()
        return name.strip() if name and name.strip() else "Friend"
    
    def _setup_ui(self) -> None:
        """Setup the user interface"""
        # Canvas for background and decorations
        self.canvas = tk.Canvas(
            self.root,
            width=AppConfig.WINDOW_WIDTH,
            height=AppConfig.WINDOW_HEIGHT,
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0)
        
        # Draw background elements
        self._draw_background()
        self._draw_ground()
        self._draw_grass()
        self._draw_clouds()
        self._draw_mushrooms()
        self._draw_flowers()
        self._draw_sparkles()
        self._draw_animals()
        
        # Title
        self.title_text = self.canvas.create_text(
            AppConfig.WINDOW_WIDTH // 2, 35,
            text=f"Hello {self.user_name}! ✦",
            font=("Segoe UI", 12, "italic"),
            fill="#6d28d9",
            tags="title"
        )
        
        # Menu button
        self.menu_btn = tk.Button(
            self.root,
            text="☰ Menu",
            command=self._toggle_dropdown,
            font=("Segoe UI", 10, "bold"),
            bg="#e9d5ff", fg="#3b0764",
            activebackground="#a78bfa",
            relief="flat", cursor="hand2",
            padx=12, pady=5
        )
        self.menu_btn.place(x=10, y=10)
        
        # Main frame
        self.main_frame = tk.Frame(
            self.root, bg="#f0ecff", bd=0,
            highlightbackground="#a78bfa", highlightthickness=2
        )
        self.canvas.create_window(
            36, 80, anchor="nw",
            window=self.main_frame,
            width=408, height=562
        )
        
        # User info row
        self._setup_user_row()
        
        # Timer display
        self._setup_timer_display()
        
        # Timer controls
        self._setup_timer_controls()
        
        # Action buttons
        self._setup_action_buttons()
    
    def _draw_background(self) -> None:
        """Draw gradient background"""
        theme = self.theme_manager.get_theme(self.current_theme)
        H = AppConfig.WINDOW_HEIGHT
        W = AppConfig.WINDOW_WIDTH
        
        def lerp(a, b, t):
            return int(a + (b - a) * t)
        
        GRAD = [
            (0.0, theme["bg_start"]),
            (0.5, theme["bg_mid"]),
            (1.0, theme["bg_end"]),
        ]
        
        for y in range(H):
            ratio = y / H
            for i in range(len(GRAD) - 1):
                r0, c0 = GRAD[i]
                r1, c1 = GRAD[i + 1]
                if ratio <= r1:
                    t = (ratio - r0) / (r1 - r0) if r1 != r0 else 0
                    color = "#{:02x}{:02x}{:02x}".format(
                        lerp(c0[0], c1[0], t),
                        lerp(c0[1], c1[1], t),
                        lerp(c0[2], c1[2], t)
                    )
                    self.canvas.create_line(0, y, W, y, fill=color, tags="background")
                    break
    
    def _draw_ground(self) -> None:
        """Draw ground"""
        theme = self.theme_manager.get_theme(self.current_theme)
        H = AppConfig.WINDOW_HEIGHT
        W = AppConfig.WINDOW_WIDTH
        self.canvas.create_rectangle(0, H - 42, W, H, fill=theme["ground1"], outline="", tags="ground")
        self.canvas.create_rectangle(0, H - 44, W, H - 40, fill=theme["ground2"], outline="", tags="ground")
    
    def _draw_grass(self) -> None:
        """Draw grass blades"""
        theme = self.theme_manager.get_theme(self.current_theme)
        H = AppConfig.WINDOW_HEIGHT
        W = AppConfig.WINDOW_WIDTH
        for _ in range(22):
            gx = random.randint(5, W - 5)
            gy = H - 44
            for _ in range(3):
                dx = random.randint(-5, 5)
                gh = random.randint(6, 14)
                self.canvas.create_line(gx + dx, gy, gx + dx + random.randint(-3, 3), gy - gh,
                                       fill=theme["grass"], width=2, capstyle="round", tags="grass")
    
    def _draw_clouds(self) -> None:
        """Draw clouds"""
        theme = self.theme_manager.get_theme(self.current_theme)
        W = AppConfig.WINDOW_WIDTH
        
        def draw_cloud(cx, cy, size, col):
            for dx, dy, r in [
                (0, 0, size), (size, -size // 3, int(size * 0.8)),
                (-size, -size // 4, int(size * 0.75)),
                (int(size * 1.6), size // 4, int(size * 0.65)),
                (-int(size * 1.5), size // 4, int(size * 0.6)),
            ]:
                self.canvas.create_oval(cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r,
                                       fill=col, outline="", tags="clouds")
        
        draw_cloud(60, 60, 22, theme["cloud_color"])
        draw_cloud(200, 38, 18, theme["cloud_color"])
        draw_cloud(370, 70, 25, theme["cloud_color"])
        draw_cloud(420, 30, 14, theme["cloud_color"])
    
    def _draw_mushrooms(self) -> None:
        """Draw mushrooms"""
        theme = self.theme_manager.get_theme(self.current_theme)
        H = AppConfig.WINDOW_HEIGHT
        W = AppConfig.WINDOW_WIDTH
        
        mushroom_colors = theme.get("mushroom_colors", [("#a78bfa", "#ddd6fe")])
        
        for _ in range(9):
            cx = random.randint(20, W - 20)
            stem_h = random.randint(14, 26)
            cap_r = random.randint(14, 26)
            cap_col, spot_col = random.choice(mushroom_colors)
            
            self.canvas.create_rectangle(cx - 5, H - 42 - stem_h, cx + 5, H - 42,
                                       fill="#d8d0f0" if self.current_theme not in ["dark", "devil"] else "#3a1515",
                                       outline="", tags="mushrooms")
            self.canvas.create_oval(cx - cap_r, H - 42 - stem_h - cap_r,
                                   cx + cap_r, H - 42 - stem_h + cap_r // 2,
                                   fill=cap_col, outline="", tags="mushrooms")
            for _ in range(3):
                sx = cx + random.randint(-cap_r // 2, cap_r // 2)
                sy = H - 42 - stem_h - random.randint(4, cap_r // 2)
                r = random.randint(3, 6)
                self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                                       fill=spot_col, outline="", tags="mushrooms")
    
    def _draw_flowers(self) -> None:
        """Draw flowers"""
        H = AppConfig.WINDOW_HEIGHT
        W = AppConfig.WINDOW_WIDTH
        self.flower_objects = []
        
        for _ in range(8):
            fx = random.randint(15, W - 15)
            fh = random.randint(45, 85)
            bc = "#a78bfa"
            fc = "#c4b5fd"
            
            if self.current_theme == "devil":
                bc, fc = "#8a2020", "#cc3333"
            
            pts = []
            for s in range(5):
                frac = s / 5
                pts.extend([fx, H - 42 - int(fh * frac)])
            
            self.canvas.create_line(pts, fill="#7060b8", width=2, smooth=True, tags="flowers")
            bx, by = fx, H - 42 - fh
            
            for angle_d in range(0, 360, 60):
                ang = math.radians(angle_d)
                ox = int(math.cos(ang) * 7)
                oy = int(math.sin(ang) * 5)
                self.canvas.create_oval(bx + ox - 5, by + oy - 4,
                                       bx + ox + 5, by + oy + 4,
                                       fill=fc, outline="", tags="flowers")
            
            self.canvas.create_oval(bx - 5, by - 5, bx + 5, by + 5,
                                   fill=bc, outline="", tags="flowers")
    
    def _draw_sparkles(self) -> None:
        """Draw sparkles"""
        W = AppConfig.WINDOW_WIDTH
        H = AppConfig.WINDOW_HEIGHT
        self.sparkle_objects = []
        
        for _ in range(14):
            sx = random.randint(10, W - 10)
            sy = random.randint(50, H - 50)
            glyph = random.choice(["✦", "✿", "★", "✩"])
            self.canvas.create_text(sx, sy, text=glyph,
                                   font=("Arial", random.randint(9, 16)),
                                   fill="#a78bfa", tags="sparkles")
    
    def _draw_animals(self) -> None:
        """Draw animals"""
        self.animal_objects = []
        positions = [(30, 280), (420, 350), (200, 200), (100, 160), (350, 420), (50, 440)]
        
        for x, y in positions:
            self.canvas.create_oval(x - 10, y - 8, x + 10, y + 8,
                                   fill="#c4b5fd", outline="", tags="animals")
            self.canvas.create_oval(x - 6, y - 14, x - 2, y - 8,
                                   fill="#c4b5fd", outline="", tags="animals")
            self.canvas.create_oval(x + 2, y - 14, x + 6, y - 8,
                                   fill="#c4b5fd", outline="", tags="animals")
            self.canvas.create_oval(x - 3, y - 11, x - 1, y - 9,
                                   fill="black", outline="", tags="animals")
            self.canvas.create_oval(x + 1, y - 11, x + 3, y - 9,
                                   fill="black", outline="", tags="animals")
    
    def _setup_user_row(self) -> None:
        """Setup user info row"""
        self.name_row = tk.Frame(self.main_frame, bg="#f0ecff")
        self.name_row.pack(pady=(14, 0))
        
        self.name_lbl = tk.Label(
            self.name_row,
            text=f"Hi {self.user_name} ✦",
            font=("Segoe UI", 12, "bold"),
            bg="#f0ecff", fg="#5b21b6"
        )
        self.name_lbl.pack(side="left", padx=(0, 10))
        
        self.change_name_btn = tk.Button(
            self.name_row,
            text="change name",
            font=("Segoe UI", 8),
            bg="#ddd6fe", fg="#5b21b6",
            relief="flat", cursor="hand2",
            activebackground="#c4b5fd",
            command=self._change_name
        )
        self.change_name_btn.pack(side="left")
    
    def _setup_timer_display(self) -> None:
        """Setup timer display"""
        self.timer_lbl = tk.Label(
            self.main_frame,
            text="00:00",
            font=("Consolas", 50, "bold"),
            bg="#f0ecff", fg="#7c3aed"
        )
        self.timer_lbl.pack(pady=(10, 2))
        
        self.status_lbl = tk.Label(
            self.main_frame,
            text="Ready ✦",
            font=("Segoe UI", 9, "italic"),
            bg="#f0ecff", fg="#6d28d9"
        )
        self.status_lbl.pack()
    
    def _setup_timer_controls(self) -> None:
        """Setup timer input controls"""
        control_frame = tk.Frame(self.main_frame, bg="#f0ecff")
        control_frame.pack(pady=(10, 4))
        
        self.minutes_entry = tk.Entry(
            control_frame,
            font=("Segoe UI", 11),
            justify="center",
            width=20,
            bg="#ede9fe", fg="#aaaaaa",
            insertbackground="#7c3aed",
            relief="flat",
            highlightbackground="#a78bfa",
            highlightthickness=1
        )
        self.minutes_entry.pack(side="left")
        
        self.custom_btn = tk.Button(
            control_frame,
            text="✨ Start Custom",
            command=self._start_custom_timer,
            font=("Segoe UI", 10, "bold"),
            bg="#c4b5fd", fg="#3b0764",
            activebackground="#a78bfa",
            relief="flat", cursor="hand2",
            padx=8, pady=4
        )
        self.custom_btn.pack(side="right", padx=(5, 0))
        
        # Placeholder handling
        self._placeholder_text = "Enter minutes"
        self.minutes_entry.insert(0, self._placeholder_text)
        self.minutes_entry.bind("<FocusIn>", self._clear_placeholder)
        self.minutes_entry.bind("<FocusOut>", self._restore_placeholder)
    
    def _setup_action_buttons(self) -> None:
        """Setup timer action buttons"""

        # Buttons frame
        self.buttons_frame = tk.Frame(self.main_frame, bg="#f0ecff")
        self.buttons_frame.pack(pady=(10, 0))
        
        # Preset timers
        presets = [
            ("📚 Study Timer", self._start_study_timer),
            ("👁 Eye Rest (20 sec)", self._start_eye_rest),
            ("🌙 Nap Timer (20 min)", self._start_nap_timer),
            ("🌸 Exercise (30 min)", self._start_exercise_timer),
        ]
        
        for text, command in presets:
            btn = self._create_button(
                self.buttons_frame, text, command,
                self.theme_manager.get_theme(self.current_theme)["btn_primary"],
                width=26
            )
            btn.pack(pady=3)
        
        # Bottom control bar
        self.bottom_bar = tk.Frame(self.main_frame, bg="#f0ecff")
        self.bottom_bar.pack(pady=(12, 14))
        
        self.stop_btn = self._create_button(
            self.bottom_bar, "Stop", self._stop_timer,
            self.theme_manager.get_theme(self.current_theme)["btn_stop"],
            width=9
        )
        self.stop_btn.pack(side="left", padx=3)
        
        self.pause_btn = self._create_button(
            self.bottom_bar, "⏸ Pause", self._toggle_pause,
            self.theme_manager.get_theme(self.current_theme)["btn_secondary"],
            width=10
        )
        self.pause_btn.pack(side="left", padx=3)
        
        self.history_btn = self._create_button(
            self.bottom_bar, "History", self._show_history,
            self.theme_manager.get_theme(self.current_theme)["btn_tertiary"],
            width=9
        )
        self.history_btn.pack(side="left", padx=3)
        
        self.summary_btn = self._create_button(
            self.bottom_bar, "Summary", self._show_weekly_summary,
            self.theme_manager.get_theme(self.current_theme)["btn_accent"],
            width=9
        )
        self.summary_btn.pack(side="left", padx=3)
    
    def _create_button(self, parent: tk.Widget, text: str, command: callable,
                       bg_color: str, width: int = None) -> tk.Button:
        """Create a styled button"""
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg_color, fg="#3b0764",
            activebackground="#a78bfa",
            relief="flat", cursor="hand2",
            width=width, pady=7
        )
    
    # Timer Actions
    
    def _start_timer(self, seconds: int, name: str, duration_minutes: int, announcement: str) -> None:
        """Start a timer with given parameters"""
        if self.timer_manager.is_running:
            messagebox.showwarning(
                AppConfig.APP_NAME,
                "A timer is already running!\n\nPress Stop first."
            )
            return
        
        self.current_timer_name = name
        self.current_timer_duration_minutes = duration_minutes
        self.current_timer_announcement = announcement
        
        self.timer_manager.start(seconds)
        self.status_lbl.config(text=f"{name} in progress ✦")
    
    def _on_timer_tick(self, remaining: int) -> None:
        """Handle timer tick updates"""
        minutes, seconds = divmod(remaining, 60)
        self.timer_lbl.config(text=f"{minutes:02d}:{seconds:02d}")
    
    def _on_timer_complete(self) -> None:
        """Handle timer completion"""
        self.timer_lbl.config(text="00:00")
        self.status_lbl.config(text="Complete! You did amazing! ✿")
        
        # Log activity
        duration_str = f"{self.current_timer_duration_minutes} min" if self.current_timer_duration_minutes >= 1 else f"{self.current_timer_duration_minutes * 60} sec"
        self.data_manager.log_daily_activity(
            self.user_name,
            self.current_timer_name,
            duration_str,
            self.current_timer_duration_minutes
        )
        
        # Speak announcement
        self.speech_manager.speak(self.current_timer_announcement)
        
        # Show completion dialog
        messagebox.showinfo(
            AppConfig.APP_NAME,
            f"Hey {self.user_name}!\n\n{self.current_timer_name} complete! ✿\n\nWell done!"
        )
        
        self.status_lbl.config(text="Ready ✦")
        self.pause_btn.config(text="⏸ Pause")
    
    def _start_study_timer(self) -> None:
        """Start study timer"""
        try:
            minutes = int(self.minutes_entry.get())
            if minutes <= 0:
                raise ValueError
            announcement = f"{self.user_name}, study session complete! Great job focusing!"
            self._start_timer(minutes * 60, "Study Time", minutes, announcement)
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Please enter valid minutes!")
    
    def _start_eye_rest(self) -> None:
        """Start eye rest timer"""
        announcement = f"{self.user_name}, eye rest complete! Your eyes feel refreshed!"
        self._start_timer(20, "Eye Rest", 0.33, announcement)
    
    def _start_nap_timer(self) -> None:
        """Start nap timer"""
        announcement = f"{self.user_name}, nap time complete! Wake up refreshed!"
        self._start_timer(20 * 60, "Nap Time", 20, announcement)
    
    def _start_exercise_timer(self) -> None:
        """Start exercise timer"""
        announcement = f"{self.user_name}, exercise complete! You're amazing!"
        self._start_timer(30 * 60, "Exercise", 30, announcement)
    
    def _start_custom_timer(self) -> None:
        """Start custom timer from entry field"""
        try:
            minutes = int(self.minutes_entry.get())
            if minutes <= 0:
                raise ValueError
            announcement = f"{self.user_name}, your {minutes}-minute timer is complete! Well done!"
            self._start_timer(minutes * 60, f"{minutes}min Timer", minutes, announcement)
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Please enter valid minutes!")
    
    def _stop_timer(self) -> None:
        """Stop current timer"""
        if self.timer_manager.is_running:
            self.timer_manager.stop()
            self.status_lbl.config(text="Timer stopped ✦")
            self.timer_lbl.config(text="00:00")
            self.pause_btn.config(text="⏸ Pause")
    
    def _toggle_pause(self) -> None:
        """Toggle timer pause/resume"""
        if not self.timer_manager.is_running:
            self.status_lbl.config(text="No timer running ✦")
            return
        
        is_paused = self.timer_manager.toggle_pause()
        if is_paused:
            self.pause_btn.config(text="▶ Resume")
            self.status_lbl.config(text="Paused ✦ Press Resume to continue")
        else:
            self.pause_btn.config(text="⏸ Pause")
            self.status_lbl.config(text="Resumed ✦")
    
    # Custom Tasks Management
    
    def _create_custom_task(self) -> None:
        """Create a new custom task"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Custom Task ✦")
        dialog.geometry("400x250")
        dialog.configure(bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        tk.Label(
            dialog,
            text="Create New Task",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_primary"]
        ).pack(pady=(15, 10))
        
        # Task name
        tk.Label(
            dialog, text="Task Name:", font=("Segoe UI", 10),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_secondary"]
        ).pack(anchor="w", padx=30)
        
        name_entry = tk.Entry(
            dialog, font=("Segoe UI", 11), width=35,
            bg=self.theme_manager.get_theme(self.current_theme)["entry_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["entry_fg"]
        )
        name_entry.pack(pady=(5, 15), padx=30)
        
        # Duration
        tk.Label(
            dialog, text="Duration (minutes):", font=("Segoe UI", 10),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_secondary"]
        ).pack(anchor="w", padx=30)
        
        duration_entry = tk.Entry(
            dialog, font=("Segoe UI", 11), width=35,
            bg=self.theme_manager.get_theme(self.current_theme)["entry_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["entry_fg"]
        )
        duration_entry.pack(pady=(5, 20), padx=30)
        
        def save_task():
            name = name_entry.get().strip()
            try:
                duration = int(duration_entry.get().strip())
                if not name:
                    messagebox.showerror("Error", "Please enter a task name!")
                    return
                if duration <= 0:
                    messagebox.showerror("Error", "Duration must be positive!")
                    return
                
                task = CustomTask(
                    name=name,
                    duration_minutes=duration,
                    created_at=datetime.datetime.now().isoformat()
                )
                self.custom_tasks.append(task)
                self.data_manager.save_custom_tasks(self.custom_tasks)
                self._refresh_custom_tasks()
                dialog.destroy()
                messagebox.showinfo("Success", f"Task '{name}' created!")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for minutes!")
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame, text="Save Task", command=save_task,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["btn_primary"],
            fg="#3b0764", relief="flat", cursor="hand2",
            padx=20, pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame, text="Cancel", command=dialog.destroy,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["btn_stop"],
            fg="white", relief="flat", cursor="hand2",
            padx=20, pady=5
        ).pack(side="left", padx=5)
    
    def _refresh_custom_tasks(self) -> None:
        """Refresh custom tasks display"""
        if self.custom_tasks_frame:
            self.custom_tasks_frame.destroy()
        
        if not self.custom_tasks:
            return
        
        self.custom_tasks_frame = tk.Frame(self.buttons_frame, bg="#f0ecff")
        self.custom_tasks_frame.pack(pady=(10, 0))
        
        tk.Label(
            self.custom_tasks_frame,
            text="✦ My Tasks ✦",
            font=("Segoe UI", 9, "bold"),
            bg="#f0ecff", fg="#5b21b6"
        ).pack(pady=(5, 2))
        
        for task in self.custom_tasks[:5]:  # Show up to 5 tasks
            task_frame = tk.Frame(self.custom_tasks_frame, bg="#f0ecff")
            task_frame.pack(pady=2)
            
            task_btn = tk.Button(
                task_frame,
                text=f"{task.icon} {task.name} ({task.duration_minutes}m)",
                command=lambda t=task: self._start_task_timer(t),
                font=("Segoe UI", 9, "bold"),
                bg=self.theme_manager.get_theme(self.current_theme)["btn_accent"],
                fg="#3b0764", relief="flat", cursor="hand2",
                width=22, pady=5
            )
            task_btn.pack(side="left", padx=(0, 5))
            
            delete_btn = tk.Button(
                task_frame, text="🗑️",
                command=lambda t=task: self._delete_custom_task(t),
                font=("Segoe UI", 9),
                bg=self.theme_manager.get_theme(self.current_theme)["btn_stop"],
                fg="white", relief="flat", cursor="hand2",
                width=3
            )
            delete_btn.pack(side="left")
    
    def _start_task_timer(self, task: CustomTask) -> None:
        """Start a custom task timer"""
        announcement = f"{self.user_name}, {task.name} complete! Great job!"
        self._start_timer(task.duration_minutes * 60, task.name, task.duration_minutes, announcement)
    
    def _delete_custom_task(self, task: CustomTask) -> None:
        """Delete a custom task"""
        if messagebox.askyesno("Delete Task", f'Delete "{task.name}"?'):
            self.custom_tasks.remove(task)
            self.data_manager.save_custom_tasks(self.custom_tasks)
            self._refresh_custom_tasks()
    
    # Theme Management
    
    def _change_theme(self) -> None:
        """Open theme selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Theme ✦")
        dialog.geometry("320x350")
        dialog.configure(bg="#f0ecff")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Choose Your Theme",
            font=("Segoe UI", 14, "bold"),
            bg="#f0ecff", fg="#5b21b6"
        ).pack(pady=(15, 10))
        
        themes = [
            ("🌸 Pookie (Default)", "pookie"),
            ("☀️ Light", "light"),
            ("🌙 Dark", "dark"),
            ("👿 Devil", "devil")
        ]
        
        for display_name, theme_name in themes:
            btn = tk.Button(
                dialog,
                text=display_name,
                command=lambda t=theme_name: [self._apply_theme(t), dialog.destroy()],
                font=("Segoe UI", 10, "bold"),
                bg="#c4b5fd", fg="#3b0764",
                activebackground="#a78bfa",
                relief="flat", cursor="hand2",
                width=25, pady=7
            )
            btn.pack(pady=5)
        
        tk.Button(
            dialog, text="Cancel", command=dialog.destroy,
            font=("Segoe UI", 10), bg="#fca5a5", fg="#7f1d1d",
            relief="flat", cursor="hand2", width=15, pady=5
        ).pack(pady=(10, 15))
    
    def _apply_theme(self, theme_name: str) -> None:
        """Apply theme to all UI elements"""
        self.current_theme = theme_name
        theme = self.theme_manager.get_theme(theme_name)
        
        # Data manager
        self.data_manager.save_theme(theme_name)
        
        # Redraw all visual elements
        self.canvas.delete("background", "ground", "grass", "clouds", "mushrooms", "flowers", "sparkles", "animals")
        self._draw_background()
        self._draw_ground()
        self._draw_grass()
        self._draw_clouds()
        self._draw_mushrooms()
        self._draw_flowers()
        self._draw_sparkles()
        self._draw_animals()
        
        # Update main frame
        self.main_frame.config(bg=theme["frame_bg"], highlightbackground=theme["frame_border"])
        self.name_row.config(bg=theme["frame_bg"])
        self.name_lbl.config(bg=theme["frame_bg"], fg=theme["text_primary"])
        self.timer_lbl.config(bg=theme["frame_bg"], fg=theme["text_secondary"])
        self.status_lbl.config(bg=theme["frame_bg"], fg=theme["text_soft"])
        self.minutes_entry.config(bg=theme["entry_bg"], highlightbackground=theme["frame_border"])
        
        for widget in [self.custom_btn, self.change_name_btn, self.menu_btn,
                       self.stop_btn, self.pause_btn, self.history_btn, self.summary_btn]:
            if widget:
                widget.config(bg=theme["btn_primary"],
                             fg=theme["btn_text"])
        
        self._refresh_custom_tasks()
        
        self.canvas.itemconfig(self.title_text, fill=theme["text_soft"])
    
    # History & Summary
    
    def _show_history(self) -> None:
        """Display activity history"""
        today_activities = self.data_manager.get_today_activities(self.user_name)
        
        if not today_activities:
            messagebox.showinfo(
                AppConfig.APP_NAME,
                "No activities today! ✦\n\nComplete a timer to start tracking."
            )
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Today's Activities ✦")
        dialog.geometry("550x450")
        dialog.configure(bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        dialog.resizable(False, False)
        
        tk.Label(
            dialog,
            text=f"Today's Activities - {datetime.datetime.now().strftime('%B %d, %Y')}",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_primary"]
        ).pack(pady=(15, 5))
        
        tk.Label(
            dialog,
            text=f"Hello {self.user_name}! Here's what you've accomplished today:",
            font=("Segoe UI", 10),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_secondary"]
        ).pack(pady=(0, 10))
        
        # History listbox with scrollbar
        frame = tk.Frame(dialog, bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(
            frame, yscrollcommand=scrollbar.set,
            font=("Consolas", 11),
            bg=self.theme_manager.get_theme(self.current_theme)["entry_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["entry_fg"],
            selectbackground=self.theme_manager.get_theme(self.current_theme)["btn_primary"],
            relief="flat", bd=0, height=15
        )
        listbox.pack(fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        total_minutes = 0
        for activity in today_activities:
            display_text = f"  {activity['timestamp']}  |  {activity['activity']}  |  {activity['duration']}"
            listbox.insert(tk.END, display_text)
            total_minutes += activity.get("duration_minutes", 0)
        
        listbox.insert(tk.END, "")
        listbox.insert(tk.END, f"  {'='*50}")
        listbox.insert(tk.END, f"  Total Time: {total_minutes} minutes")
        listbox.insert(tk.END, f"  Total Sessions: {len(today_activities)}")
        
        tk.Button(
            dialog, text="Close", command=dialog.destroy,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["btn_primary"],
            fg="#3b0764", relief="flat", cursor="hand2",
            padx=20, pady=7
        ).pack(pady=15)
    
    def _show_weekly_summary(self) -> None:
        """Display weekly summary"""
        summary = self.data_manager.get_weekly_summary(self.user_name)
        
        if summary["total_sessions"] == 0:
            messagebox.showinfo(
                AppConfig.APP_NAME,
                "No activities this week! ✦\n\nComplete some timers to see your progress."
            )
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Weekly Summary ✦")
        dialog.geometry("500x450")
        dialog.configure(bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        dialog.resizable(False, False)
        
        tk.Label(
            dialog,
            text="Weekly Summary",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_primary"]
        ).pack(pady=(15, 5))
        
        tk.Label(
            dialog,
            text=f"Hello {self.user_name}! Here's your progress this week:",
            font=("Segoe UI", 10),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_secondary"]
        ).pack(pady=(0, 10))
        
        # Stats frame
        stats_frame = tk.Frame(dialog, bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        stats_frame.pack(pady=10)
        
        tk.Label(
            stats_frame,
            text=f"📊 Total Sessions: {summary['total_sessions']}",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_primary"]
        ).pack(anchor="w", padx=20, pady=2)
        
        tk.Label(
            stats_frame,
            text=f"⏱️ Total Time: {summary['total_minutes']} minutes ({summary['total_minutes']//60} hours {summary['total_minutes']%60} minutes)",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_primary"]
        ).pack(anchor="w", padx=20, pady=2)
        
        # Daily breakdown
        tk.Label(
            dialog,
            text="Daily Breakdown:",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Frame for listbox
        frame = tk.Frame(dialog, bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"])
        frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(
            frame, yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            bg=self.theme_manager.get_theme(self.current_theme)["entry_bg"],
            fg=self.theme_manager.get_theme(self.current_theme)["entry_fg"],
            selectbackground=self.theme_manager.get_theme(self.current_theme)["btn_primary"],
            relief="flat", bd=0, height=12
        )
        listbox.pack(fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Sort dates and display
        for date in sorted(summary["daily_data"].keys(), reverse=True):
            day_data = summary["daily_data"][date]
            display_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d")
            listbox.insert(tk.END, f"  {display_date}")
            listbox.insert(tk.END, f"     Sessions: {day_data['activities']}  |  Time: {day_data['total_minutes']} min")
            listbox.insert(tk.END, "")
        
        tk.Button(
            dialog, text="Close", command=dialog.destroy,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme_manager.get_theme(self.current_theme)["btn_primary"],
            fg="#3b0764", relief="flat", cursor="hand2",
            padx=20, pady=7
        ).pack(pady=15)
    
    # Dropdown Menu
    
    def _toggle_dropdown(self) -> None:
        """Toggle dropdown menu"""
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
            return
        
        self.dropdown = tk.Toplevel(self.root)
        self.dropdown.title("")
        self.dropdown.configure(
            bg=self.theme_manager.get_theme(self.current_theme)["frame_bg"],
            bd=1, highlightthickness=1,
            highlightbackground=self.theme_manager.get_theme(self.current_theme)["frame_border"]
        )
        self.dropdown.resizable(False, False)
        self.dropdown.overrideredirect(True)
        self.dropdown.attributes('-topmost', True)
        
        x = self.root.winfo_x() + 10
        y = self.root.winfo_y() + 50
        self.dropdown.geometry(f"200x90+{x}+{y}")
        
        items = [
            ("🎨 Change Theme", self._change_theme),
            ("➕ Create Task", self._create_custom_task),
        ]
        
        for text, command in items:
            btn = tk.Button(
                self.dropdown,
                text=text, command=lambda cmd=command: [cmd(), self._toggle_dropdown()],
                font=("Segoe UI", 10, "bold"),
                bg=self.theme_manager.get_theme(self.current_theme)["btn_accent"],
                fg=self.theme_manager.get_theme(self.current_theme)["btn_text"],
                activebackground="#a78bfa",
                relief="flat", cursor="hand2",
                anchor="w", padx=10, pady=8, bd=0
            )
            btn.pack(fill="x", padx=2, pady=2)
    
    # Utility Methods
    
    def _change_name(self) -> None:
        """Change user name"""
        new_name = simpledialog.askstring(
            "Change Name ✦",
            "What should I call you?",
            parent=self.root
        )
        if new_name and new_name.strip():
            self.user_name = new_name.strip()
            self.data_manager.save_user(self.user_name)
            self.name_lbl.config(text=f"Hi {self.user_name} ✦")
            self.canvas.itemconfig(self.title_text, text=f"Hello {self.user_name}! ✦")
            messagebox.showinfo(AppConfig.APP_NAME, f"Hi {self.user_name}! ✦")
    
    def _clear_placeholder(self, event=None) -> None:
        """Clear entry placeholder"""
        if self.minutes_entry.get() == self._placeholder_text:
            self.minutes_entry.delete(0, tk.END)
            self.minutes_entry.config(fg=self.theme_manager.get_theme(self.current_theme)["entry_fg"])
    
    def _restore_placeholder(self, event=None) -> None:
        """Restore entry placeholder"""
        if not self.minutes_entry.get().strip():
            self.minutes_entry.delete(0, tk.END)
            self.minutes_entry.insert(0, self._placeholder_text)
            self.minutes_entry.config(fg="#aaaaaa")
    
    def _animate(self) -> None:
        """Animation loop for UI elements"""
        self._animation_counter += 1
        self.root.after(50, self._animate)
    
    def _on_closing(self) -> None:
        """Handle application closing"""
        if self.timer_manager.is_running:
            self.timer_manager.stop()
        self.root.destroy()
    
    def run(self) -> None:
        """Run the application"""
        self.root.mainloop()


# Application Entry Point

def main():
    """Main entry point"""
    try:
        app = GentleTimeApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        messagebox.showerror(
            "Startup Error",
            f"Failed to start {AppConfig.APP_NAME}:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()