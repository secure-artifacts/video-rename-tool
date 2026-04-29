#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频排贴命名工具 v1.0
专为 Facebook 资源视频排贴命名设计
依赖：pip install customtkinter
可选：pip install tkinterdnd2  （拖放）
      pip install pillow       （系统标题栏图标）
"""

# ── Windows DPI 修复（必须在 import tkinter 之前）─────────────────
import sys
import ctypes
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import re
import random
import string
import datetime
import calendar
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ════════════════════════════════════════════════════════════════
#  双主题配色系统
# ════════════════════════════════════════════════════════════════

THEMES = {
    "light": {
        "ctk_mode":   "Light",
        "BG":         "#F9F8F5",
        "CARD":       "#FFFFFF",
        "CARD2":      "#F3F1EC",
        "BORDER":     "#E2DDD6",
        "ACCENT":     "#C96442",
        "ACCENT2":    "#A84F33",
        "GREEN":      "#16A34A",
        "GREEN2":     "#15803D",
        "TEAL":       "#0D9488",
        "TEAL2":      "#0F766E",
        "TEXT":       "#1A1716",
        "TEXT2":      "#2E2825",
        "DIM":        "#78716C",
        "WARN":       "#D97706",
        "IC_DATE":    "#C96442", "IC_DATE_BG": "#FEF0EA",
        "IC_PPD":     "#2563EB", "IC_PPD_BG":  "#EEF3FF",
        "IC_TIME":    "#16A34A", "IC_TIME_BG": "#F0FDF4",
        "IC_RULE":    "#7C3AED", "IC_RULE_BG": "#F5F3FF",
        "TBTN_BG":    "#F0EDE8",
        "TBTN_BD":    "#D9D4CE",
        "TBTN_FG":    "#3D3530",
        "TOPBAR":     "#FFFFFF",
        "TOPBAR_BD":  "#E2DDD6",
        "TOPBAR_FG":  "#1A1716",
        "LB_BG":      "#FFFFFF",
        "LB_SEL":     "#F3F1EC",
    },
    "dark": {
        "ctk_mode":   "Dark",
        "BG":         "#0F0E0D",
        "CARD":       "#1C1917",
        "CARD2":      "#252220",
        "BORDER":     "#2C2825",
        "ACCENT":     "#C96442",
        "ACCENT2":    "#A84F33",
        "GREEN":      "#16A34A",
        "GREEN2":     "#15803D",
        "TEAL":       "#0D9488",
        "TEAL2":      "#0F766E",
        "TEXT":       "#F0EAE4",
        "TEXT2":      "#E0D8D2",
        "DIM":        "#6B6460",
        "WARN":       "#F59E0B",
        "IC_DATE":    "#E8906A", "IC_DATE_BG": "#3A2218",
        "IC_PPD":     "#60A5FA", "IC_PPD_BG":  "#1A2840",
        "IC_TIME":    "#4ADE80", "IC_TIME_BG": "#0F2A1A",
        "IC_RULE":    "#A78BFA", "IC_RULE_BG": "#241A38",
        "TBTN_BG":    "#2A2522",
        "TBTN_BD":    "#3A3330",
        "TBTN_FG":    "#C8BCB4",
        "TOPBAR":     "#1C1917",
        "TOPBAR_BD":  "#2C2825",
        "TOPBAR_FG":  "#F5EDE6",
        "LB_BG":      "#1C1917",
        "LB_SEL":     "#2C2825",
    },
}

_CURRENT = "light"

# 全局颜色变量（运行时由 _apply_theme 覆盖）
BG=CARD=CARD2=BORDER=ACCENT=ACCENT2=GREEN=GREEN2=TEAL=TEAL2=""
TEXT=TEXT2=DIM=WARN=""
IC_DATE=IC_PPD=IC_TIME=IC_RULE=""
IC_DATE_BG=IC_PPD_BG=IC_TIME_BG=IC_RULE_BG=""
TBTN_BG=TBTN_BD=TBTN_FG=TOPBAR=TOPBAR_BD=TOPBAR_FG=""
LB_BG=LB_SEL=""

# 图标 固定颜色（不随主题变化）
ICON_TEAL  = "#0F766E"
ICON_MID   = "#4BC4B8"
ICON_DARK  = "#2FA89E"
ICON_L1    = "#CFFAF8"
ICON_L2    = "#AEECEA"
ICON_L3    = "#8DE0DC"


def _apply_theme(mode: str = "light"):
    global _CURRENT
    _CURRENT = mode
    t = THEMES[mode]
    g = globals()
    for k, v in t.items():
        if k != "ctk_mode":
            g[k] = v
    ctk.set_appearance_mode(t["ctk_mode"])
    ctk.set_default_color_theme("blue")


_apply_theme("light")

# ── 常量 ─────────────────────────────────────────────────────────
CN_NUMS    = ['1','2','3','4','5','6','7','8']
VIDEO_EXTS = {'.mp4','.mov','.avi','.mkv','.flv','.wmv',
              '.m4v','.webm','.ts','.rmvb','.3gp','.mts'}
FC         = '：'


# ════════════════════════════════════════════════════════════════
#  工具函数
# ════════════════════════════════════════════════════════════════

def get_creation_time(p: Path) -> float:
    s = p.stat()
    return getattr(s, "st_birthtime", s.st_ctime)


def parse_hm(raw: str):
    raw = raw.strip().replace('：', ':')
    m = re.match(r'^(\d{1,2}):(\d{2})$', raw)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h, mi
    return 8, 0


def random_time(bh, bm, mn, mx):
    delta = random.randint(mn, mx) * random.choice([-1, 1])
    total = max(0, min(23*60+59, bh*60+bm+delta))
    return divmod(total, 60)


def distribute_times(n: int) -> list:
    if n <= 0: return []
    if n == 1: return [(13, 0)]
    s, e = 8*60, 22*60
    return [divmod(round(s + i*(e-s)/(n-1)), 60) for i in range(n)]


def date_add(month, day, offset):
    year = datetime.date.today().year
    try:
        d = datetime.date(year, month, day) + datetime.timedelta(days=offset)
        return d.month, d.day
    except Exception:
        return month, day


def _mix(h1: str, h2: str, r: float) -> str:
    c1 = [int(h1.lstrip('#')[i*2:i*2+2], 16) for i in range(3)]
    c2 = [int(h2.lstrip('#')[i*2:i*2+2], 16) for i in range(3)]
    return '#' + ''.join(f"{int(c1[i]+(c2[i]-c1[i])*r):02x}" for i in range(3))


# ════════════════════════════════════════════════════════════════
#  气泡 Toast
# ════════════════════════════════════════════════════════════════

def show_toast(root_widget, message: str, kind: str = "success",
               duration_ms: int = 2200):
    BG_MAP = {"success":"#16A34A", "warn":"#D97706", "error":"#DC2626"}
    SYM    = {"success":"✓", "warn":"!", "error":"✕"}
    bg     = BG_MAP.get(kind, "#16A34A")
    sym    = SYM.get(kind, "✓")

    toast = tk.Toplevel(root_widget)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=bg)

    outer = tk.Frame(toast, bg=bg)
    outer.pack(padx=1, pady=1)

    lighter = _mix(bg, "#FFFFFF", 0.30)
    IC = 22
    cv = tk.Canvas(outer, width=IC, height=IC, bg=bg, highlightthickness=0)
    cv.pack(side="left", padx=(22, 7), pady=11)
    cv.create_oval(1, 1, IC-1, IC-1, fill=lighter, outline="white", width=1)
    cv.create_text(IC//2, IC//2+1, text=sym, fill="white",
                   font=("Arial", 10, "bold"))

    tk.Label(outer, text=message, bg=bg, fg="white",
             font=("Microsoft YaHei UI", 12, "bold")).pack(
        side="left", padx=(0, 24), pady=11)

    toast.update_idletasks()
    tw = toast.winfo_reqwidth()
    th = toast.winfo_reqheight()
    try:
        rx = root_widget.winfo_rootx(); ry = root_widget.winfo_rooty()
        rw = root_widget.winfo_width(); rh = root_widget.winfo_height()
    except Exception:
        rx, ry, rw, rh = 100, 100, 900, 680
    toast.geometry(f"{tw}x{th}+{rx+max(0,(rw-tw)//2)}+{ry+int(rh*0.80)}")
    toast.attributes("-alpha", 0.0)

    def _fi(step=0):
        a = min(1.0, step*0.13)
        try:
            toast.attributes("-alpha", a)
            if a < 1.0: toast.after(16, _fi, step+1)
        except Exception: pass

    def _fo(step=9):
        a = max(0.0, step/9)
        try:
            toast.attributes("-alpha", a)
            if a > 0: toast.after(30, _fo, step-1)
            else: toast.destroy()
        except Exception: pass

    _fi()
    toast.after(duration_ms, _fo)


# ════════════════════════════════════════════════════════════════
#  区段图标绘制（Canvas，4 色系彩色图标）
# ════════════════════════════════════════════════════════════════

def _cv_rrect(cv, x1, y1, x2, y2, r, fill="", outline="", width=1):
    if fill:
        cv.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline="")
        cv.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline="")
        for (cx2, cy2) in [(x1+r,y1+r),(x2-r,y1+r),(x1+r,y2-r),(x2-r,y2-r)]:
            cv.create_oval(cx2-r, cy2-r, cx2+r, cy2+r, fill=fill, outline="")
    if outline:
        for (a1,e1,a2,e2) in [(90,90,None,None),(0,90,None,None),
                               (180,90,None,None),(270,90,None,None)]:
            pass
        # 简洁边框：只画四条线+四段弧
        cv.create_arc(x1,y1,x1+2*r,y1+2*r, start=90,extent=90,
                       style="arc", outline=outline, width=width)
        cv.create_arc(x2-2*r,y1,x2,y1+2*r, start=0,extent=90,
                       style="arc", outline=outline, width=width)
        cv.create_arc(x1,y2-2*r,x1+2*r,y2, start=180,extent=90,
                       style="arc", outline=outline, width=width)
        cv.create_arc(x2-2*r,y2-2*r,x2,y2, start=270,extent=90,
                       style="arc", outline=outline, width=width)
        cv.create_line(x1+r,y1,x2-r,y1, fill=outline, width=width)
        cv.create_line(x1+r,y2,x2-r,y2, fill=outline, width=width)
        cv.create_line(x1,y1+r,x1,y2-r, fill=outline, width=width)
        cv.create_line(x2,y1+r,x2,y2-r, fill=outline, width=width)


def _draw_sec_icon(cv: tk.Canvas, kind: str, S: int = 26):
    if kind == "date":
        c, bg = IC_DATE, IC_DATE_BG
        cv.configure(bg=bg)
        _cv_rrect(cv, 1, 3, S-1, S-1, 3, fill=bg, outline=c, width=1)
        # 顶部标题条
        cv.create_rectangle(1, 3, S-1, 9, fill=c, outline="")
        cv.create_rectangle(1, 7, S-1, 9, fill=c, outline="")
        # 两根柱
        for hx in (S//3+1, S*2//3):
            cv.create_rectangle(hx-1, 1, hx+1, 8, fill=c, outline="")
        # 小格子 2行×3列
        gw = max(2, (S-8)//3)
        for row in range(2):
            for col in range(3):
                gx = 4 + col*(gw+1)
                gy = 12 + row*6
                fc = c if not (row==1 and col==2) else _mix(c, bg, 0.5)
                cv.create_rectangle(gx, gy, gx+gw, gy+3, fill=fc, outline="")

    elif kind == "ppd":
        c, bg = IC_PPD, IC_PPD_BG
        cv.configure(bg=bg)
        base = S - 3
        bar_w = max(3, S//5)
        heights = [int(S*0.30), int(S*0.50), int(S*0.70)]
        xs = [3, S//2-bar_w//2, S-bar_w-2]
        for i, (bx, bh) in enumerate(zip(xs, heights)):
            ratio = 0.4 + 0.3*i
            fc = _mix(bg, c, ratio)
            cv.create_rectangle(bx, base-bh, bx+bar_w, base,
                                  fill=fc, outline=c, width=1)
        cv.create_line(2, base, S-2, base, fill=c, width=1)

    elif kind == "time":
        c, bg = IC_TIME, IC_TIME_BG
        cv.configure(bg=bg)
        cx = cy = S//2
        rd = S//2 - 2
        cv.create_oval(cx-rd, cy-rd, cx+rd, cy+rd,
                        fill=bg, outline=c, width=1)
        # 时针（短，朝上）
        cv.create_line(cx, cy, cx, cy-int(rd*0.52),
                        fill=c, width=2, capstyle="round")
        # 分针（长，朝右偏下）
        ang = math.radians(55)
        cv.create_line(cx, cy,
                        cx+int(rd*0.68*math.sin(ang)),
                        cy-int(rd*0.68*math.cos(ang)),
                        fill=c, width=2, capstyle="round")
        cv.create_oval(cx-2, cy-2, cx+2, cy+2, fill=c, outline="")

    elif kind == "rule":
        c, bg = IC_RULE, IC_RULE_BG
        cv.configure(bg=bg)
        # 后层纸
        _cv_rrect(cv, 5, 2, S-2, S-5, 3,
                   fill=_mix(bg, c, 0.22), outline=_mix(c, bg, 0.4), width=1)
        # 前层纸
        _cv_rrect(cv, 2, 5, S-5, S-1, 3,
                   fill=_mix(bg, c, 0.40), outline=c, width=1)
        # 内容线 ×3
        lx1, lx2 = 5, S-8
        for i, (ly, ratio, shrink) in enumerate(
                [(10, 0.90, 0), (15, 0.65, 3), (19, 0.40, 5)]):
            lc = _mix(bg, c, ratio)
            cv.create_line(lx1, ly, lx2-shrink, ly,
                            fill=lc, width=1, capstyle="round")


# ════════════════════════════════════════════════════════════════
#  图标 E（系统标题栏，PIL 生成，固定绿色）
# ════════════════════════════════════════════════════════════════

def _set_window_icon(root: tk.Tk):
    if not PIL_AVAILABLE:
        return
    try:
        size = 64
        img  = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0,0,size-1,size-1], radius=12,
                                fill=(15,118,110,255))
        dm=int(size*0.10); dx=dm; dy=int(size*0.20)
        dw=int(size*0.54); dh=int(size*0.64); fold=int(dw*0.30)
        draw.polygon([(dx,dy),(dx+dw-fold,dy),(dx+dw,dy+fold),
                       (dx+dw,dy+dh),(dx,dy+dh)],
                      fill=(75,196,184,220))
        draw.polygon([(dx+dw-fold,dy),(dx+dw,dy+fold),(dx+dw-fold,dy+fold)],
                      fill=(47,168,158,220))
        lx1=dx+int(dw*0.18); lx2=dx+int(dw*0.82)
        lb=dy+int(dh*0.40); gap=int(dh*0.17); lw=max(2,size//18)
        draw.line([(lx1,lb),(lx2,lb)], fill=(207,250,248,200), width=lw)
        draw.line([(lx1,lb+gap),(lx2-int(dw*0.18),lb+gap)],
                   fill=(174,236,234,180), width=lw)
        draw.line([(lx1,lb+gap*2),(lx2-int(dw*0.35),lb+gap*2)],
                   fill=(141,224,220,160), width=lw)
        tx=int(size*0.46); ty=int(size*0.03)
        tw=int(size*0.46); th=int(size*0.25); tail=int(size*0.13)
        draw.polygon([(tx,ty),(tx+tw,ty),(tx+tw,ty+th),
                       (tx+tw//2,ty+th+tail),(tx,ty+th)],
                      fill=(255,255,255,230))
        hr=max(2,size//14); hx=tx+int(tw*0.78); hy=ty+th//2
        draw.ellipse([hx-hr,hy-hr,hx+hr,hy+hr], fill=(15,118,110,255))
        draw.line([(tx+int(tw*0.12),hy),(tx+int(tw*0.56),hy)],
                   fill=(75,196,184,180), width=max(1,size//22))
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        root._icon_ref = photo   # 防 GC
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
#  冲突检测弹窗
# ════════════════════════════════════════════════════════════════

class ConflictDialog(ctk.CTkToplevel):
    def __init__(self, master, conflicts: list):
        super().__init__(master)
        self.title("发现文件名冲突")
        self.geometry("460x320")
        self.configure(fg_color=BG)
        self.resizable(False, False)
        self.grab_set()
        self.result = "cancel"

        ctk.CTkLabel(self, text=f"以下 {len(conflicts)} 个文件名已存在：",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=WARN).pack(padx=16, pady=(14,5), anchor="w")

        box = ctk.CTkTextbox(self, font=("Consolas", 11),
                              fg_color=CARD, text_color=TEXT,
                              corner_radius=8, border_width=1,
                              border_color=BORDER, height=140)
        box.pack(fill="x", padx=16, pady=(0,10))
        for name in conflicts[:25]:
            box.insert(tk.END, f"  {name}\n")
        if len(conflicts) > 25:
            box.insert(tk.END, f"  … 还有 {len(conflicts)-25} 个\n")
        box.configure(state="disabled")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0,14))
        ctk.CTkButton(btn_row, text="跳过冲突", width=108, height=34,
                       fg_color=CARD2, hover_color=BORDER,
                       border_width=1, border_color=BORDER,
                       text_color=TEXT, corner_radius=8,
                       font=ctk.CTkFont(size=12),
                       command=lambda: self._pick("skip")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="全部覆盖", width=108, height=34,
                       fg_color=WARN, hover_color="#c06010", corner_radius=8,
                       font=ctk.CTkFont(size=12),
                       command=lambda: self._pick("overwrite")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="取消", width=80, height=34,
                       fg_color=CARD, hover_color=CARD2,
                       border_width=1, border_color=BORDER,
                       text_color=DIM, corner_radius=8,
                       font=ctk.CTkFont(size=12),
                       command=lambda: self._pick("cancel")
                       ).pack(side="left", padx=4)

    def _pick(self, val):
        self.result = val
        self.destroy()


def two_pass_rename(pairs: list, strategy: str = "overwrite") -> tuple:
    tmp_pairs = []
    for old, new in pairs:
        dest  = old.parent / new
        final = dest if (strategy == "overwrite" or not dest.exists()) else None
        if final is None:
            tmp_pairs.append(None); continue
        while True:
            stem = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789",
                                           k=random.randint(4,10)))
            tmp  = old.parent / (stem + old.suffix.lower())
            if not tmp.exists(): break
        try:
            old.rename(tmp); tmp_pairs.append((tmp, final))
        except Exception as e:
            tmp_pairs.append(("err", str(e)))

    ok, skipped, fail = 0, 0, []
    for item in tmp_pairs:
        if item is None: skipped += 1; continue
        if item[0] == "err": fail.append(item[1]); continue
        tmp, final = item
        try:
            tmp.rename(final); ok += 1
        except Exception as e:
            fail.append(f"{final.name}: {e}")
            try: tmp.rename(tmp.parent / final.name)
            except Exception: pass
    return ok, skipped, fail


# ════════════════════════════════════════════════════════════════
#  日历弹窗
# ════════════════════════════════════════════════════════════════

class CalendarPopup(tk.Toplevel):
    def __init__(self, anchor, on_select, year=None, month=None, day=None):
        super().__init__(anchor)
        today   = datetime.date.today()
        self._y = year  or today.year
        self._m = month or today.month
        self._d = day   or today.day
        self._cb = on_select
        self._anchor = anchor
        self.overrideredirect(True)
        self.configure(bg=BORDER)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self._build()
        self._pos()
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _pos(self):
        self.update_idletasks()
        ax = self._anchor.winfo_rootx()
        ay = self._anchor.winfo_rooty() + self._anchor.winfo_height() + 4
        if ay + self.winfo_reqheight() > self.winfo_screenheight() - 40:
            ay = self._anchor.winfo_rooty() - self.winfo_reqheight() - 4
        self.geometry(f"+{ax}+{ay}")

    def _build(self):
        outer = tk.Frame(self, bg=BORDER, padx=1, pady=1); outer.pack()
        inner = tk.Frame(outer, bg=CARD); inner.pack()
        hdr   = tk.Frame(inner, bg=ACCENT); hdr.pack(fill="x")
        tk.Button(hdr, text=" ‹ ", bg=ACCENT, fg="#FFF", bd=0, relief="flat",
                  cursor="hand2", font=("Arial",12,"bold"),
                  activebackground=ACCENT2, command=self._prev).pack(side="left")
        self._lbl = tk.Label(hdr, text="", bg=ACCENT, fg="#FFF",
                              font=("Microsoft YaHei UI",11,"bold"), padx=10)
        self._lbl.pack(side="left", expand=True)
        tk.Button(hdr, text=" › ", bg=ACCENT, fg="#FFF", bd=0, relief="flat",
                  cursor="hand2", font=("Arial",12,"bold"),
                  activebackground=ACCENT2, command=self._next).pack(side="right")
        wk = tk.Frame(inner, bg=CARD2); wk.pack(fill="x")
        for d in ["一","二","三","四","五","六","日"]:
            tk.Label(wk, text=d, bg=CARD2, fg=DIM,
                     font=("Microsoft YaHei UI",9),
                     width=3, anchor="center").pack(side="left", padx=3, pady=3)
        self._gf = tk.Frame(inner, bg=CARD, padx=5, pady=5); self._gf.pack()
        self._render()

    def _render(self):
        for w in self._gf.winfo_children(): w.destroy()
        self._lbl.configure(text=f"{self._y} 年 {self._m} 月")
        for week in calendar.monthcalendar(self._y, self._m):
            row = tk.Frame(self._gf, bg=CARD); row.pack()
            for day in week:
                if day == 0:
                    tk.Label(row, text="", width=3, bg=CARD,
                             font=("Arial",10)).pack(side="left", padx=2, pady=2)
                else:
                    sel = (day == self._d)
                    tk.Button(row, text=str(day), width=3,
                               bg=ACCENT if sel else CARD,
                               fg="#FFF" if sel else TEXT,
                               activebackground=CARD2, bd=0, relief="flat",
                               cursor="hand2",
                               font=("Arial",10,"bold" if sel else "normal"),
                               command=lambda d=day: self._pick(d)
                               ).pack(side="left", padx=2, pady=2)

    def _prev(self):
        self._m -= 1
        if self._m < 1: self._m, self._y = 12, self._y-1
        self._render()

    def _next(self):
        self._m += 1
        if self._m > 12: self._m, self._y = 1, self._y+1
        self._render()

    def _pick(self, day):
        self._cb(self._y, self._m, day); self.destroy()


# ════════════════════════════════════════════════════════════════
#  文件列表组件
# ════════════════════════════════════════════════════════════════

class FileListWidget(ctk.CTkFrame):
    def __init__(self, master, file_exts: set, **kw):
        super().__init__(master, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=BORDER, **kw)
        self.file_exts = file_exts
        self.files: list = []
        self._build()

    def _build(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=7, pady=(7,3))
        ctk.CTkButton(bar, text="＋ 添加文件", width=96, height=28,
                       fg_color=ACCENT, hover_color=ACCENT2,
                       corner_radius=6, font=ctk.CTkFont(size=11),
                       command=self._pick).pack(side="left", padx=(0,5))
        ctk.CTkButton(bar, text="清空", width=48, height=28,
                       fg_color=CARD2, hover_color=BORDER,
                       border_width=1, border_color=BORDER,
                       text_color=DIM, corner_radius=6,
                       command=self._clear).pack(side="left")
        if DND_AVAILABLE:
            ctk.CTkLabel(bar, text="  ✦ 支持拖入", text_color=DIM,
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=3)
        self._cnt = ctk.CTkLabel(bar, text="0 个文件", text_color=TEAL,
                                  font=ctk.CTkFont(size=11, weight="bold"))
        self._cnt.pack(side="right")

        self.lb = tk.Listbox(self, bg=LB_BG, fg=TEXT,
                              selectbackground=LB_SEL, selectforeground=ACCENT,
                              font=("Consolas", 10), bd=0,
                              highlightthickness=0, relief="flat",
                              activestyle="none")
        sb = ctk.CTkScrollbar(self, command=self.lb.yview)
        self.lb.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0,3), pady=3)
        self.lb.pack(fill="both", expand=True, padx=(7,0), pady=(0,7))
        if DND_AVAILABLE:
            try:
                self.lb.drop_target_register(DND_FILES)
                self.lb.dnd_bind("<<Drop>>", self._drop)
            except Exception: pass

    def _pick(self):
        exts  = " ".join(f"*{e}" for e in self.file_exts)
        paths = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[("视频文件", exts), ("所有文件","*.*")])
        for p in paths: self._add(Path(p))

    def _drop(self, event):
        for a, b in re.findall(r'\{([^}]+)\}|(\S+)', event.data):
            p = a or b
            if p: self._add(Path(p))

    def _add(self, p: Path):
        if p.suffix.lower() in self.file_exts and p not in self.files:
            self.files.append(p)
            self.lb.insert(tk.END, "  " + p.name)
            self._cnt.configure(text=f"{len(self.files)} 个文件")

    def _clear(self):
        self.files.clear()
        self.lb.delete(0, tk.END)
        self._cnt.configure(text="0 个文件")

    def get_sorted(self) -> list:
        return sorted(self.files, key=get_creation_time)

    def clear(self): self._clear()


# ════════════════════════════════════════════════════════════════
#  预览弹窗
# ════════════════════════════════════════════════════════════════

class PreviewWindow(ctk.CTkToplevel):
    def __init__(self, master, pairs: list):
        super().__init__(master)
        self.title("命名预览")
        self.geometry("540x360")
        self.configure(fg_color=BG)
        self.grab_set()
        ctk.CTkLabel(self, text="📋  重命名预览",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=ACCENT).pack(pady=(12,5))
        box = ctk.CTkTextbox(self, font=("Consolas",11),
                              fg_color=CARD, text_color=TEXT,
                              corner_radius=8, border_width=1,
                              border_color=BORDER)
        box.pack(fill="both", expand=True, padx=14, pady=(0,14))
        for old, new in pairs:
            box.insert(tk.END, f"  {old.name}\n  → {new}\n\n")
        box.configure(state="disabled")


# ════════════════════════════════════════════════════════════════
#  主功能面板
# ════════════════════════════════════════════════════════════════

class PostNamingPanel(ctk.CTkFrame):

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        today          = datetime.date.today()
        self._sel_year = today.year
        self._sel_month= today.month
        self._sel_day  = today.day
        self._root_ref = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=35, minsize=255)
        self.grid_columnconfigure(1, weight=65)
        self.grid_rowconfigure(0, weight=1)

        # 左侧设置
        left = ctk.CTkScrollableFrame(
            self, fg_color=CARD, corner_radius=12,
            border_width=1, border_color=BORDER,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=CARD2)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,7))

        self._sec(left, "date",  "开始日期")
        self._build_date(left)
        self._sec(left, "ppd",   "每天发帖数量")
        self._build_ppd(left)
        self._sec(left, "time",  "发帖时间")
        self._build_time(left)
        self._sec(left, "rule",  "命名规则")
        self._build_options(left)

        # 右侧文件列表
        right = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12,
                              border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(right, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(11,4))
        ctk.CTkLabel(hdr, text="视频文件列表",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(hdr, text="mp4  mov  avi  mkv …",
                     text_color=DIM, font=ctk.CTkFont(size=10)).pack(side="right")

        self.file_list = FileListWidget(right, VIDEO_EXTS)
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,5))

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=2, column=0, pady=(0,12))
        ctk.CTkButton(btn_row, text="👁  预览", width=108, height=34,
                       fg_color=TEAL, hover_color=TEAL2, corner_radius=8,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._preview).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="🚀  开始重命名", width=136, height=34,
                       fg_color=ACCENT, hover_color=ACCENT2, corner_radius=8,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._execute).pack(side="left", padx=4)

    # ── 区段标题（图标 + 加粗深色字）────────────────────────────
    def _sec(self, parent, icon_kind: str, title: str):
        IC_SZ = 26
        bg_map = {"date":IC_DATE_BG,"ppd":IC_PPD_BG,
                   "time":IC_TIME_BG,"rule":IC_RULE_BG}
        ic_bg = bg_map.get(icon_kind, CARD2)

        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=10, pady=(13,4))

        # 图标 Canvas
        cv = tk.Canvas(row, width=IC_SZ, height=IC_SZ,
                        bg=CARD, highlightthickness=0)
        cv.pack(side="left", padx=(0,9))
        _cv_rrect(cv, 0, 0, IC_SZ, IC_SZ, 6, fill=ic_bg, outline="")
        _draw_sec_icon(cv, icon_kind, IC_SZ)

        tk.Label(row, text=title, bg=CARD, fg=TEXT2,
                  font=("Microsoft YaHei UI", 13, "bold"),
                  anchor="w").pack(side="left", fill="both", expand=True)

        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=10, pady=(0,5))

    # ── 日期 ──────────────────────────────────────────────────────
    def _build_date(self, p):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0,6))
        self._date_btn = ctk.CTkButton(
            row, text=f"  {self._sel_month:02d} 月 {self._sel_day:02d} 日",
            width=148, height=32, fg_color=CARD2, hover_color=BORDER,
            text_color=TEXT, corner_radius=8, border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=12), command=self._open_cal)
        self._date_btn.pack(side="left")
        ctk.CTkButton(row, text="今天", width=50, height=32,
                       fg_color=CARD, hover_color=CARD2,
                       text_color=DIM, corner_radius=8,
                       border_width=1, border_color=BORDER,
                       font=ctk.CTkFont(size=11),
                       command=self._reset_date).pack(side="left", padx=7)

    def _open_cal(self):
        CalendarPopup(self._date_btn, on_select=self._on_date,
                      year=self._sel_year, month=self._sel_month,
                      day=self._sel_day)

    def _on_date(self, y, m, d):
        self._sel_year, self._sel_month, self._sel_day = y, m, d
        self._date_btn.configure(text=f"  {m:02d} 月 {d:02d} 日")

    def _reset_date(self):
        t = datetime.date.today()
        self._on_date(t.year, t.month, t.day)

    # ── 每日发帖数 ────────────────────────────────────────────────
    def _build_ppd(self, p):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0,6))
        ctk.CTkLabel(row, text="每天发", text_color=DIM,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.ppd_var = tk.StringVar(value="3 贴")
        ctk.CTkOptionMenu(
            row, variable=self.ppd_var,
            values=[f"{i} 贴" for i in range(1,9)],
            width=88, height=30, fg_color=CARD2, button_color=ACCENT,
            button_hover_color=ACCENT2, text_color=TEXT,
            dropdown_fg_color=CARD2, dropdown_text_color=TEXT,
            dropdown_hover_color=BORDER, corner_radius=8,
            command=lambda _: self._refresh_slots()
        ).pack(side="left", padx=7)
        ctk.CTkLabel(row, text="自动分配时间",
                     text_color=DIM, font=ctk.CTkFont(size=10)).pack(side="left")

    # ── 发帖时间 ──────────────────────────────────────────────────
    def _build_time(self, p):
        vrow = ctk.CTkFrame(p, fg_color=CARD2, corner_radius=8)
        vrow.pack(fill="x", padx=10, pady=(0,7))
        ir = ctk.CTkFrame(vrow, fg_color="transparent")
        ir.pack(fill="x", padx=10, pady=7)
        ctk.CTkLabel(ir, text="随机波动", text_color=DIM,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.v_mn = ctk.CTkEntry(ir, width=42, height=26)
        self.v_mn.insert(0, "5")
        self.v_mn.pack(side="left", padx=(7,0))
        ctk.CTkLabel(ir, text=" ~ ", text_color=DIM).pack(side="left")
        self.v_mx = ctk.CTkEntry(ir, width=42, height=26)
        self.v_mx.insert(0, "20")
        self.v_mx.pack(side="left")
        ctk.CTkLabel(ir, text=" 分钟", text_color=DIM,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self.slots_wrap = ctk.CTkFrame(p, fg_color="transparent")
        self.slots_wrap.pack(fill="x", padx=10)
        self.time_entries = []
        self._refresh_slots()

    def _refresh_slots(self):
        for w in self.slots_wrap.winfo_children(): w.destroy()
        self.time_entries.clear()
        n     = int(self.ppd_var.get().split()[0])
        times = distribute_times(n)
        for i, (h, m) in enumerate(times):
            row = ctk.CTkFrame(self.slots_wrap, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"第 {CN_NUMS[i]} 帖",
                         text_color=ACCENT,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         width=48, anchor="e").pack(side="left")
            e = ctk.CTkEntry(row, width=66, height=26,
                              placeholder_text="HH:MM")
            e.insert(0, f"{h:02d}:{m:02d}")
            e.pack(side="left", padx=7)
            ctk.CTkLabel(row, text="24h制", text_color=DIM,
                         font=ctk.CTkFont(size=10)).pack(side="left")
            self.time_entries.append(e)

    # ── 命名规则 ──────────────────────────────────────────────────
    def _build_options(self, p):
        ctk.CTkLabel(p, text="文件排序方式", text_color=DIM,
                     font=ctk.CTkFont(size=11)).pack(
            anchor="w", padx=10, pady=(0,4))
        self.sort_var = tk.StringVar(value="按创建时间")
        sf = ctk.CTkFrame(p, fg_color="transparent")
        sf.pack(fill="x", padx=10, pady=(0,4))
        for val, tip in [("按创建时间","按文件创建时间先后排序"),
                          ("随机打乱","随机打乱顺序")]:
            ctk.CTkRadioButton(sf, text=val, variable=self.sort_var, value=val,
                                fg_color=ACCENT, hover_color=ACCENT2,
                                font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)
            ctk.CTkLabel(sf, text=f"    {tip}", text_color=DIM,
                         font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0,2))
        ctk.CTkFrame(p, height=1, fg_color=BORDER).pack(
            fill="x", padx=10, pady=(5,7))
        ctk.CTkLabel(p, text="命名格式示例：",
                     text_color=DIM, font=ctk.CTkFont(size=11)).pack(
            anchor="w", padx=10, pady=(0,2))
        ctk.CTkLabel(p, text="  0420-第 1 帖-08：36.mp4",
                     text_color=ACCENT,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     justify="left").pack(anchor="w", padx=10, pady=(0,12))

    # ── 逻辑 ──────────────────────────────────────────────────────
    def _toast(self, msg, kind="success"):
        if self._root_ref:
            show_toast(self._root_ref, msg, kind)

    def _get_params(self):
        try:
            ppd = int(self.ppd_var.get().split()[0])
            mn  = int(self.v_mn.get())
            mx  = int(self.v_mx.get())
            if mn > mx: mn, mx = mx, mn
        except Exception:
            self._toast("波动分钟数填写有误", "error")
            return None
        return self._sel_month, self._sel_day, ppd, mn, mx

    def _compute(self):
        p = self._get_params()
        if not p: return []
        month, day, ppd, mn, mx = p
        if self.sort_var.get() == "随机打乱":
            files = self.file_list.files[:]
            random.shuffle(files)
        else:
            files = self.file_list.get_sorted()
        if not files:
            self._toast("请先添加视频文件", "warn")
            return []
        slots  = [parse_hm(e.get()) for e in self.time_entries]
        result = []
        offset = 0
        for idx, f in enumerate(files):
            si = idx % ppd
            if idx > 0 and si == 0: offset += 1
            m, d  = date_add(month, day, offset)
            pfx   = f"{m:02d}{d:02d}"
            cn    = CN_NUMS[si]
            if si < len(slots):
                rh, rm = random_time(*slots[si], mn, mx)
                stem = f"{pfx}-第 {cn} 帖-{rh:02d}{FC}{rm:02d}"
            else:
                stem = f"{pfx}-第 {cn} 帖"
            result.append((f, stem + f.suffix.lower()))
        return result

    def _preview(self):
        pairs = self._compute()
        if pairs: PreviewWindow(self, pairs)

    def _execute(self):
        pairs = self._compute()
        if not pairs: return
        if not messagebox.askyesno("确认重命名",
                                    f"即将重命名 {len(pairs)} 个文件，确认继续？"):
            return
        conflicts = [new for old, new in pairs if (old.parent/new).exists()]
        strategy  = "overwrite"
        if conflicts:
            dlg = ConflictDialog(self, conflicts)
            self.wait_window(dlg)
            strategy = dlg.result
            if strategy == "cancel": return
        ok, skipped, fail = two_pass_rename(pairs, strategy)
        self.file_list.clear()
        msg = f" 成功重命名 {ok} 个视频文件"
        if skipped: msg += f"（跳过 {skipped} 个）"
        if fail:
            self._toast(f"部分失败：{len(fail)} 个文件未重命名", "error")
            messagebox.showerror("部分失败",
                f"成功 {ok} 个，失败 {len(fail)} 个\n\n"+"\n".join(fail[:8]))
        else:
            self._toast(msg, "success")


# ════════════════════════════════════════════════════════════════
#  主应用 v1.0
# ════════════════════════════════════════════════════════════════

class App:

    def __init__(self):
        root_cls  = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk
        self.root = root_cls()
        self.root.title("视频排贴命名工具  v1.0")
        self.root.minsize(780, 500)
        _set_window_icon(self.root)
        self._build()

    def _build(self):
        root = self.root
        root.configure(bg=BG)
        # 清空旧 layout
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # ── 顶部栏 ──────────────────────────────────────────────
        topbar = tk.Frame(root, bg=TOPBAR, height=48)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.pack_propagate(False)

        # 软件名 + 主题图标（紧跟标题后，完全不受右侧约束影响）
        left_row = tk.Frame(topbar, bg=TOPBAR)
        left_row.pack(side="left", fill="y", padx=(20, 0))

        tk.Label(left_row, text="视频排贴命名工具",
                  bg=TOPBAR, fg=TOPBAR_FG,
                  font=("Microsoft YaHei UI", 14, "bold"),
                  anchor="w").pack(side="left", fill="y")

        # 两格间距
        tk.Frame(left_row, bg=TOPBAR, width=12).pack(side="left")

        # 主题图标按钮（26×26 圆角块，紧跟标题）
        IC_BTN = 26
        tbtn = tk.Frame(left_row, bg=TBTN_BG,
                         highlightbackground=TBTN_BD, highlightthickness=1)
        tbtn.pack(side="left", anchor="c")

        self._tic = tk.Canvas(tbtn, width=IC_BTN, height=IC_BTN,
                               bg=TBTN_BG, highlightthickness=0, cursor="hand2")
        self._tic.pack(padx=4, pady=4)
        self._refresh_tbtn()

        for w in (tbtn, self._tic):
            w.bind("<Button-1>", lambda e: self._toggle_theme())

        # 版本徽章（右侧）
        ver_btn = tk.Label(topbar, text="  v 1.0  ",
                            bg=ACCENT, fg="#FFF",
                            font=("Consolas", 9, "bold"), cursor="hand2")
        ver_btn.pack(side="right", padx=14, pady=14)
        ver_btn.bind("<Button-1>", lambda e: self._show_changelog())
        ver_btn.bind("<Enter>",    lambda e: ver_btn.configure(bg=ACCENT2))
        ver_btn.bind("<Leave>",    lambda e: ver_btn.configure(bg=ACCENT))

        # 顶部分隔线
        tk.Frame(root, bg=TOPBAR_BD, height=1).grid(
            row=0, column=0, sticky="sew")

        # ── 内容区 ──────────────────────────────────────────────
        content = tk.Frame(root, bg=BG)
        content.grid(row=1, column=0, sticky="nsew", padx=13, pady=13)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        panel = PostNamingPanel(content)
        panel._root_ref = self.root
        panel.grid(row=0, column=0, sticky="nsew")

        if DND_AVAILABLE:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", lambda e: None)
            except Exception: pass

    def _refresh_tbtn(self):
        """更新主题图标（26×26，月牙/太阳，无文字）"""
        cv = self._tic
        cv.configure(bg=TBTN_BG)
        cv.delete("all")
        c = TBTN_FG
        if _CURRENT == "light":
            # 月牙：用多边形近似，确保完整显示在 26×26 内
            # 大圆填充扇形
            cv.create_arc(4, 4, 22, 22, start=50, extent=220,
                           fill=c, outline="", style="chord")
            # 遮罩圆（同背景色）挖出月牙效果
            cv.create_oval(9, 3, 23, 17, fill=TBTN_BG, outline=TBTN_BG)
        else:
            # 太阳：中心圆 + 8 条射线，全部在 26×26 内
            cx, cy = 13, 13
            cv.create_oval(cx-4, cy-4, cx+4, cy+4, fill=c, outline="")
            for i in range(8):
                a = math.radians(i * 45)
                x1 = cx + 6.5*math.cos(a)
                y1 = cy - 6.5*math.sin(a)
                x2 = cx + 9.5*math.cos(a)
                y2 = cy - 9.5*math.sin(a)
                cv.create_line(x1, y1, x2, y2,
                                fill=c, width=2, capstyle="round")

    def _toggle_theme(self):
        new = "dark" if _CURRENT == "light" else "light"
        _apply_theme(new)
        for w in self.root.winfo_children():
            w.destroy()
        self._build()

    def _show_changelog(self):
        win = tk.Toplevel(self.root)
        win.title("更新日志")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        ctk.CTkLabel(win, text="更新日志",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=ACCENT).pack(padx=24, pady=(16,4), anchor="w")
        ctk.CTkFrame(win, height=1, fg_color=BORDER).pack(
            fill="x", padx=24, pady=(0,10))
        CHANGELOG = [("v1.0  —  当前版本", ACCENT, [
            "全新独立发布：视频排贴命名工具 · 专为 FB 视频排贴命名设计",
            "专为 Facebook 资源视频排贴设计，按日期 + 帖次 + 时间自动命名",
            "支持自定义每日发帖数（1 ~ 8 贴）及随机时间波动范围",
            "内置日历选择器，精准控制起始发布日期",
            "支持按文件创建时间排序 / 随机打乱两种模式",
            "两步重命名机制，彻底解决文件名碰撞问题",
            "全新气泡提醒系统，替代传统弹窗，体验更流畅",
            "亮色 / 暗色双主题，一键切换",
        ])]
        scroll = ctk.CTkScrollableFrame(win, fg_color=CARD,
                                         width=400, height=210,
                                         scrollbar_button_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0,8))
        for ver, color, items in CHANGELOG:
            ctk.CTkLabel(scroll, text=ver,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color).pack(anchor="w", padx=6, pady=(10,4))
            for item in items:
                ctk.CTkLabel(scroll, text=f"  · {item}",
                             font=ctk.CTkFont(size=11), text_color=TEXT,
                             justify="left", wraplength=375,
                             anchor="w").pack(anchor="w", padx=6, pady=2)
        ctk.CTkButton(win, text="关闭", width=90, height=30,
                       fg_color=CARD2, hover_color=BORDER,
                       border_width=1, border_color=BORDER,
                       text_color=DIM, corner_radius=8,
                       font=ctk.CTkFont(size=12),
                       command=win.destroy).pack(pady=(4,14))
        win.update_idletasks()
        x = self.root.winfo_x()+(self.root.winfo_width()-win.winfo_width())//2
        y = self.root.winfo_y()+(self.root.winfo_height()-win.winfo_height())//2
        win.geometry(f"+{x}+{y}")

    def run(self):
        self.root.geometry("1000x1030")
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
