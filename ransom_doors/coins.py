"""Движок монет: создание .goldN/.crucifix, обход папок вширь, трекинг."""
import hashlib
import json
import os
import uuid

from .config import COIN_VALUES

COIN_CACHE = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "ransom_coins.json")


def coin_id(path):
    """ID монетки как в ransom_window_pyqt.py (защита от повторного приёма)."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read(65536))
        return h.hexdigest() + path
    except OSError:
        return path


def _rm(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def _rmdir(path):
    try:
        os.rmdir(path)
        return True
    except OSError:
        return False


def _read_xdg_dirs():
    """Парсит ~/.config/user-dirs.dirs -> {DESKTOP: path, ...}."""
    out = {}
    p = os.path.expanduser("~/.config/user-dirs.dirs")
    home = os.path.expanduser("~")
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip().strip('"')
                v = v.replace("$HOME", home)
                out[k.strip()] = v
    except OSError:
        pass
    return out


def get_user_folders():
    """Существующие папки: Desktop/Documents/Downloads/Music/Pictures/Projects."""
    xdg = _read_xdg_dirs()
    home = os.path.expanduser("~")
    cand = {
        "Desktop": xdg.get("XDG_DESKTOP_DIR", os.path.join(home, "Desktop")),
        "Documents": xdg.get("XDG_DOCUMENTS_DIR", os.path.join(home, "Documents")),
        "Downloads": xdg.get("XDG_DOWNLOAD_DIR", os.path.join(home, "Downloads")),
        "Music": xdg.get("XDG_MUSIC_DIR", os.path.join(home, "Music")),
        "Pictures": xdg.get("XDG_PICTURES_DIR", os.path.join(home, "Pictures")),
        "Videos": xdg.get("XDG_VIDEOS_DIR", os.path.join(home, "Videos")),
    }
    for pc in ("Projects", "projects", "code", "Code", "src", "work"):
        pp = os.path.join(home, pc)
        if os.path.isdir(pp):
            cand["Projects"] = pp
            break
    else:
        cand["Projects"] = os.path.join(home, "Projects")
    existing = {k: v for k, v in cand.items() if os.path.isdir(v)}
    return existing, cand


def weighted_extension(rng):
    r = rng.randrange(100)
    if r < 40:
        return 1
    if r < 70:
        return 2
    if r < 85:
        return 3
    if r < 93:
        return 4
    return 5


def create_coin(directory, ext):
    cid = uuid.uuid4().hex
    payload = json.dumps({"RANSOM_COIN": cid}).encode()
    name = f"{uuid.uuid4().hex}.gold{ext}"
    full = os.path.join(directory, name)
    with open(full, "wb") as f:
        f.write(payload)
    return full, COIN_VALUES[ext]


def create_crucifix(directory):
    cid = uuid.uuid4().hex
    payload = json.dumps({"RANSOM_COIN": cid}).encode()
    full = os.path.join(directory, f"{uuid.uuid4().hex}.crucifix")
    with open(full, "wb") as f:
        f.write(payload)
    return full


def load_track():
    try:
        with open(COIN_CACHE, encoding="utf-8") as f:
            d = json.load(f)
            return d.get("files", []), d.get("dirs", [])
    except (OSError, ValueError):
        return [], []


def save_track(files, dirs):
    old_f, old_d = load_track()
    data = {"files": old_f + files, "dirs": old_d + dirs}
    os.makedirs(os.path.dirname(COIN_CACHE), exist_ok=True)
    with open(COIN_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _dir_has_coin(path):
    """Есть ли в папке уже монета (.gold1-6/.crucifix)."""
    try:
        names = os.listdir(path)
    except OSError:
        return False
    for n in names:
        ext = os.path.splitext(n)[1]
        if ext in (".crucifix", ".gold1", ".gold2", ".gold3",
                   ".gold4", ".gold5", ".gold6"):
            return True
    return False


def iter_dirs(root, max_depth, cap=5000):
    """BFS по подпапкам (без скрытых и симлинков), с лимитом глубины и капом.
    Вширь: сначала весь текущий уровень, глубже — только когда класть некуда."""
    from collections import deque
    q = deque([(root, 0)])
    seen = 0
    while q and seen < cap:
        cur, d = q.popleft()
        seen += 1
        yield cur
        if d >= max_depth:
            continue
        try:
            subs = sorted(os.listdir(cur))
        except OSError:
            continue
        for name in subs:
            if name.startswith("."):
                continue
            full = os.path.join(cur, name)
            try:
                if os.path.isdir(full) and not os.path.islink(full):
                    q.append((full, d + 1))
            except OSError:
                continue


def spawn_deep(ransom, roots, rng, depth=6, extra=100, chance=0.6, honeypot=25,
               cruc=10, dry_run=False):
    """Разброс вширь: по монете в каждую папку уровня (где ещё нет, и то
    с шансом chance), глубже — когда на уровне класть некуда. Стоп при
    сумме ransom + extra. Затем honeypot/crucifix шансами."""
    target = int(ransom) + int(extra)
    chance = max(0.0, min(1.0, chance))
    gen = 0
    files = []
    visited = []
    for root in roots:
        if gen >= target:
            break
        for d in iter_dirs(root, max(0, depth)):
            if gen >= target:
                break
            visited.append(d)
            try:
                os.makedirs(d, exist_ok=True)
            except OSError:
                continue
            if _dir_has_coin(d):
                continue  # монета есть — идём глубже, сюда не кладём
            if rng.random() >= chance:
                continue  # не повезло — папка остаётся без монеты
            ext = weighted_extension(rng)
            if dry_run:
                gen += COIN_VALUES[ext]
                files.append(f"[dry] {d} -> .gold{ext} ({COIN_VALUES[ext]})")
            else:
                try:
                    fp, val = create_coin(d, ext)
                except OSError:
                    continue
                files.append(fp)
                gen += val
    # не хватило папок — круги уже без проверки «есть монета», пока не добьём
    guard = 0
    while gen < target and visited and guard < 1000:
        guard += 1
        for d in visited:
            if gen >= target:
                break
            ext = weighted_extension(rng)
            if dry_run:
                gen += COIN_VALUES[ext]
                files.append(f"[dry] {d} -> .gold{ext} ({COIN_VALUES[ext]})")
            else:
                try:
                    fp, val = create_coin(d, ext)
                except OSError:
                    continue
                files.append(fp)
                gen += val
    # honeypot .gold6
    if rng.random() * 100 < honeypot and visited:
        d = rng.choice(visited)
        if dry_run:
            files.append(f"[dry] {d} -> .gold6 (500)")
        else:
            try:
                files.append(create_coin(d, 6)[0])
            except OSError:
                pass
    # crucifix
    if rng.random() * 100 < cruc and visited:
        d = rng.choice(visited)
        if dry_run:
            files.append(f"[dry] {d} -> .crucifix")
        else:
            try:
                files.append(create_crucifix(d))
            except OSError:
                pass
    return gen, files, []
