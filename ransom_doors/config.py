"""Константы и пути RansomDoors. Чистый модуль без сторонних зависимостей."""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OVERLAY_TITLE = "downloading + attack overlay"
LAYER_NAMESPACE = "downloading-attack"
PIDFILE = "/tmp/downloading_attack_overlay.pid"

DOWNLOAD_CANDIDATES = [
    os.path.join(BASE, "assets", "downloading.gif"),
    os.path.join(BASE, "downloading.gif"),
    "assets/downloading.gif",
]
ATTACK_CANDIDATES = [
    os.path.join(BASE, "assets", "ransom_attack.gif"),
    os.path.join(BASE, "ransom_attack.gif"),
    "assets/ransom_attack.gif",
]
GLITCH_NAMES = ["glitch1.jpg", "glitch2.jpeg", "glitch3.jpg", "glitch4.jpg", "glitch5.jpg"]
GLITCH_DIRS = [
    os.path.join(BASE, "assets", "taunts"),
    os.path.join(BASE, "assets"),
    os.path.join(BASE, "taunts"),
    BASE,
]
RANSOM_FACE_CANDIDATES = [
    os.path.join(BASE, "assets", "ransom_idle.png"),
    os.path.join(BASE, "Assets", "ransom_idle.png"),
]
RANSOM_COIN_CANDIDATES = [
    os.path.join(BASE, "assets", "Gold.png"),
    os.path.join(BASE, "Assets", "Gold.png"),
]
SIGN_CANDIDATES = [
    os.path.join(BASE, "assets", "stop_sign.png"),
    os.path.join(BASE, "stop_sign.png"),
    "assets/stop_sign.png",
]
CORNER_MS = 1500  # прыжки attack по углам: раз в 1.5с
CORNERS = ["слева сверху", "справа сверху", "слева снизу", "справа снизу"]
THANKS_CANDIDATES = [
    os.path.join(BASE, "assets", "thankyou.gif"),
    os.path.join(BASE, "thankyou.gif"),
    "assets/thankyou.gif",
]
REPENT_CANDIDATES = [
    os.path.join(BASE, "assets", "repent.gif"),
    os.path.join(BASE, "repent.gif"),
    "assets/repent.gif",
]
WALLPAPER_CANDIDATES = [
    os.path.join(BASE, "assets", "darkred_wallpaper.png"),
    os.path.join(BASE, "darkred_wallpaper.png"),
    "assets/darkred_wallpaper.png",
]
LOSS_CANDIDATES = [
    os.path.join(BASE, "assets", "loss_no_vignette.gif"),
    os.path.join(BASE, "loss_no_vignette.gif"),
    "assets/loss_no_vignette.gif",
]
VIGNETTE_CANDIDATES = [
    os.path.join(BASE, "assets", "red_vignette.gif"),
    os.path.join(BASE, "red_vignette.gif"),
    "assets/red_vignette.gif",
]
WINDOW_TITLES = [
    "RANS0M", "MOSNAR", "RANSOM", "M0NARS", "YOU ARE AN IDIOT", "Untitled",
    "Untitled (3)", "I FOUND YOU", "RANSOM.exe", "RAANNNSSSSOOOOOMMMMMM",
    "times up", "GIVE MONEY", "ERROR", "DHAUFGH", "_________", "IMG.JPG",
]
TITLE_H = 28  # высота белой полоски заголовка
RANSOM_W, RANSOM_H = 560, 400  # размер записки без полоски
COIN_VALUES = {1: 10, 2: 50, 3: 100, 4: 150, 5: 200, 6: 500}
ICON_BY_EXT = {
    ".gold1": "Gold/Gold1.png",
    ".gold2": "Gold/Gold2.png",
    ".gold3": "Gold/Gold3.png",
    ".gold4": "Gold/Gold4.png",
    ".gold5": "Gold/Gold5.png",
    ".gold6": "Gold/HoneyPot.png",
    ".crucifix": "crucifix.png",
}
SOUNDS_DIRS = [
    os.path.join(BASE, "assets", "sounds"),
    os.path.join(BASE, "assets", "Sounds"),
]
SOUND_FILES = {
    "spawn": "spawn.wav",
    "attack": "attack.wav",
    "install": "install.wav",
    "layer1": "layer1.wav",
    "layer2": "layer2.wav",
    "layer3": "layer3.wav",
    "cash": "cash.wav",
    "thankyou": "thankyou.wav",
    "crucifix": "crucifix.wav",
    "tauntspawn": "tauntSpawn.wav",
    "tauntleave": "tauntLeave.wav",
}
TAUNT_CANDIDATES = [
    os.path.join(BASE, "assets", "taunts", "idiot.png"),
    os.path.join(BASE, "assets", "taunts", "tauntface.png"),
    os.path.join(BASE, "assets", "taunts", "tauntflower.png"),
    os.path.join(BASE, "assets", "idiot.png"),
]
