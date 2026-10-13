"""Обои: запомнить, поставить тёмные, вернуть при выходе.

Кросс-композитор, авто-детект первого доступного бэкенда:
  awww        — Hyprland (как раньше; `awww query` / `awww img`)
  swww        — wlroots (Hyprland/Sway/labwc/wayfire): query/img
  hyprpaper   — Hyprland штатный (`hyprctl hyprpaper ...`)
  swaybg      — Sway/wlroots (одноразовый процесс, kill при restore)
  gsettings   — GNOME/MATE/Cinnamon (picture-uri)
  plasma      — KDE (`plasma-apply-wallpaperimage`, restore лучшим усилием)
  feh/nitrogen— X11 запасной вариант

Неизвестная среда или нет тулзов — пропуск с понятным логом,
скрипт продолжает работать без смены обоев.
"""
import shutil
import subprocess

from .config import WALLPAPER_CANDIDATES
from .utils import find_first


class WallpaperManager:
    def __init__(self, disabled=False):
        self.disabled = bool(disabled)
        self.backend = None
        self.old = {}
        self.changed = False
        self._swaybg_proc = None
        self._gsettings_old = {}
        self._feh_old = None

    # ---------- детект ----------

    def _pick_backend(self):
        if shutil.which("awww") is not None:
            return "awww"
        if shutil.which("swww") is not None:
            return "swww"
        if shutil.which("hyprctl") is not None and shutil.which("hyprpaper") is not None:
            return "hyprpaper"
        if shutil.which("swaybg") is not None:
            return "swaybg"
        if shutil.which("gsettings") is not None:
            return "gsettings"
        if shutil.which("plasma-apply-wallpaperimage") is not None:
            return "plasma"
        if shutil.which("feh") is not None:
            return "feh"
        return None

    # ---------- public ----------

    def swap(self):
        """Запомнить текущие обои и поставить тёмные на все выходы."""
        if self.disabled:
            return
        wp = find_first(WALLPAPER_CANDIDATES)
        if not wp:
            print("обои: darkred_wallpaper.png не найден — пропуск", flush=True)
            return
        backend = self._pick_backend()
        if backend is None:
            print("обои: нет awww/swww/hyprpaper/swaybg/gsettings/plasma/feh — пропуск",
                  flush=True)
            return
        self.backend = backend
        try:
            ok = {
                "awww": lambda: self._swap_awww(wp),
                "swww": lambda: self._swap_swww(wp),
                "hyprpaper": lambda: self._swap_hyprpaper(wp),
                "swaybg": lambda: self._swap_swaybg(wp),
                "gsettings": lambda: self._swap_gsettings(wp),
                "plasma": lambda: self._swap_plasma(wp),
                "feh": lambda: self._swap_feh(wp),
            }[backend]()
        except Exception as e:
            print(f"обои: {backend} не удался: {e}", flush=True)
            ok = False
        if ok:
            self.changed = True

    def restore(self):
        """Вернуть запомненные обои."""
        if not self.changed:
            return
        self.changed = False
        try:
            if self.backend in ("awww", "swww"):
                self._restore_awww_swww()
            elif self.backend == "hyprpaper":
                self._restore_hyprpaper()
            elif self.backend == "swaybg":
                self._restore_swaybg()
            elif self.backend == "gsettings":
                self._restore_gsettings()
            elif self.backend == "plasma":
                self._restore_plasma()
            elif self.backend == "feh":
                self._restore_feh()
        except Exception:
            pass
        print(f"обои: вернул ({self.backend}) {self.old or self._gsettings_old}",
              flush=True)

    # ---------- awww / swww (совместимый CLI) ----------

    @staticmethod
    def _parse_query(out, exe):
        olds = {}
        for line in out.splitlines():
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
        return olds

    def _swap_awww(self, wp):
       	return self._swap_awww_swww(wp, "awww")

    def _swap_swww(self, wp):
        return self._swap_awww_swww(wp, "swww")

    def _swap_awww_swww(self, wp, exe=None):
        exe = exe or self.backend
        try:
            out = subprocess.run([exe, "query"], capture_output=True,
                                 text=True, timeout=10)
        except Exception as e:
            print(f"обои: {exe} query не удался: {e}", flush=True)
            return False
        olds = self._parse_query(out.stdout, exe)
        if not olds:
            print(f"обои: не разобрал {exe} query — пропуск", flush=True)
            return False
        self.old = olds
        try:
            subprocess.run([exe, "img", wp], capture_output=True, timeout=15)
            print(f"обои: [{exe}] запомнил {olds} -> ставлю {wp.split('/')[-1]}",
                  flush=True)
            return True
        except Exception as e:
            print(f"обои: не смог поставить: {e}", flush=True)
            return False

    def _restore_awww_swww(self):
        exe = self.backend
        by_img = {}
        for mon, img in self.old.items():
            by_img.setdefault(img, []).append(mon)
        for img, mons in by_img.items():
            try:
                subprocess.run([exe, "img", "-o", ",".join(mons), img],
                               capture_output=True, timeout=15)
            except Exception:
                pass

    # ---------- hyprpaper ----------

    def _swap_hyprpaper(self, wp):
        try:
            out = subprocess.run(["hyprctl", "hyprpaper", "listactive"],
                                 capture_output=True, text=True, timeout=10)
            olds = {}
            for line in (out.stdout or "").splitlines():
                # формат: "<mon> = <path>"
                if "=" in line:
                    mon, _, img = line.partition("=")
                    mon, img = mon.strip(), img.strip()
                    if mon and img:
                        olds[mon] = img
            if not olds:
                # listactive пуст — хотя бы запомним факт смены
                olds = {"*": "hyprpaper-prev"}
            self.old = olds
            subprocess.run(["hyprctl", "hyprpaper", "wallpaper", f",{wp}"],
                           capture_output=True, timeout=15)
            print(f"обои: [hyprpaper] запомнил {olds} -> ставлю {wp.split('/')[-1]}",
                  flush=True)
            return True
        except Exception as e:
            print(f"обои: hyprpaper не удался: {e}", flush=True)
            return False

    def _restore_hyprpaper(self):
        for mon, img in self.old.items():
            if mon == "*" or not img or img == "hyprpaper-prev":
                continue
            try:
                subprocess.run(["hyprctl", "hyprpaper", "wallpaper", f"{mon},{img}"],
                               capture_output=True, timeout=15)
            except Exception:
                pass

    # ---------- swaybg (процесс) ----------

    def _swap_swaybg(self, wp):
        import os
        self.old = {"*": "swaybg-prev"}
        try:
            self._kill_swaybg_prev()
            proc = subprocess.Popen(["swaybg", "-i", wp, "-m", "fill"],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            self._swaybg_proc = proc
            print(f"обои: [swaybg] ставлю {os.path.basename(wp)} (pid {proc.pid})",
                  flush=True)
            return True
        except Exception as e:
            print(f"обои: swaybg не удался: {e}", flush=True)
            return False

    @staticmethod
    def _kill_swaybg_prev():
        try:
            subprocess.run(["pkill", "-x", "swaybg"], capture_output=True, timeout=5)
        except Exception:
            pass

    def _restore_swaybg(self):
        proc = self._swaybg_proc
        self._swaybg_proc = None
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    # ---------- gsettings (GNOME и др.) ----------

    _GSETTINGS_KEYS = [
        ("org.gnome.desktop.background", "picture-uri"),
        ("org.gnome.desktop.background", "picture-uri-dark"),
    ]

    def _swap_gsettings(self, wp):
        import pathlib
        uri = pathlib.Path(wp).absolute().as_uri()
        old = {}
        for schema, key in self._GSETTINGS_KEYS:
            try:
                r = subprocess.run(["gsettings", "get", schema, key],
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    old[(schema, key)] = r.stdout.strip()
            except Exception:
                pass
        self._gsettings_old = old
        ok = False
        for schema, key in self._GSETTINGS_KEYS:
            try:
                r = subprocess.run(["gsettings", "set", schema, key, uri],
                                   capture_output=True, timeout=5)
                if r.returncode == 0:
                    ok = True
            except Exception:
                pass
        if ok:
            print(f"обои: [gsettings] запомнил {old} -> ставлю {uri}", flush=True)
        else:
            print("обои: gsettings set не удался — пропуск", flush=True)
        return ok

    def _restore_gsettings(self):
        for (schema, key), val in self._gsettings_old.items():
            try:
                subprocess.run(["gsettings", "set", schema, key, val],
                               capture_output=True, timeout=5)
            except Exception:
                pass

    # ---------- KDE Plasma ----------

    def _swap_plasma(self, wp):
        self.old = {"*": "plasma-prev (restore вручную)"}
        try:
            r = subprocess.run(["plasma-apply-wallpaperimage", wp],
                               capture_output=True, timeout=15)
            if r.returncode == 0:
                print(f"обои: [plasma] ставлю {wp.split('/')[-1]} "
                      f"(восстановление штатно невозможно — верните вручную)",
                      flush=True)
                return True
            print("обои: plasma-apply-wallpaperimage вернул ошибку — пропуск",
                  flush=True)
            return False
        except Exception as e:
            print(f"обои: plasma не удался: {e}", flush=True)
            return False

    def _restore_plasma(self):
        # Plasma не хранит предыдущие обои доступным способом —
        # честно ничего не делаем, пользователь вернёт вручную.
        pass

    # ---------- feh (X11) ----------

    def _swap_feh(self, wp):
        self._feh_old = None
        try:
            subprocess.run(["feh", "--bg-fill", wp],
                           capture_output=True, timeout=15)
            print(f"обои: [feh] ставлю {wp.split('/')[-1]} (restore вручную)",
                  flush=True)
            return True
        except Exception as e:
            print(f"обои: feh не удался: {e}", flush=True)
            return False

    def _restore_feh(self):
        pass
