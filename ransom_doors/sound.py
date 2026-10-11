"""Звук: ffplay (лупы+стоп) либо paplay (только разовые) либо выкл."""
import os
import shutil
import subprocess

from .config import SOUND_FILES, SOUNDS_DIRS


class SoundEngine:
    def __init__(self, no_sound=False):
        self.engine = None
        self.files = {}
        self.dur = {}
        self.mus = None
        self.mus_proc = None
        self.sfx_procs = []
        self.disabled = bool(no_sound)

    def init(self):
        if self.disabled:
            return
        eng = ("ffplay" if shutil.which("ffplay")
               else "paplay" if shutil.which("paplay") else None)
        if eng is None:
            print("звук: нет ffplay/paplay — выкл", flush=True)
            return
        found = 0
        for key, name in SOUND_FILES.items():
            for d in SOUNDS_DIRS:
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    self.files[key] = p
                    found += 1
                    break
        if not found:
            print("звук: файлы не найдены — выкл", flush=True)
            return
        self.engine = eng
        import wave as _wave
        for key, p in self.files.items():
            try:
                w = _wave.open(p, "rb")
                self.dur[key] = w.getnframes() / max(1, w.getframerate())
                w.close()
            except Exception:
                pass
        print(f"звук: {eng}, файлов: {found}", flush=True)

    def sfx(self, name):
        """Разовый звук. Процесс трекаем, чтобы при выходе прибить хвост."""
        p = self.files.get(name)
        if p is None:
            return
        print(f"sfx: {name}", flush=True)
        try:
            if self.engine == "ffplay":
                proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit",
                                         "-loglevel", "error", p],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            else:
                proc = subprocess.Popen(["paplay", p],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            self._reap_sfx()
            self.sfx_procs.append(proc)
        except Exception:
            pass

    def _reap_sfx(self):
        live = []
        for proc in self.sfx_procs:
            try:
                if proc.poll() is None:
                    live.append(proc)
            except Exception:
                pass
        self.sfx_procs = live

    def stop_sfx(self):
        """Прибить все разовые хвосты (layer3 26с, thankyou, crucifix и т.д.)."""
        procs, self.sfx_procs = self.sfx_procs, []
        for proc in procs:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
        for proc in procs:
            try:
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def music(self, name):
        """Фоновая (луп), только через ffplay. Повтор того же — пропуск."""
        if self.mus == name:
            return
        self.stop_music()
        p = self.files.get(name)
        if p is None or self.engine != "ffplay":
            return
        print(f"music: {name} (loop)", flush=True)
        try:
            self.mus_proc = subprocess.Popen(
                ["ffplay", "-nodisp", "-loop", "0", "-loglevel", "error", p],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.mus = name
        except Exception:
            self.mus = None

    def stop_music(self):
        proc = getattr(self, "mus_proc", None)
        self.mus_proc = None
        self.mus = None
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def stop_all(self):
        """Полная тишина: луп + все разовые хвосты. Вызывать при
        победе/поражении перед финальным звуком и в finally при выходе."""
        self.stop_music()
        self.stop_sfx()
