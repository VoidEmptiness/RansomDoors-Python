"""Обои: запомнить через `awww query`, поставить тёмные, вернуть при выходе."""
import shutil
import subprocess

from .config import WALLPAPER_CANDIDATES
from .utils import find_first


class WallpaperManager:
    def __init__(self, disabled=False):
        self.disabled = bool(disabled)
        self.old = {}
        self.changed = False

    def swap(self):
        """Запомнить текущие обои (awww query) и поставить тёмные на все выходы."""
        if self.disabled:
            return
        if shutil.which("awww") is None:
            print("обои: нет awww — пропуск", flush=True)
            return
        wp = find_first(WALLPAPER_CANDIDATES)
        if not wp:
            print("обои: darkred_wallpaper.png не найден — пропуск", flush=True)
            return
        try:
            out = subprocess.run(["awww", "query"], capture_output=True,
                                 text=True, timeout=10)
        except Exception as e:
            print(f"обои: query не удался: {e}", flush=True)
            return
        olds = {}
        for line in out.stdout.splitlines():
            if "currently displaying:" not in line:
                continue
            left, _, right = line.partition("currently displaying:")
            parts = left.split(":")
            mon = parts[1].strip() if len(parts) > 1 else ""
            img = right.strip()
            if img.startswith("image:"):
                img = img[len("image:"):].strip()
            if mon and img:
                olds[mon] = img
        if not olds:
            print("обои: не разобрал query — пропуск", flush=True)
            return
        self.old = olds
        try:
            subprocess.run(["awww", "img", wp], capture_output=True, timeout=15)
            self.changed = True
            print(f"обои: запомнил {olds} -> ставлю {wp.split('/')[-1]}",
                  flush=True)
        except Exception as e:
            print(f"обои: не смог поставить: {e}", flush=True)

    def restore(self):
        """Вернуть запомненные обои (по мониторам)."""
        if not self.changed:
            return
        self.changed = False
        by_img = {}
        for mon, img in self.old.items():
            by_img.setdefault(img, []).append(mon)
        for img, mons in by_img.items():
            try:
                subprocess.run(["awww", "img", "-o", ",".join(mons), img],
                               capture_output=True, timeout=15)
            except Exception:
                pass
        print(f"обои: вернул {self.old}", flush=True)
