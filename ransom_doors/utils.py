"""Общие утилиты: поиск ассетов, PIL-инфо GIF, pidfile, выбор монитора."""
import os

from .config import GLITCH_DIRS, GLITCH_NAMES, PIDFILE


def find_first(candidates):
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def find_glitches():
    found, missing = [], []
    for name in GLITCH_NAMES:
        hit = next((os.path.join(d, name) for d in GLITCH_DIRS
                    if os.path.isfile(os.path.join(d, name))), None)
        (found if hit else missing).append(hit or name)
    return found, missing


def gif_info(gif_path):
    """(n_frames, one_loop_ms) — через PIL, с запасами при ошибке."""
    try:
        from PIL import Image
        im = Image.open(gif_path)
        n = getattr(im, "n_frames", 1) or 1
        total = 0
        for i in range(n):
            im.seek(i)
            total += int(im.info.get("duration", 100))
        return max(1, n), max(1, total)
    except Exception:
        return 12, 1500


def toggle_existing():
    """Повторный запуск завершает уже висящий оверлей."""
    import signal
    import time
    if not os.path.isfile(PIDFILE):
        return False
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
    except (ValueError, OSError):
        return False
    if pid == os.getpid():
        return False
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            if "show_downloading_attack" not in f.read().decode(errors="ignore"):
                try:
                    os.remove(PIDFILE)
                except OSError:
                    pass
                return False
    except OSError:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return False
    for _ in range(20):
        time.sleep(0.1)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
    try:
        os.remove(PIDFILE)
    except OSError:
        pass
    print("Оверлей был запущен — завершил его (повторный запуск).", flush=True)
    return True


def write_pidfile():
    try:
        with open(PIDFILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def remove_pidfile():
    try:
        if os.path.isfile(PIDFILE):
            with open(PIDFILE) as f:
                if f.read().strip() == str(os.getpid()):
                    os.remove(PIDFILE)
    except OSError:
        pass


def pick_monitor(display):
    """Фокусный монитор Hyprland (матчинг по геометрии), иначе как в vignette.

    get_client_pointer().get_position() на Wayland/GDK отдаёт (screen, 0, 0),
    т.е. всегда выбирался бы монитор в точке 0,0 — поэтому сначала пробуем
    фокусный монитор через hyprctl.
    """
    want = None
    try:
        import json
        import subprocess
        mons = json.loads(subprocess.check_output(
            ["hyprctl", "monitors", "-j"], timeout=3).decode())
        foc = next((m for m in mons if m.get("focused")), None)
        if foc is not None:
            want = (foc.get("x"), foc.get("y"), foc.get("width"), foc.get("height"))
    except Exception:
        want = None
    if want is not None and None not in want:
        try:
            for i in range(display.get_n_monitors()):
                m = display.get_monitor(i)
                if m is not None:
                    g = m.get_geometry()
                    if (g.x, g.y, g.width, g.height) == tuple(want):
                        return m
        except Exception:
            pass
    try:
        pos = display.get_device_manager().get_client_pointer().get_position()
        m = display.get_monitor_at_point(pos[-2], pos[-1])
        if m is not None:
            return m
    except Exception:
        pass
    try:
        m = display.get_primary_monitor()
        if m is not None:
            return m
    except Exception:
        pass
    return display.get_monitor(0)
