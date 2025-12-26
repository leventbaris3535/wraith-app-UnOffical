"""
Profile Port Watcher - Dark Tkinter GUI + Tray (Windows)

Save as: profile_port_watcher.py

Dependencies:
pip install psutil pillow pywin32 requests pystray

This variant: GUI strings and code are in English/Turkish. Adds tray-based language selection (English / Turkish).
Config file is stored next to the script/exe.
"""

import os
import sys
import json
import threading
import queue
import time
import logging
from pathlib import Path
from functools import partial

import requests
from PIL import Image, ImageTk, ImageDraw, ImageFont

import tkinter as tk
from tkinter import filedialog, messagebox

# Windows-specific imports
import psutil
import win32gui
import win32process
import win32con
import win32ui

# Tray
import pystray
from pystray import MenuItem as TrayItem, Menu as TrayMenu

# ---------------- Configuration ----------------
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "profile_port_watcher.json"

URL = "http://localhost:3000/control"
CHECK_INTERVAL = 0.25  # seconds
ICON_SIZE = 48
TRAY_ICON_SIZE = 64

PROFILE_PORTS = {1: "2s", 2: "3s", 3: "4s", 4: "5s"}
FALLBACK_PORT = "1s"

PROFILE_BTN_W = 340
PROFILE_BTN_H = 96

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------- Utilities ----------------
def safe_get_foreground_process():
    """Return (exe_name_lower, exe_full_path) for current foreground window, or (None, None)."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None, None
        proc = psutil.Process(pid)
        try:
            exe_path = proc.exe()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return None, None
        exe_name = os.path.basename(exe_path).lower()
        return exe_name, exe_path
    except Exception as e:
        logging.debug("safe_get_foreground_process error: %s", e)
        return None, None


def extract_icon_from_exe(path, size=ICON_SIZE):
    """Extract icon as RGBA PIL.Image from .exe using Win32 APIs. Returns fallback image on failure."""
    try:
        large, small = win32gui.ExtractIconEx(str(path), 0)
        hicon = None
        if small:
            hicon = small[0]
        elif large:
            hicon = large[0]

        if not hicon:
            raise RuntimeError("No icon handle")

        # create DCs and bitmap
        hdc_screen = win32gui.GetDC(0)
        hdc = win32ui.CreateDCFromHandle(hdc_screen)
        memdc = hdc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(hdc, size, size)
        memdc.SelectObject(bmp)

        # draw icon into memory DC
        win32gui.DrawIconEx(memdc.GetHandleOutput(), 0, 0, hicon, size, size, 0, None, win32con.DI_NORMAL)

        bmpinfo = bmp.GetInfo()
        bmp_str = bmp.GetBitmapBits(True)

        img = Image.frombuffer("RGBA", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmp_str, "raw", "BGRA", 0, 1)

        # cleanup handles
        try:
            win32gui.DestroyIcon(hicon)
        except Exception:
            pass
        try:
            memdc.DeleteDC()
            hdc.DeleteDC()
            win32gui.ReleaseDC(0, hdc_screen)
        except Exception:
            pass

        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        return img
    except Exception as e:
        logging.debug("extract_icon_from_exe failed (%s): %s", path, e)
        fallback = Image.new("RGBA", (size, size), (60, 60, 60, 255))
        draw = ImageDraw.Draw(fallback)
        draw.rectangle((6, 6, size - 6, size - 6), outline=(100, 100, 100), width=2)
        return fallback


def send_port_async(port):
    """Send POST to control URL in a background thread."""
    def _send():
        try:
            requests.post(URL, json={"port": port}, timeout=1.5)
            logging.info("POST sent: %s", port)
        except Exception as e:
            logging.warning("POST failed (%s): %s", port, e)
    threading.Thread(target=_send, daemon=True).start()


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning("Config load failed: %s", e)
    return {}


def save_config(data):
    try:
        # ensure directory exists (defensive)
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Config saved to %s", CONFIG_PATH)
    except Exception as e:
        logging.warning("Config save failed: %s", e)


# ---------------- Localization ----------------
LOCALES = {
    "en": {
        "app_title": "Profile Port Watcher",
        "status_stopped": "Status: Stopped",
        "status_running": "Status: Running",
        "last_sent": "Last sent port: {}",
        "start": "Start",
        "stop": "Stop",
        "assign_by_click": "Assign by click (5s)",
        "assign_by_exe": "Assign by .exe",
        "clear_assignment": "Clear assignment",
        "assigned": "Assigned: {}",
        "assigned_none": "Assigned: (none)",
        "assigned_ok": "{} assigned to profile {}.",
        "assign_failed": "No application detected.",
        "cleared": "Profile {} cleared.",
        "tray_toggle": "Show/Hide",
        "tray_open": "Open",
        "tray_exit": "Exit",
        "exit_confirm": "Do you want to exit the application?",
        "config_saved": "Config saved.",
        "hint": "Assign by click: click the target app within 5 seconds",
        "language_menu": "Language",
        "lang_en": "English",
        "lang_tr": "Türkçe"
    },
    "tr": {
        "app_title": "Profile Port Watcher",
        "status_stopped": "Durum: Durduruldu",
        "status_running": "Durum: Çalışıyor",
        "last_sent": "Son gönderilen port: {}",
        "start": "Başlat",
        "stop": "Durdur",
        "assign_by_click": "🖱 Click ile atama (5s)",
        "assign_by_exe": "📂 .exe ile atama",
        "clear_assignment": "Atamayı temizle",
        "assigned": "Atandı: {}",
        "assigned_none": "Atandı: (yok)",
        "assigned_ok": "{} profile {} olarak atandı.",
        "assign_failed": "Uygulama algılanamadı.",
        "cleared": "Profile {} temizlendi.",
        "tray_toggle": "Göster/Gizle",
        "tray_open": "Aç",
        "tray_exit": "Çıkış",
        "exit_confirm": "Uygulamadan çıkmak istiyor musunuz?",
        "config_saved": "Ayarlar kaydedildi.",
        "hint": "Butona tıkla → 'Assign by click' veya 'Assign by exe' seç. (Assign by click: hedef uygulamaya 5 saniye içinde tıkla)",
        "language_menu": "Dil",
        "lang_en": "English",
        "lang_tr": "Türkçe"
    }
}


# ---------------- Profile model ----------------
class ProfileModel:
    def __init__(self, idx):
        self.idx = idx
        self.exe_name = None
        self.exe_path = None
        self.icon_imgtk = None
        self._pil_icon = None

    def is_assigned(self):
        return bool(self.exe_name and self.exe_path)

    def assign(self, exe_name, exe_path):
        self.exe_name = exe_name.lower() if exe_name else None
        self.exe_path = exe_path
        try:
            self._pil_icon = extract_icon_from_exe(self.exe_path, size=ICON_SIZE)
        except Exception:
            self._pil_icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (60, 60, 60, 255))
        try:
            self.icon_imgtk = ImageTk.PhotoImage(self._pil_icon)
        except Exception:
            self.icon_imgtk = None

    def clear(self):
        self.exe_name = None
        self.exe_path = None
        self.icon_imgtk = None
        self._pil_icon = None

    def to_dict(self):
        return {"exe_name": self.exe_name, "exe_path": self.exe_path}

    @staticmethod
    def from_dict(idx, d):
        p = ProfileModel(idx)
        if d and "exe_path" in d and d["exe_path"]:
            try:
                p.assign(d.get("exe_name"), d.get("exe_path"))
            except Exception:
                p.exe_name = d.get("exe_name")
                p.exe_path = d.get("exe_path")
        return p


# ---------------- Main App ----------------
class ProfilePortWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("760x420")
        self.root.configure(bg="#111111")
        self.root.resizable(False, False)

        # defaults
        self.language = "en"
        self.profiles = {i: ProfileModel(i) for i in range(1, 5)}
        self._load_profiles_from_config()  # may override language and populate profiles

        # make sure window title reflects loaded language
        try:
            self.root.title(self.t("app_title"))
        except Exception:
            self.root.title(LOCALES["en"]["app_title"])

        # Queue & threads
        self.queue = queue.Queue()
        self.watcher_thread = None
        self.watcher_stop_event = threading.Event()

        # watcher cached state (fix for the crash)
        self._last_hwnd = None
        self._last_fg_exe = None

        # tray
        self.tray_icon = None
        self.tray_thread = None
        self.minimized_to_tray = False

        self._build_ui()
        try:
            self._start_tray()
        except Exception as e:
            logging.warning("Starting tray failed: %s", e)

        self.root.after(100, self._process_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_to_tray)

    # ---------- UI helpers ----------
    def t(self, key):
        return LOCALES.get(self.language, LOCALES["en"]).get(key, key)

    def _add_hover(self, widget, normal_bg, hover_bg):
        try:
            widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
            widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))
        except Exception:
            pass

    def _build_ui(self):
        # use a custom title bar (no native decorations) with only a close button
        try:
            self.root.overrideredirect(True)
        except Exception:
            # fallback: if it fails, continue with native decorations
            pass

        # draggable title bar
        title_bar = tk.Frame(self.root, bg="#0f0f0f", height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        # close button (only control on title bar)
        close_btn = tk.Button(title_bar, text='✕', command=self.on_close_full,
                              bg="#0f0f0f", fg="white", bd=0, relief="flat", padx=8, pady=2, cursor="hand2")
        close_btn.pack(side="right", padx=6, pady=3)
        try:
            self._add_hover(close_btn, "#0f0f0f", "#1b1b1b")
        except Exception:
            pass

        # allow dragging the window by the title bar
        def _start_move(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def _do_move(event):
            try:
                x = self.root.winfo_x() + (event.x - self._drag_x)
                y = self.root.winfo_y() + (event.y - self._drag_y)
                self.root.geometry(f"+{x}+{y}")
            except Exception:
                pass

        title_bar.bind("<ButtonPress-1>", _start_move)
        title_bar.bind("<B1-Motion>", _do_move)

        # main content below title bar
        content = tk.Frame(self.root, bg="#111111")
        content.pack(fill="both", expand=True)

        title = tk.Label(content, text=self.t("app_title"), font=("Segoe UI", 16, "bold"),
                         bg="#111111", fg="white")
        title.pack(pady=(12, 6))

        pf = tk.Frame(content, bg="#111111")
        pf.pack(padx=12, pady=6, fill="x")

        self.profile_buttons = {}
        for i in range(1, 5):
            container = tk.Frame(pf, bg="#1a1a1a", width=PROFILE_BTN_W, height=PROFILE_BTN_H)
            container.grid(row=(i - 1) // 2, column=(i - 1) % 2, padx=12, pady=12)
            container.grid_propagate(False)

            btn = tk.Button(container, command=partial(self._open_profile_menu, i),
                            bg="#1a1a1a", activebackground="#222", bd=0, relief="flat",
                            anchor="w", compound="left", cursor="hand2")
            btn.pack(expand=True, fill="both", padx=10, pady=10)
            # hover
            try:
                self._add_hover(btn, "#1a1a1a", "#262626")
            except Exception:
                pass

            self.profile_buttons[i] = btn
            self._refresh_profile_button(i)

        ctl = tk.Frame(content, bg="#111111")
        ctl.pack(fill="x", padx=12, pady=(6, 12))

        self.status_label = tk.Label(ctl, text=self.t("status_stopped"), bg="#111111", fg="#cccccc", anchor="w")
        self.status_label.pack(side="left")

        self.start_btn = tk.Button(ctl, text=self.t("start"), command=self.start_watcher,
                                   bg="#0b8043", fg="white", bd=0, padx=12, pady=6, cursor="hand2")
        self.start_btn.pack(side="right", padx=(6, 0))
        try:
            self._add_hover(self.start_btn, "#0b8043", "#0e8a4a")
        except Exception:
            pass

        self.stop_btn = tk.Button(ctl, text=self.t("stop"), command=self.stop_watcher,
                                  bg="#444444", fg="white", bd=0, padx=12, pady=6, state="disabled", cursor="hand2")
        self.stop_btn.pack(side="right")
        try:
            self._add_hover(self.stop_btn, "#444444", "#555555")
        except Exception:
            pass

        hint = tk.Label(content, text=self.t("hint"), font=("Segoe UI", 9), bg="#111111", fg="#888888", justify="center")
        hint.pack(pady=(4, 8))

    def _refresh_profile_button(self, idx):
        btn = self.profile_buttons[idx]
        pm = self.profiles[idx]
        if pm.is_assigned():
            txt = f"{pm.exe_name}\nProfile {idx}"
            if pm.icon_imgtk:
                btn.config(image=pm.icon_imgtk, text=txt, compound="left", anchor="w", padx=8, justify="left")
                btn.image = pm.icon_imgtk
            else:
                btn.config(image="", text=txt)
        else:
            placeholder = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (60, 60, 60, 255))
            draw = ImageDraw.Draw(placeholder)
            draw.rectangle((6, 6, ICON_SIZE - 6, ICON_SIZE - 6), outline=(100, 100, 100), width=2)
            try:
                imgtk = ImageTk.PhotoImage(placeholder)
            except Exception:
                imgtk = None
            btn.config(image=imgtk, text=f"Profile {idx}\n(empty)", compound="left", anchor="w", padx=8, justify="left")
            btn.image = imgtk

        btn.config(fg="white", font=("Segoe UI", 10, "bold"))
        btn.config(wraplength=PROFILE_BTN_W - ICON_SIZE - 40)

    def _open_profile_menu(self, idx):
        menu = tk.Toplevel(self.root)
        menu.title(f"Profile {idx} - Settings")
        menu.configure(bg="#121212")
        menu.resizable(False, False)
        menu.grab_set()

        lbl = tk.Label(menu, text=f"Profile {idx}", bg="#121212", fg="white", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=(8, 6), padx=12)

        btn_click = tk.Button(menu, text=self.t("assign_by_click"), width=28,
                              command=lambda: (menu.destroy(), self.assign_by_click(idx)), cursor="hand2")
        btn_click.pack(padx=12, pady=6)
        try:
            self._add_hover(btn_click, menu.cget('bg'), '#2a2a2a')
        except Exception:
            pass

        btn_file = tk.Button(menu, text=self.t("assign_by_exe"), width=28,
                             command=lambda: (menu.destroy(), self.assign_by_exe(idx)), cursor="hand2")
        btn_file.pack(padx=12, pady=6)
        try:
            self._add_hover(btn_file, menu.cget('bg'), '#2a2a2a')
        except Exception:
            pass

        btn_clear = tk.Button(menu, text=self.t("clear_assignment"), width=28,
                              command=lambda: (menu.destroy(), self.clear_profile(idx)), cursor="hand2")
        btn_clear.pack(padx=12, pady=6)
        try:
            self._add_hover(btn_clear, menu.cget('bg'), '#2a2a2a')
        except Exception:
            pass

        current = self.profiles[idx]
        ctext = self.t("assigned").format(current.exe_name) if current.is_assigned() else self.t("assigned_none")
        lblc = tk.Label(menu, text=ctext, bg="#121212", fg="#cccccc", font=("Segoe UI", 9))
        lblc.pack(pady=(6, 12))

        menu.transient(self.root)
        menu.update_idletasks()
        w = menu.winfo_width(); h = menu.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() - w)//2
        y = self.root.winfo_y() + (self.root.winfo_height() - h)//2
        menu.geometry(f"{w}x{h}+{x}+{y}")

    # ---------- assignments ----------
    def assign_by_exe(self, idx):
        path = filedialog.askopenfilename(filetypes=[("Windows Executable", "*.exe")])
        if not path:
            return
        exe_name = os.path.basename(path).lower()
        self.profiles[idx].assign(exe_name, path)
        self._refresh_profile_button(idx)
        self._save_profiles_to_config()
        messagebox.showinfo(self.t("app_title"), self.t("assigned_ok").format(exe_name, idx))

    def assign_by_click(self, idx):
        # NOTE: Do NOT grab the window here because we want the user to be able to switch to the target app.
        countdown = tk.Toplevel(self.root)
        countdown.title(self.t("assign_by_click"))
        countdown.configure(bg="#121212")
        countdown.resizable(False, False)
        # don't call grab_set() here

        label = tk.Label(countdown, text=self.t("assign_by_click") + "\n" + "Remaining: 5s", bg="#121212", fg="white", font=("Segoe UI", 12))
        label.pack(padx=18, pady=12)

        countdown.transient(self.root)
        countdown.update_idletasks()
        w = countdown.winfo_width(); h = countdown.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() - w)//2
        y = self.root.winfo_y() + (self.root.winfo_height() - h)//2
        countdown.geometry(f"{w}x{h}+{x}+{y}")

        start = time.time()

        def tick():
            rem = 5 - int(time.time() - start)
            if rem <= 0:
                label.config(text="Detected. Processing...")
                countdown.update()
                exe_name, exe_path = safe_get_foreground_process()
                if exe_name and exe_path:
                    self.profiles[idx].assign(exe_name, exe_path)
                    self._refresh_profile_button(idx)
                    self._save_profiles_to_config()
                    # show info on main thread
                    messagebox.showinfo(self.t("app_title"), self.t("assigned_ok").format(exe_name, idx))
                else:
                    messagebox.showerror(self.t("app_title"), self.t("assign_failed"))
                countdown.destroy()
                return
            else:
                label.config(text=self.t("assign_by_click") + f"\nRemaining: {rem}s")
                countdown.after(300, tick)

        tick()

    def clear_profile(self, idx):
        self.profiles[idx].clear()
        self._refresh_profile_button(idx)
        self._save_profiles_to_config()
        messagebox.showinfo(self.t("app_title"), self.t("cleared").format(idx))

    # ---------- watcher ----------
    def start_watcher(self):
        if self.watcher_thread and self.watcher_thread.is_alive():
            return
        self.watcher_stop_event.clear()
        self.watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
        self.watcher_thread.start()
        self.status_label.config(text=self.t("status_running"))
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        logging.info("Watcher started")

    def stop_watcher(self):
        if not (self.watcher_thread and self.watcher_thread.is_alive()):
            return
        self.watcher_stop_event.set()
        self.watcher_thread.join(timeout=1.0)
        self.status_label.config(text=self.t("status_stopped"))
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        logging.info("Watcher stopped")

    def _watcher_loop(self):
        """
        Optimized watcher loop:
        - Only resolves process exe when foreground window handle (HWND) changes.
        - Sends port only when changed.
        - Keeps a small sleep to avoid busy-waiting.
        This loop is hardened so exceptions inside the loop won't kill the thread.
        """
        last_sent = None
        while not self.watcher_stop_event.is_set():
            try:
                # Wrap a single iteration so unexpected exceptions will not stop the entire thread.
                try:
                    hwnd = win32gui.GetForegroundWindow()
                except Exception:
                    hwnd = None

                fg_exe = None
                # ensure cached attrs exist (defensive)
                if not hasattr(self, "_last_hwnd"):
                    self._last_hwnd = None
                if not hasattr(self, "_last_fg_exe"):
                    self._last_fg_exe = None

                if hwnd:
                    if hwnd != self._last_hwnd:
                        # window changed — resolve process once
                        self._last_hwnd = hwnd
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid:
                                proc = psutil.Process(pid)
                                try:
                                    exe_path = proc.exe()
                                    fg_exe = os.path.basename(exe_path).lower()
                                    self._last_fg_exe = fg_exe
                                except (psutil.AccessDenied, psutil.NoSuchProcess):
                                    fg_exe = None
                                    self._last_fg_exe = None
                            else:
                                fg_exe = None
                                self._last_fg_exe = None
                        except Exception:
                            fg_exe = None
                            self._last_fg_exe = None
                    else:
                        fg_exe = self._last_fg_exe
                else:
                    # no foreground window
                    self._last_hwnd = None
                    self._last_fg_exe = None

                selected_port = None
                if fg_exe:
                    for idx, pm in self.profiles.items():
                        if pm.is_assigned() and pm.exe_name == fg_exe:
                            selected_port = PROFILE_PORTS.get(idx)
                            break

                if selected_port:
                    if selected_port != last_sent:
                        logging.info("Detected profile for exe %s -> sending %s", fg_exe, selected_port)
                        send_port_async(selected_port)
                        last_sent = selected_port
                        # push status update
                        try:
                            self.queue.put(("status", self.t("last_sent").format(selected_port)))
                        except Exception:
                            pass
                else:
                    if last_sent != FALLBACK_PORT:
                        logging.info("No profile matched (fg=%s) -> sending fallback %s", fg_exe, FALLBACK_PORT)
                        send_port_async(FALLBACK_PORT)
                        last_sent = FALLBACK_PORT
                        try:
                            self.queue.put(("status", self.t("last_sent").format(FALLBACK_PORT)))
                        except Exception:
                            pass

                # small sleep — optimized but responsive
                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                # Log and continue; don't let the watcher thread die.
                logging.exception("Exception in watcher loop iteration: %s", e)
                try:
                    time.sleep(0.5)
                except Exception:
                    pass

    # ---------- config persistence ----------
    def _load_profiles_from_config(self):
        data = load_config()
        if not data:
            return
        # load language
        self.language = data.get("language", self.language)
        p = data.get("profiles", {})
        for i in range(1, 5):
            d = p.get(str(i))
            if d:
                try:
                    self.profiles[i] = ProfileModel.from_dict(i, d)
                except Exception as e:
                    logging.warning("Failed to load profile %s: %s", i, e)

    def _save_profiles_to_config(self):
        out = {"language": self.language, "profiles": {str(i): self.profiles[i].to_dict() for i in range(1, 5)}}
        save_config(out)

    # ---------- GUI queue ----------
    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "status":
                    self.status_label.config(text=item[1])
        except queue.Empty:
            pass
        self.root.after(150, self._process_queue)

    # ---------- tray integration ----------
    def _create_tray_image(self):
        img = Image.new("RGBA", (TRAY_ICON_SIZE, TRAY_ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, TRAY_ICON_SIZE-4, TRAY_ICON_SIZE-4), fill=(20, 20, 20, 255), outline=(80,80,80))
        try:
            fnt = ImageFont.load_default()
            w, h = draw.textsize("P", font=fnt)
            draw.text(((TRAY_ICON_SIZE-w)//2, (TRAY_ICON_SIZE-h)//2), "P", font=fnt, fill=(220,220,220))
        except Exception:
            draw.text((TRAY_ICON_SIZE//3, TRAY_ICON_SIZE//3), "P", fill=(220,220,220))
        return img

    def set_language(self, lang_code):
        if lang_code not in LOCALES:
            return
        self.language = lang_code
        try:
            self.root.title(self.t("app_title"))
        except Exception:
            pass
        # update small UI strings
        try:
            self.status_label.config(text=self.t("status_stopped"))
            self.start_btn.config(text=self.t("start"))
            self.stop_btn.config(text=self.t("stop"))
        except Exception:
            pass
        # update profile button labels
        for i in range(1,5):
            self._refresh_profile_button(i)
        self._save_profiles_to_config()
        logging.info("Language set to %s", lang_code)

    def _animate_show(self):
        # fade in window
        try:
            try:
                self.root.attributes('-alpha', 0.0)
            except Exception:
                pass
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            step = 0.08
            alpha = 0.0
            def _inc():
                nonlocal alpha
                alpha += step
                if alpha >= 1.0:
                    try:
                        self.root.attributes('-alpha', 1.0)
                    except Exception:
                        pass
                    return
                try:
                    self.root.attributes('-alpha', alpha)
                except Exception:
                    pass
                self.root.after(15, _inc)
            _inc()
            self.minimized_to_tray = False
            self.queue.put(("status", self.t("status_running") if (self.watcher_thread and self.watcher_thread.is_alive()) else self.t("status_stopped")))
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass

    def _animate_hide(self):
        # fade out then withdraw
        try:
            try:
                current_alpha = self.root.attributes('-alpha')
                alpha = float(current_alpha) if current_alpha is not None else 1.0
            except Exception:
                alpha = 1.0
            step = 0.08
            def _dec():
                nonlocal alpha
                alpha -= step
                if alpha <= 0.0:
                    try:
                        self.root.attributes('-alpha', 1.0)
                    except Exception:
                        pass
                    self.root.withdraw()
                    self.minimized_to_tray = True
                    self.queue.put(("status", self.t("status_stopped")))
                    return
                try:
                    self.root.attributes('-alpha', alpha)
                except Exception:
                    pass
                self.root.after(15, _dec)
            _dec()
        except Exception:
            try:
                self.root.withdraw()
            except Exception:
                pass

    def _toggle_from_tray(self):
        if self.minimized_to_tray or not self.root.winfo_viewable():
            self.root.after(0, self._animate_show)
        else:
            self.root.after(0, self._animate_hide)

    def _start_tray(self):
        if self.tray_icon:
            return
        img = self._create_tray_image()
        # build menu: first/default item toggles visibility on left-click (Windows)
        try:
            menu = TrayMenu(
                TrayItem(self.t("tray_toggle"), lambda icon, item: self.root.after(0, self._toggle_from_tray), default=True),
                TrayItem(self.t("tray_open"), lambda icon, item: self.root.after(0, self._restore_from_tray)),
                TrayItem(self.t("language_menu"), TrayMenu(
                    TrayItem(self.t("lang_en"), lambda icon, item: self.root.after(0, lambda: self.set_language("en")), checked=lambda item: self.language=="en"),
                    TrayItem(self.t("lang_tr"), lambda icon, item: self.root.after(0, lambda: self.set_language("tr")), checked=lambda item: self.language=="tr")
                )),
                TrayItem(self.t("tray_exit"), lambda icon, item: self.root.after(0, self._tray_exit)),
            )
            self.tray_icon = pystray.Icon("ProfilePortWatcher", img, self.t("app_title"), menu)
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            logging.info("Tray started (visible)")
        except Exception as e:
            logging.warning("Failed to start tray: %s", e)
            self.tray_icon = None

    def _stop_tray(self):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

    def _on_close_to_tray(self):
        self.root.withdraw()
        self.minimized_to_tray = True
        try:
            self._start_tray()
        except Exception:
            pass
        self.queue.put(("status", self.t("status_stopped")))

    def _restore_from_tray(self):
        try:
            def _do():
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.minimized_to_tray = False
                self.queue.put(("status", self.t("status_running") if (self.watcher_thread and self.watcher_thread.is_alive()) else self.t("status_stopped")))
            self.root.after(0, _do)
        except Exception as e:
            logging.warning("Restore from tray failed: %s", e)

    def _tray_exit(self):
        def _do_exit():
            if messagebox.askyesno(self.t("app_title"), self.t("exit_confirm")):
                self._shutdown()
        self.root.after(0, _do_exit)

    def _shutdown(self):
        logging.info("Shutting down...")
        self.watcher_stop_event.set()
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.watcher_thread.join(timeout=1.0)
        self._save_profiles_to_config()
        try:
            self._stop_tray()
        except Exception:
            pass
        self.root.destroy()

    def on_close_full(self):
        if messagebox.askyesno(self.t("app_title"), self.t("exit_confirm")):
            self._shutdown()


# ---------------- Run ----------------

def main():
    root = tk.Tk()
    app = ProfilePortWatcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
