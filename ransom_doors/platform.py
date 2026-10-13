"""Кроссплатформенная прослойка: детект композитора, курсор, мониторы.

Hyprland-специфичное раньше было размазано по коду:
  utils.pick_monitor -> `hyprctl monitors -j`
  idle._hypr_pos     -> `hyprctl cursorpos`
  app._setup_window  -> GtkLayerShell без фолбэка (нет на GNOME/KDE/COSMIC)
  wallpaper          -> только `awww`
  sound              -> ffplay/paplay без pw-play/aplay

Здесь — одна точка детекта + цепочки фолбэков. Всё с таймаутами
и без падений: неизвестный композитор = GDK-фолбэк.
"""
import json
import os
import shutil
import subprocess


def detect_compositor():
    """Имя композитора/DE маленькими буквами: hyprland, sway, kde, gnome..."""
    for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"):
        v = (os.environ.get(var) or "").lower()
        for name in ("hyprland", "sway", "kde", "plasma", "gnome",
                     "cosmic", "labwc", "wayfire", "niri", "river",
                     "weston", "mutter", "kwin", "xfce", "i3"):
            if name in v:
                if name == "plasma":
                    return "kde"
                return name
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    if os.environ.get("SWAYSOCK"):
        return "sway"
    if os.environ.get("KDE_SESSION_VERSION"):
        return "kde"
    if os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        return "gnome"
    sess = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    return sess or "unknown"


def layershell_wanted():
    """GtkLayerShell имеет смысл только на wlr-композиторах.

    На GNOME (Mutter), KDE (KWin), COSMIC layer-shell для оверлеев
    либо отсутствует, либо ведёт себя иначе — там лучше обычный
    fullscreen-поверх-всех. Список wlr-friendly держим явно.
    """
    comp = detect_compositor()
    if comp in ("gnome", "mutter", "kde", "kwin", "plasma", "cosmic", "xfce"):
        return False
    return True


def layershell_available():
    """Есть ли биндинг GtkLayerShell в системе (gi)."""
    try:
        import gi
        gi.require_version('GtkLayerShell', '0.1')
        from gi.repository import GtkLayerShell  # noqa: F401
        return True
    except Exception:
        return False


def use_layershell():
    return layershell_wanted() and layershell_available()


# ---------- курсор: глобальная позиция ----------

def _hypr_pos():
    if shutil.which("hyprctl") is None:
        return None
    try:
        r = subprocess.run(["hyprctl", "cursorpos"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode != 0:
            return None
        x, y = r.stdout.strip().split(",")
        return (int(x.strip()), int(y.strip()))
    except Exception:
        return None


def _sway_pos():
    """Sway: `swaymsg -t get_seats` отдаёт JSON, координаты курсора
    лежат в разных версиях по-разному — ищем рекурсивно пару x/y
    рядом с ключами cursor/seat. Не нашли — None (не ошибка)."""
    if shutil.which("swaymsg") is None:
        return None
    try:
        r = subprocess.run(["swaymsg", "-t", "get_seats"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout or "null")
    except Exception:
        return None
    best = None

    def walk(o):
        nonlocal best
        if isinstance(o, dict):
            keys = set(o.keys())
            if {"x", "y"} <= keys:
                try:
                    best = (int(o["x"]), int(o["y"]))
                except Exception:
                    pass
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    try:
        walk(data)
    except Exception:
        pass
    return best


def _xdotool_pos():
    """X11 / XWayland запасной вариант."""
    if shutil.which("xdotool") is None:
        return None
    try:
        r = subprocess.run(["xdotool", "getmouselocation", "--shell"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode != 0:
            return None
        x = y = None
        for line in r.stdout.splitlines():
            if line.startswith("X="):
                x = int(line[2:])
            elif line.startswith("Y="):
                y = int(line[2:])
        if x is not None and y is not None:
            return (x, y)
    except Exception:
        pass
    return None


def _wlrctl_pos():
    # wlrctl читать позицию не умеет — место под будущий бэкенд.
    return None


def get_cursor_pos():
    """Глобальная позиция курсора или None.

    Порядок: hyprctl (Hyprland) -> swaymsg (Sway) -> xdotool (X11) -> None.
    Вызывать из фонового потока: каждый вызов — это spawn (~мс).
    """
    for fn in (_hypr_pos, _sway_pos, _xdotool_pos, _wlrctl_pos):
        try:
            pos = fn()
        except Exception:
            pos = None
        if pos is not None:
            return pos
    return None


def cursor_backend_name():
    """Имя рабочего бэкенда курсора для логов ('hyprctl'/'swaymsg'/.../'gdk')."""
    if shutil.which("hyprctl") is not None and _hypr_pos() is not None:
        return "hyprctl"
    if shutil.which("swaymsg") is not None and _sway_pos() is not None:
        return "swaymsg"
    if shutil.which("xdotool") is not None and _xdotool_pos() is not None:
        return "xdotool"
    return "gdk"


# ---------- мониторы: геометрия фокусного ----------

def _hypr_focused_geom():
    if shutil.which("hyprctl") is None:
        return None
    try:
        mons = json.loads(subprocess.check_output(
            ["hyprctl", "monitors", "-j"], timeout=3).decode())
        foc = next((m for m in mons if m.get("focused")), None)
        if foc is not None:
            want = (foc.get("x"), foc.get("y"),
                    foc.get("width"), foc.get("height"))
            if None not in want:
                return tuple(want)
    except Exception:
        pass
    return None


def _sway_focused_geom():
    """Sway: фокусный вывод = тот, у которого focused=True в get_outputs,
    либо active workspace. Возвращает (x, y, w, h) в координатах Sway
    (rect.x/rect.y/rect.width/rect.height)."""
    if shutil.which("swaymsg") is None:
        return None
    try:
        r = subprocess.run(["swaymsg", "-t", "get_outputs"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode != 0:
            return None
        outs = json.loads(r.stdout or "[]")
        foc = next((o for o in outs if o.get("focused")), None) or None
        if foc is None:
            try:
                w = subprocess.run(["swaymsg", "-t", "get_workspaces"],
                                   capture_output=True, text=True, timeout=3)
                if w.returncode == 0:
                    spaces = json.loads(w.stdout or "[]")
                    cur = next((s for s in spaces if s.get("focused")), None)
                    if cur is not None:
                        foc = next((o for o in outs
                                    if o.get("name") == cur.get("output")), None)
            except Exception:
                pass
        if not foc:
            return None
        rect = foc.get("rect") or {}
        want = (rect.get("x", foc.get("x")),
                rect.get("y", foc.get("y")),
                rect.get("width", foc.get("width")),
                rect.get("height", foc.get("height")))
        if None not in want:
            return (int(want[0]), int(want[1]), int(want[2]), int(want[3]))
    except Exception:
        pass
    return None


def _wlr_rand_geom():
    """wlr-randr: фокусный определить нельзя, берём первый включённый."""
    if shutil.which("wlr-randr") is None and shutil.which("wlr-randr-rs") is None:
        return None
    exe = shutil.which("wlr-randr") or shutil.which("wlr-randr-rs")
    try:
        r = subprocess.run([exe], capture_output=True, text=True, timeout=3)
        if r.returncode != 0:
            return None
        import re
        m = re.search(r"Position:\s*(-?\d+),(-?\d+).*?current\s+(-?\d+)\s*x\s*(-?\d+)",
                      r.stdout, re.S)
        if m:
            return (int(m.group(1)), int(m.group(2)),
                    int(m.group(3)), int(m.group(4)))
    except Exception:
        pass
    return None


def _kscreen_geom():
    """KDE: kscreen-doctor -j, берём enabled+primary (фокусный API не даёт)."""
    if shutil.which("kscreen-doctor") is None:
        return None
    try:
        r = subprocess.run(["kscreen-doctor", "-j"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout or "{}")
        outs = data.get("outputs") or []
        foc = (next((o for o in outs if o.get("primary")), None)
               or next((o for o in outs if o.get("enabled")), None))
        if not foc:
            return None
        pos = foc.get("pos") or {}
        size = foc.get("size") or {}
        mode = foc.get("mode") or {}
        w = size.get("width", mode.get("width"))
        h = size.get("height", mode.get("height"))
        want = (pos.get("x", 0), pos.get("y", 0), w, h)
        if None not in want and w and h:
            return (int(want[0]), int(want[1]), int(want[2]), int(want[3]))
    except Exception:
        pass
    return None


def focused_monitor_geom():
    """Геометрия фокусного/основного монитора (x, y, w, h) или None."""
    comp = detect_compositor()
    order = []
    if comp == "hyprland":
        order = [_hypr_focused_geom, _sway_focused_geom,
                 _wlr_rand_geom, _kscreen_geom]
    elif comp == "sway":
        order = [_sway_focused_geom, _hypr_focused_geom,
                 _wlr_rand_geom, _kscreen_geom]
    elif comp in ("kde", "kwin", "plasma"):
        order = [_kscreen_geom, _hypr_focused_geom,
                 _sway_focused_geom, _wlr_rand_geom]
    else:
        order = [_hypr_focused_geom, _sway_focused_geom,
                 _kscreen_geom, _wlr_rand_geom]
    for fn in order:
        try:
            g = fn()
        except Exception:
            g = None
        if g is not None:
            return g
    return None
