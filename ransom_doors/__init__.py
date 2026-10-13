"""RansomDoors — пакет вместо монолита.

Модули:
- config: константы/пути
- platform: детект композитора, курсор, геометрия монитора
- coins: движок монет .goldN/.crucifix
- utils: поиск ассетов, gif_info, pidfile, монитор
- cli: argparse
- idle: стартовая засада (мигающий ransom_idle.png, триггер/таймаут)
- sound: SoundEngine (ffplay/pw-play/paplay/aplay)
- wallpaper: смена/возврат обоев (awww/swww/hyprpaper/swaybg/gsettings/plasma/feh)
- gtkkit: Sprite, fit_static, fake-окна (GtkLayerShell опционален)
- ransom_note: GTK-реплика записки 560x400
- app: оркестрация оверлея (этапы, глитчи, флоатеры, финалы, DnD)
"""
from .app import App
from .cli import parse_args

__all__ = ["App", "parse_args", "main"]


def main(argv=None):
    a = parse_args(argv)
    return App(a).run()
