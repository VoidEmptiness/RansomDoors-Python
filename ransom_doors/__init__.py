"""RansomDoors — пакет вместо монолита.

Модули:
- config: константы/пути
- coins: движок монет .goldN/.crucifix
- utils: поиск ассетов, gif_info, pidfile, монитор
- cli: argparse
- idle: стартовая засада (мигающий ransom_idle.png, триггер/таймаут)
- sound: SoundEngine (ffplay/paplay)
- wallpaper: смена/возврат обоев через awww
- gtkkit: Sprite, fit_static, fake-окна
- ransom_note: GTK-реплика записки 560x400
- app: оркестрация оверлея (этапы, глитчи, флоатеры, финалы, DnD)
"""
from .app import App
from .cli import parse_args

__all__ = ["App", "parse_args", "main"]


def main(argv=None):
    a = parse_args(argv)
    return App(a).run()
