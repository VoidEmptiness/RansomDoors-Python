#!/usr/bin/env python3
"""Точка входа RansomDoors (тонкий шим).

Вся логика переехала в пакет `ransom_doors/`:
  config      — константы/пути
  coins       — движок монет .goldN/.crucifix
  utils       — поиск ассетов, gif_info, pidfile, монитор
  cli         — argparse
  sound       — SoundEngine (ffplay/paplay)
  wallpaper   — смена/возврат обоев через awww
  gtkkit      — Sprite, fit_static, fake-окна
  ransom_note — GTK-реплика записки 560x400
  app         — оркестрация оверлея (этапы, глитчи, флоатеры, финалы, DnD)

Старый монолит сохранён как RansomDoors.monolith.bak.
Запуск как раньше: python3 RansomDoors.py [опции] / python3 -m ransom_doors [опции]
"""
import sys

from ransom_doors import main

if __name__ == "__main__":
    sys.exit(main())
