import tkinter as tk
from tkinter import messagebox, simpledialog
import time, threading, random, math, datetime, os
import wave, struct, io, audioop, tempfile, platform

# ── sound engine (pure stdlib) ────────────────────────────────────────────────

def _make_sine_wav(freq: float, duration: float, volume: float = 0.45,
                   sample_rate: int = 44100) -> bytes:
    """Return raw bytes of a 16-bit mono WAV for a sine tone."""
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            # simple exponential decay envelope
            env = math.exp(-3.0 * i / n_samples)
            val = int(volume * env * 32767 *
                      math.sin(2 * math.pi * freq * i / sample_rate))
            wf.writeframesraw(struct.pack("<h", val))
    return buf.getvalue()


def _make_multi_tone_wav(freqs_durs, volume=0.45, sample_rate=44100) -> bytes:
    """Concatenate several sine tones into one WAV."""
    segments = []
    for freq, dur in freqs_durs:
        data = _make_sine_wav(freq, dur, volume, sample_rate)
        # extract raw PCM from the WAV bytes
        with wave.open(io.BytesIO(data)) as wf:
            segments.append(wf.readframes(wf.getnframes()))
    combined = b"".join(segments)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(combined)
    return buf.getvalue()


def _play_wav_bytes(wav_bytes: bytes):
    """Play WAV bytes cross-platform using only stdlib."""
    sys_name = platform.system()
    # Write to a temp file then play
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tf.write(wav_bytes)
        tmp_path = tf.name
    try:
        if sys_name == "Windows":
            import winsound
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
        elif sys_name == "Darwin":   # macOS
            os.system(f'afplay "{tmp_path}" &')
        else:                        # Linux / other
            # try aplay, then paplay, then sox play
            for cmd in [f'aplay -q "{tmp_path}"',
                        f'paplay "{tmp_path}"',
                        f'play -q "{tmp_path}"']:
                if os.system(cmd + " 2>/dev/null") == 0:
                    break
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def play_sound(kind: str):
    """Play a distinct bell sound for each timer type (non-blocking)."""
    def _play():
        try:
            # ── Study: clean school-bell two-tone ding ──────────────────────
            if kind == "study":
                wav = _make_multi_tone_wav([
                    (880, 0.18), (1046, 0.22), (880, 0.12), (1046, 0.35)
                ], volume=0.5)

            # ── Eye rest: soft single chime (low, gentle) ───────────────────
            elif kind == "eye_rest":
                wav = _make_multi_tone_wav([
                    (523, 0.55)      # middle C — one soft ding
                ], volume=0.35)

            # ── Nap: gentle lullaby-style descending tones ──────────────────
            elif kind == "nap":
                wav = _make_multi_tone_wav([
                    (659, 0.25), (587, 0.25), (523, 0.25), (494, 0.5)
                ], volume=0.4)

            # ── Exercise: energetic ascending fanfare ────────────────────────
            elif kind == "exercise":
                wav = _make_multi_tone_wav([
                    (523, 0.12), (659, 0.12), (784, 0.12),
                    (1047, 0.18), (784, 0.10), (1047, 0.30)
                ], volume=0.55)

            # ── Custom: triple soft ding ─────────────────────────────────────
            else:
                wav = _make_multi_tone_wav([
                    (740, 0.18), (740, 0.18), (740, 0.30)
                ], volume=0.4)

            _play_wav_bytes(wav)
        except Exception:
            pass   # sound is best-effort; never crash the app

    threading.Thread(target=_play, daemon=True).start()


# ── persistence helpers ───────────────────────────────────────────────────────

HISTORY_FILE = "gentletime_history.txt"
NAME_FILE    = "gentletime_user.txt"

def load_name():
    if os.path.exists(NAME_FILE):
        n = open(NAME_FILE, encoding="utf-8").read().strip()
        if n:
            return n
    return None

def save_name(n):
    open(NAME_FILE, "w", encoding="utf-8").write(n.strip())

def log_activity(user, act, dur):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}]  {user}  |  {act}  |  {dur}\n")


# ── root & user name ──────────────────────────────────────────────────────────

root = tk.Tk()
root.title("GentleTime ✦")
root.geometry("480x670")
root.resizable(False, False)

saved = load_name()
if saved:
    USER = saved
else:
    root.withdraw()
    ans = simpledialog.askstring("GentleTime ✦",
        "Hey there! What's your name?  (saved for next time)", parent=root)
    root.deiconify()
    USER = ans.strip() if ans and ans.strip() else "Friend"
    save_name(USER)

W, H = 480, 670

# ── canvas & gradient ─────────────────────────────────────────────────────────

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="#e8e0f8")
canvas.place(x=0, y=0)

GRAD = [
    (0.0, (180, 165, 240)),
    (0.5, (200, 185, 248)),
    (1.0, (220, 210, 255)),
]

def lerp(a, b, t):
    return int(a + (b - a) * t)

def grad_col(ratio):
    for i in range(len(GRAD) - 1):
        r0, c0 = GRAD[i]; r1, c1 = GRAD[i + 1]
        if ratio <= r1:
            t = (ratio - r0) / (r1 - r0)
            return "#{:02x}{:02x}{:02x}".format(
                lerp(c0[0], c1[0], t),
                lerp(c0[1], c1[1], t),
                lerp(c0[2], c1[2], t))
    return "#c8c0f0"

for y in range(H):
    canvas.create_line(0, y, W, y, fill=grad_col(y / H))

# ground
canvas.create_rectangle(0, H - 42, W, H,      fill="#9b8fd4", outline="")
canvas.create_rectangle(0, H - 44, W, H - 40, fill="#b0a0e0", outline="")

for _ in range(22):
    gx = random.randint(5, W - 5)
    gy = H - 44
    for j in range(3):
        dx = random.randint(-5, 5)
        gh = random.randint(6, 14)
        canvas.create_line(gx + dx, gy,
                           gx + dx + random.randint(-3, 3), gy - gh,
                           fill="#7060b8", width=2, capstyle="round")

for _ in range(18):
    px = random.randint(5, W - 5)
    py = random.randint(H - 38, H - 6)
    pr = random.randint(3, 7)
    col = random.choice(["#c3b1e1", "#a78bfa", "#93c5fd", "#bfdbfe", "#ddd6fe"])
    canvas.create_oval(px - pr, py - pr // 2, px + pr, py + pr // 2,
                       fill=col, outline="")

for r in range(5):
    lx = random.randint(40, W - 40)
    pts = [lx - 6, 0, lx + 6, 0, lx + 35, H - 42, lx - 35, H - 42]
    canvas.create_polygon(pts, fill="#ffffff", stipple="gray12", outline="")

# clouds
def draw_cloud(cx, cy, size, col="#eeeaff"):
    for dx, dy, r in [
        (0, 0, size), (size, -size // 3, int(size * 0.8)),
        (-size, -size // 4, int(size * 0.75)),
        (int(size * 1.6), size // 4, int(size * 0.65)),
        (-int(size * 1.5), size // 4, int(size * 0.6)),
    ]:
        canvas.create_oval(cx + dx - r, cy + dy - r,
                           cx + dx + r, cy + dy + r,
                           fill=col, outline="")

draw_cloud(60,  60,  22, "#e8e4ff")
draw_cloud(200, 38,  18, "#ddd8ff")
draw_cloud(370, 70,  25, "#eae6ff")
draw_cloud(420, 30,  14, "#e0dcff")

# flowers
FLOWER_COLS = [
    ("#a78bfa", "#c4b5fd"),
    ("#60a5fa", "#93c5fd"),
    ("#818cf8", "#a5b4fc"),
    ("#c084fc", "#d8b4fe"),
    ("#38bdf8", "#7dd3fc"),
]

flowers = []
for k in range(10):
    fx    = random.randint(15, W - 15)
    fh    = random.randint(45, 85)
    segs  = random.randint(4, 7)
    bc, fc = random.choice(FLOWER_COLS)
    phase  = random.uniform(0, math.pi * 2)
    speed  = random.uniform(0.018, 0.035)

    pts = []
    for s in range(segs + 1):
        frac = s / segs
        pts.extend([fx, H - 42 - int(fh * frac)])
    pid = canvas.create_line(pts, fill="#7060b8", width=random.randint(2, 4),
                             smooth=True, joinstyle="round", capstyle="round")

    head_ids = []
    bx, by = fx, H - 42 - fh
    for angle_d in range(0, 360, 60):
        ang = math.radians(angle_d)
        ox  = int(math.cos(ang) * 7)
        oy  = int(math.sin(ang) * 5)
        pid2 = canvas.create_oval(bx + ox - 5, by + oy - 4,
                                  bx + ox + 5, by + oy + 4,
                                  fill=fc, outline="")
        head_ids.append(pid2)
    centre = canvas.create_oval(bx - 5, by - 5, bx + 5, by + 5,
                                fill=bc, outline="")
    head_ids.append(centre)

    flowers.append({"id": pid, "fx": fx, "fh": fh, "segs": segs,
                    "phase": phase, "speed": speed, "head_ids": head_ids})

def sway_flowers(t):
    for fl in flowers:
        angle = math.sin(t * fl["speed"] * 60 + fl["phase"]) * 0.22
        pts   = []
        for s in range(fl["segs"] + 1):
            frac = s / fl["segs"]
            ox   = math.sin(angle * frac * 2) * 14 * frac
            pts.extend([int(fl["fx"] + ox), H - 42 - int(fl["fh"] * frac)])
        canvas.coords(fl["id"], pts)
        ox_tip = math.sin(angle * 2) * 14
        bx = int(fl["fx"] + ox_tip)
        by = H - 42 - fl["fh"]
        for i, hid in enumerate(fl["head_ids"][:-1]):
            ang = math.radians(i * 60)
            px  = bx + int(math.cos(ang) * 7)
            py  = by + int(math.sin(ang) * 5)
            canvas.coords(hid, px - 5, py - 4, px + 5, py + 4)
        canvas.coords(fl["head_ids"][-1], bx - 5, by - 5, bx + 5, by + 5)

# sparkles
SPARKLE_COUNT  = 14
SPARKLE_GLYPHS = ["♦", "✦", "✿", "★", "✩", "♣"]
sparkles = []

for _ in range(SPARKLE_COUNT):
    sx  = random.randint(10, W - 10)
    sy  = float(random.randint(50, H - 50))
    spd = random.uniform(0.3, 0.9)
    wob = random.uniform(0.02, 0.05)
    wob_phase = random.uniform(0, math.pi * 2)
    col = random.choice(["#a78bfa", "#60a5fa", "#818cf8",
                         "#c084fc", "#38bdf8", "#93c5fd"])
    glyph = random.choice(SPARKLE_GLYPHS)
    sid   = canvas.create_text(sx, int(sy), text=glyph,
                               font=("Arial", random.randint(9, 16)),
                               fill=col)
    sparkles.append({"x": float(sx), "y": sy, "spd": spd,
                     "wob": wob, "wob_phase": wob_phase, "id": sid})

def move_sparkles(_t):
    for sp in sparkles:
        sp["y"]         -= sp["spd"]
        sp["wob_phase"] += sp["wob"]
        ox = math.sin(sp["wob_phase"]) * 7
        canvas.coords(sp["id"], int(sp["x"] + ox), int(sp["y"]))
        if sp["y"] < -20:
            sp["y"] = float(H - 42)
            sp["x"] = float(random.randint(10, W - 10))

# animals
ANIMAL_DATA = [
    ("bunny", "#c4b5fd", "#a78bfa", 30,  280, 1.0,  1),
    ("bunny", "#bfdbfe", "#93c5fd", 420, 350, 0.85, -1),
    ("bird",  "#ddd6fe", "#818cf8", 200, 200, 1.3,  1),
    ("bird",  "#bae6fd", "#38bdf8", 100, 160, 1.0, -1),
    ("bunny", "#e9d5ff", "#c084fc", 350, 420, 0.9,  1),
    ("bird",  "#a5b4fc", "#6366f1",  50, 440, 0.75, -1),
]

def make_bunny(cx, cy, s, d, bcol, ccol, tail_phase):
    shapes = []
    bob = math.sin(tail_phase * 0.5) * 3
    shapes.append(("oval",
        [cx - int(14*s), cy - int(10*s) + bob,
         cx + int(14*s), cy + int(12*s) + bob],
        {"fill": bcol, "outline": "#8070c0", "width": 1}))
    hx = cx + d * int(14*s)
    shapes.append(("oval",
        [hx - int(10*s), cy - int(11*s) + bob,
         hx + int(10*s), cy + int(7*s)  + bob],
        {"fill": bcol, "outline": "#8070c0", "width": 1}))
    for ex_off in (-4, 4):
        ex = hx + int(ex_off * s)
        shapes.append(("oval",
            [ex - int(3*s), cy - int(22*s) + bob,
             ex + int(3*s), cy - int(11*s) + bob],
            {"fill": bcol, "outline": "#8070c0", "width": 1}))
        shapes.append(("oval",
            [ex - int(1.5*s), cy - int(20*s) + bob,
             ex + int(1.5*s), cy - int(12*s) + bob],
            {"fill": "#a78bfa", "outline": ""}))
    shapes.append(("oval",
        [hx + d*int(3*s) - int(4*s), cy - int(3*s) + bob,
         hx + d*int(3*s) + int(4*s), cy + int(2*s) + bob],
        {"fill": ccol, "outline": ""}))
    ex2 = hx + d * int(5*s)
    shapes.append(("oval",
        [ex2 - int(2*s), cy - int(6*s) + bob,
         ex2 + int(2*s), cy - int(2*s) + bob],
        {"fill": "#1e1b4b", "outline": ""}))
    shapes.append(("oval",
        [ex2 - int(0.8*s), cy - int(6*s) + bob,
         ex2 + int(0.8*s), cy - int(4.5*s) + bob],
        {"fill": "white", "outline": ""}))
    tx = cx - d * int(14*s)
    shapes.append(("oval",
        [tx - int(5*s), cy + int(2*s) + bob,
         tx + int(5*s), cy + int(10*s) + bob],
        {"fill": "white", "outline": ""}))
    return shapes

def make_bird(cx, cy, s, d, bcol, ccol, tail_phase):
    shapes = []
    wing_flap = math.sin(tail_phase) * 6 * s
    shapes.append(("oval",
        [cx - int(12*s), cy - int(8*s),
         cx + int(12*s), cy + int(8*s)],
        {"fill": bcol, "outline": ""}))
    hx = cx + d * int(12*s)
    shapes.append(("oval",
        [hx - int(8*s), cy - int(9*s),
         hx + int(8*s), cy + int(5*s)],
        {"fill": bcol, "outline": ""}))
    wx = cx - d * int(2*s)
    shapes.append(("polygon",
        [wx, cy,
         wx - d * int(14*s), cy - int(wing_flap),
         wx - d * int(8*s),  cy + int(6*s)],
        {"fill": ccol, "outline": ""}))
    bx = hx + d * int(8*s)
    shapes.append(("polygon",
        [bx, cy - int(2*s),
         bx + d * int(6*s), cy,
         bx, cy + int(2*s)],
        {"fill": "#f59e0b", "outline": ""}))
    ex = hx + d * int(4*s)
    shapes.append(("oval",
        [ex - int(2*s), cy - int(4*s),
         ex + int(2*s), cy],
        {"fill": "#1e1b4b", "outline": ""}))
    shapes.append(("oval",
        [ex - int(0.8*s), cy - int(4*s),
         ex + int(0.8*s), cy - int(2.5*s)],
        {"fill": "white", "outline": ""}))
    shapes.append(("oval",
        [hx - int(2*s), cy - int(1*s),
         hx + int(4*s), cy + int(4*s)],
        {"fill": ccol, "outline": ""}))
    return shapes

animal_state = []
for (kind, bc, cc, sx, sy, sp, di) in ANIMAL_DATA:
    animal_state.append({
        "kind": kind,
        "x": float(sx), "y": float(sy),
        "speed": sp, "dir": di,
        "scale": random.uniform(0.85, 1.15),
        "bcol": bc, "ccol": cc,
        "tail_phase": random.uniform(0, math.pi * 2),
        "bob_phase":  random.uniform(0, math.pi * 2),
        "ids": [],
    })

def draw_shapes(shapes):
    ids = []
    for (kind, coords, kw) in shapes:
        c = [int(round(v)) for v in coords]
        if kind == "oval":
            ids.append(canvas.create_oval(*c, **kw))
        elif kind == "polygon":
            ids.append(canvas.create_polygon(*c, **kw))
    return ids

def move_animals():
    for a in animal_state:
        for pid in a["ids"]:
            try: canvas.delete(pid)
            except Exception: pass
        a["tail_phase"] += 0.10
        a["bob_phase"]  += 0.035
        a["x"] += a["speed"] * a["dir"]
        bob_y = math.sin(a["bob_phase"]) * 4
        if a["dir"] == 1  and a["x"] >  W + 70:
            a["x"] = -70.0
            a["y"] = float(random.randint(120, H - 120))
        elif a["dir"] == -1 and a["x"] < -70:
            a["x"] = float(W + 70)
            a["y"] = float(random.randint(120, H - 120))
        cx = a["x"]; cy = a["y"] + bob_y
        s  = a["scale"]
        if a["kind"] == "bunny":
            shapes = make_bunny(cx, cy, s, a["dir"], a["bcol"], a["ccol"], a["tail_phase"])
        else:
            shapes = make_bird(cx, cy, s, a["dir"], a["bcol"], a["ccol"], a["tail_phase"])
        a["ids"] = draw_shapes(shapes)

# mushrooms
MUSHROOM_COLS = [
    ("#a78bfa", "#ddd6fe"),
    ("#60a5fa", "#bfdbfe"),
    ("#818cf8", "#c7d2fe"),
    ("#c084fc", "#e9d5ff"),
    ("#6366f1", "#a5b4fc"),
]

def draw_mushroom(cx, by, cap_col, spot_col):
    stem_h = random.randint(14, 26)
    cap_r  = random.randint(14, 26)
    canvas.create_rectangle(cx - 5, by - stem_h, cx + 5, by,
                             fill="#d8d0f0", outline="")
    canvas.create_oval(cx - cap_r, by - stem_h - cap_r,
                       cx + cap_r, by - stem_h + cap_r // 2,
                       fill=cap_col, outline="")
    for _ in range(3):
        sx = cx + random.randint(-cap_r // 2, cap_r // 2)
        sy = by - stem_h - random.randint(4, cap_r // 2)
        r  = random.randint(3, 6)
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                           fill=spot_col, outline="")

for _ in range(9):
    cx  = random.randint(20, W - 20)
    cap, spot = random.choice(MUSHROOM_COLS)
    draw_mushroom(cx, H - 42, cap, spot)

# title (created once, kept as IDs for tag_raise later)
canvas.create_text(242, 32, text="✦  GentleTime  ✦",
    font=("Comic Sans MS", 18, "bold"), fill="#5b21b6")
canvas.create_text(240, 30, text="✦  GentleTime  ✦",
    font=("Comic Sans MS", 18, "bold"), fill="#7c3aed")
title_sub = canvas.create_text(240, 54,
    text=f"Hello {USER}!  Your cosy daily helper  ♦",
    font=("Comic Sans MS", 10, "italic"), fill="#6d28d9")

# ── UI frame ──────────────────────────────────────────────────────────────────

frame = tk.Frame(root, bg="#f0ecff", bd=0,
                 highlightbackground="#a78bfa", highlightthickness=2)
# FIX: use canvas.create_window so we get a proper canvas-item id for tag_raise
frame_window_id = canvas.create_window(36, 80, anchor="nw",
                                       window=frame, width=408, height=562)

name_row = tk.Frame(frame, bg="#f0ecff")
name_row.pack(pady=(14, 0))

name_lbl = tk.Label(name_row, text=f"Hi  {USER}  ✦",
                    font=("Comic Sans MS", 12, "bold"),
                    bg="#f0ecff", fg="#5b21b6")
name_lbl.pack(side="left", padx=(0, 10))

def change_name():
    global USER
    new_name = simpledialog.askstring("Change Name ✦",
        "What should I call you?", parent=root)
    if new_name and new_name.strip():
        USER = new_name.strip()
        save_name(USER)
        name_lbl.config(text=f"Hi  {USER}  ✦")
        canvas.itemconfig(title_sub,
            text=f"Hello {USER}!  Your cosy daily helper  ♦")
        messagebox.showinfo("GentleTime ✦", f"Saved as  '{USER}'  ✦")

tk.Button(name_row, text="change name",
          font=("Comic Sans MS", 8), bg="#ddd6fe", fg="#5b21b6",
          relief="flat", bd=0, cursor="hand2",
          activebackground="#c4b5fd",
          command=change_name).pack(side="left")

timer_lbl = tk.Label(frame, text="00:00",
                     font=("Courier New", 50, "bold"),
                     bg="#f0ecff", fg="#7c3aed")
timer_lbl.pack(pady=(10, 2))

status_lbl = tk.Label(frame, text="Choose a timer below  ✦",
                      font=("Comic Sans MS", 9, "italic"),
                      bg="#f0ecff", fg="#6d28d9")
status_lbl.pack()

PLACEHOLDER = "enter minutes  (study / custom)"
entry_var = tk.StringVar(value=PLACEHOLDER)
entry = tk.Entry(frame, textvariable=entry_var,
                 font=("Comic Sans MS", 11), justify="center",
                 width=26, bg="#ede9fe", fg="#aaaaaa",
                 insertbackground="#7c3aed",
                 relief="flat",
                 highlightbackground="#a78bfa", highlightthickness=1)
entry.pack(pady=(10, 4))

def clear_ph(_e):
    if entry_var.get() == PLACEHOLDER:
        entry_var.set(""); entry.config(fg="#4c1d95")

def restore_ph(_e):
    if not entry_var.get().strip():
        entry_var.set(PLACEHOLDER); entry.config(fg="#aaaaaa")

entry.bind("<FocusIn>",  clear_ph)
entry.bind("<FocusOut>", restore_ph)

# ── timer state ───────────────────────────────────────────────────────────────

_stop_evt      = threading.Event()
_pause_evt     = threading.Event()   # NEW: set = paused, clear = running
_timer_running = [False]
_current_sound = [None]              # track which sound kind to play at end

def countdown(seconds, name, msg, sound_kind):
    _stop_evt.clear()
    _pause_evt.clear()
    start = seconds
    try:
        while seconds > 0 and not _stop_evt.is_set():
            # ── pause: block here until resumed or stopped ──
            while _pause_evt.is_set() and not _stop_evt.is_set():
                time.sleep(0.1)
            if _stop_evt.is_set():
                break

            m, s = divmod(seconds, 60)
            timer_lbl.config(text=f"{m:02d}:{s:02d}")
            status_lbl.config(text=f"{name}  in progress  ✦")
            time.sleep(1)
            seconds -= 1

        if not _stop_evt.is_set():
            timer_lbl.config(text="00:00")
            status_lbl.config(text="Done!  You did amazing!  ✿")
            dur = f"{start//60} min" if start >= 60 else f"{start} sec"
            log_activity(USER, name, dur)
            play_sound(sound_kind)                # ← distinct bell per timer
            messagebox.showinfo("GentleTime ✦", f"Hey {USER}!\n{msg}")
            status_lbl.config(text="Choose a timer below  ✦")
        else:
            timer_lbl.config(text="00:00")
            status_lbl.config(text="Timer stopped.  Choose again  ✦")
    finally:
        _timer_running[0] = False
        _pause_evt.clear()
        pause_btn.config(text="Pause  ⏸")       # reset button label

def start_timer(seconds, name, msg, sound_kind="custom"):
    if _timer_running[0]:
        messagebox.showwarning("GentleTime ✦",
            "A timer is already running!\n\nPress  Stop  first, then pick a new one  ✦")
        return
    _timer_running[0] = True
    _current_sound[0] = sound_kind
    pause_btn.config(text="Pause  ⏸")
    threading.Thread(target=countdown,
                     args=(seconds, name, msg, sound_kind), daemon=True).start()

def stop_timer():
    if _timer_running[0]:
        _pause_evt.clear()           # un-pause so thread can see stop
        _stop_evt.set()
        pause_btn.config(text="Pause  ⏸")
    else:
        status_lbl.config(text="Nothing running right now  ✦")

# ── NEW: pause / resume ───────────────────────────────────────────────────────

def toggle_pause():
    if not _timer_running[0]:
        status_lbl.config(text="No timer running  ✦")
        return
    if _pause_evt.is_set():
        # currently paused → resume
        _pause_evt.clear()
        pause_btn.config(text="Pause  ⏸")
        status_lbl.config(text="Resumed  ✦")
    else:
        # currently running → pause
        _pause_evt.set()
        pause_btn.config(text="Resume  ▶")
        status_lbl.config(text="Paused  ✦  Press Resume to continue")

# ── timer launchers ───────────────────────────────────────────────────────────

def get_mins():
    v = entry_var.get().strip()
    m = int(v)
    if m <= 0: raise ValueError
    return m

def study_timer():
    try:
        start_timer(get_mins() * 60, "Study Time",
                    "Study session done!  ✿\nRest those eyes now  ✦",
                    sound_kind="study")
    except (ValueError, TypeError):
        messagebox.showerror("Oops ✦", "Please enter valid minutes!")

def eye_rest():
    start_timer(20, "Eye Rest",
                "Eye rest complete!  ✿\nContinue when ready  ✦",
                sound_kind="eye_rest")

def nap_timer():
    start_timer(20 * 60, "Nap Time",
                "Wake up, sunshine!  ✿\nYou slept so well  ✦",
                sound_kind="nap")

def exercise_timer():
    start_timer(30 * 60, "Exercise",
                "Exercise done!  ✿\nYou are amazing!  ✦",
                sound_kind="exercise")

def custom_timer():
    try:
        m = get_mins()
        start_timer(m * 60, "Custom Timer",
                    f"{m}-minute timer done!  ✿\nWell done, {USER}!  ✦",
                    sound_kind="custom")
    except (ValueError, TypeError):
        messagebox.showerror("Oops ✦", "Please enter valid minutes!")

def show_history():
    if not os.path.exists(HISTORY_FILE):
        messagebox.showinfo("GentleTime ✦",
            "No history yet!  ✦\nComplete a timer to start tracking."); return
    content = open(HISTORY_FILE, encoding="utf-8").read().strip()
    if not content:
        messagebox.showinfo("GentleTime ✦", "No history yet!  ✦"); return
    win = tk.Toplevel(root)
    win.title("Activity History  ✦")
    win.geometry("530x400")
    win.configure(bg="#f0ecff")
    win.resizable(False, False)
    tk.Label(win, text="Activity History  ✦",
             font=("Comic Sans MS", 14, "bold"),
             bg="#f0ecff", fg="#5b21b6").pack(pady=(14, 4))
    frm = tk.Frame(win, bg="#f0ecff"); frm.pack(fill="both", expand=True, padx=14, pady=6)
    sc  = tk.Scrollbar(frm); sc.pack(side="right", fill="y")
    lb  = tk.Listbox(frm, yscrollcommand=sc.set,
                     font=("Courier New", 10), bg="#ede9fe",
                     fg="#4c1d95", selectbackground="#c4b5fd",
                     relief="flat", bd=0, highlightthickness=1,
                     highlightbackground="#a78bfa")
    lb.pack(fill="both", expand=True)
    sc.config(command=lb.yview)
    for line in reversed(content.split("\n")):
        if line.strip(): lb.insert(tk.END, "  " + line)
    tk.Button(win, text="Close  ✦", font=("Comic Sans MS", 10),
              bg="#c4b5fd", fg="#3b0764", relief="flat",
              activebackground="#a78bfa",
              command=win.destroy, cursor="hand2").pack(pady=10)

# ── buttons ───────────────────────────────────────────────────────────────────

def mkbtn(parent, text, cmd, bg, fg="#3b0764", w=26, pad=7):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Comic Sans MS", 10, "bold"),
                     bg=bg, fg=fg,
                     activebackground="#a78bfa", activeforeground="#1e1b4b",
                     relief="flat", bd=0, cursor="hand2",
                     width=w, pady=pad)

bf = tk.Frame(frame, bg="#f0ecff"); bf.pack(pady=(10, 0))

mkbtn(bf, "📚  Study Timer",          study_timer,    "#c4b5fd").pack(pady=3)
mkbtn(bf, "👁  Eye Rest  (20 sec)",   eye_rest,       "#bfdbfe", fg="#1e3a5f").pack(pady=3)
mkbtn(bf, "🌙  Nap Timer  (20 min)",  nap_timer,      "#ddd6fe").pack(pady=3)
mkbtn(bf, "🌸  Exercise  (30 min)",   exercise_timer, "#a5f3fc", fg="#164e63").pack(pady=3)
mkbtn(bf, "✨  Custom Timer",         custom_timer,   "#e9d5ff").pack(pady=3)
bot = tk.Frame(frame, bg="#f0ecff"); bot.pack(pady=(12, 14))
mkbtn(bot, "Stop",    stop_timer,    "#c4b5fd", w=9).pack(side="left", padx=3)
# NEW: Pause/Resume button — same style as the others, sits between Stop & History
pause_btn = tk.Button(bot, text="Pause  ⏸", command=toggle_pause,
                      font=("Comic Sans MS", 10, "bold"),
                      bg="#ddd6fe", fg="#3b0764",
                      activebackground="#a78bfa", activeforeground="#1e1b4b",
                      relief="flat", bd=0, cursor="hand2",
                      width=10, pady=7)
pause_btn.pack(side="left", padx=3)
mkbtn(bot, "History", show_history,  "#93c5fd", fg="#1e3a5f", w=9).pack(side="left", padx=3)
mkbtn(bot, "Exit",    root.destroy,  "#fca5a5", fg="#7f1d1d", w=9).pack(side="left", padx=3)

# ── animation loop ────────────────────────────────────────────────────────────

_tick = [0]

def animate():
    _tick[0] += 1
    t = _tick[0]
    move_animals()
    move_sparkles(t)
    sway_flowers(t)
    if t % 30 == 0:
        # FIX: raise the canvas window item (frame_window_id), not the Frame widget
        canvas.tag_raise(frame_window_id)
        canvas.tag_raise(title_sub)
    root.after(50, animate)

root.after(100, animate)
root.mainloop()