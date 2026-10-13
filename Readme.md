# RansomDoors

**Language / Язык:** [English](#english) | [Русский](#russian)

---

<a id="english"></a>

## 🇬🇧 English

**I won't hide it: the project was written with the help of AI and my clumsy fingers.**

# RansomDoors

This is a fork of the original RansomDoors (https://github.com/Ixars/ransomdoors).

This version has been rewritten in Python, which makes it compatible with practically any system (my system is Arch Linux, Hyprland, Config - ML4W Lua).

### Features

Everything the original RansomDoors has — except mine also has bugs :)

### Requirements

- Linux + Wayland/X11. Best on Hyprland and wlroots (Sway/labwc/wayfire/niri); also works on GNOME/Mutter, KDE/KWin, COSMIC, XFCE, i3 via fallback (see Notes).
- Python 3 + `PyGObject` (GTK 3), `Pillow` (GIF durations), `pycairo`. `GtkLayerShell 0.1` is optional — used only on wlroots compositors, otherwise a fullscreen/maximize fallback is used.
- Optional, auto-detected (first available wins):
  - sound: `ffplay` → `pw-play` → `paplay` → `aplay`;
  - wallpaper: `awww` → `swww` → `hyprpaper` (+`hyprctl`) → `swaybg` → `gsettings` (GNOME/MATE/Cinnamon) → `plasma-apply-wallpaperimage` (KDE) → `feh` (X11);
  - cursor/monitor: `hyprctl` → `swaymsg` → `xdotool`, plus `wlr-randr` / `kscreen-doctor` for geometry, otherwise GDK fallback;
  - `gio` (coin icons).

### Installation and Launch

```bash
# system deps (Arch example)
sudo pacman -S python-gobject gtk-layer-shell python-pillow python-cairo
# optional backends (different for each system):
# sudo pacman -S ffmpeg pipewire-pulse libpulse alsa-utils awww swww hyprpaper swaybg feh xdotool wlr-randr

git clone https://github.com/VoidEmptiness/RansomDoors-Python && cd RansomDoors-Python && python3 RansomDoors.py
```

### Payment

Denominations: `.gold1`=10, `.gold2`=50, `.gold3`=100, `.gold4`=150, `.gold5`=200, `.gold6`=500. `.crucifix` wipes the debt entirely.

Each coin is a JSON `{"RANSOM_COIN": "<uuid>"}` with a random name, protected against being accepted twice via a content hash. On payment the file is deleted. On exit, your own coins are removed (unless `--no-coin-cleanup`). Track list: `~/.cache/ransom_coins.json`.

Total coin sum ≈ `--ransom-sum` (or `--coin-ransom`) + `--coin-extra 100`.

### Key Options

```
--loops 1 --loss-loops 2 --thanks-loops 1 --repent-loops 1
--idle-timeout 30 --idle-min 4 --idle-max 6 --no-idle (skip the ambush)
--attack-scale 2.0 --sign-scale 2.0 --download-scale 1.0
--glitch-delay 350 --glitch-width 480
--shake-px 6 --shake-ms 120
--move-min 2 --move-max 10 --vis-min 2 --vis-max 6
--hide-chance 0.35 --show-chance 0.5 --max-visible 4 --min-visible 1 --max-cover 0.3
--ransom-sum 500 --rantime 90 --auto-quit 0
--coin-depth 6 --coin-chance 0.6 --coin-extra 100 --coin-honeypot 25 --coin-cruc 10
--coin-roots DIR (repeatable) --coin-drawer --coin-seed N --coin-ransom N
--pay-file FILE (repeatable, for tests)
--seed N
--no-attack --no-loss --no-ransom --no-coins --no-floaters/--no-taunts
--no-vignette --no-sound --no-wallpaper --no-coin-cleanup --no-coin-icons
--no-fullscreen (960x540 window for debugging)
--fullscreen-mode auto|fullscreen|maximize (fallback without layer-shell; auto = maximize on GNOME/Mutter, fullscreen elsewhere)
--click-through (default on) / --no-click-through (overlay captures input)
```

Full list: `python3 RansomDoors.py --help`.

### Structure

```
RansomDoors.py        # thin entry-point shim
ransom_doors/
  __init__.py __main__.py
  app.py              # orchestration: window, stages, glitches, floaters, finals, DnD
  cli.py              # argparse
  platform.py         # compositor detect, cursor, monitor geometry, layer-shell check
  idle.py             # starting ambush ransom_idle.png
  config.py           # constants, path candidates, denominations, sounds
  coins.py            # spawn .goldN/.crucifix, BFS traversal, tracking
  gtkkit.py           # Sprite with stepping/cover, fit_static, fake windows (GtkLayerShell optional)
  ransom_note.py      # GTK replica of the note 560x400 + timer
  sound.py            # SoundEngine (ffplay/pw-play/paplay/aplay)
  wallpaper.py        # swap/restore via awww/swww/hyprpaper/swaybg/gsettings/plasma/feh
  utils.py            # asset lookup, gif_info (PIL), pidfile, pick_monitor (via platform)
assets/
  downloading.gif ransom_attack.gif loss_no_vignette.gif red_vignette.gif
  thankyou.gif repent.gif ransom_idle.png Gold.png stop_sign.png
  darkred_wallpaper.png crucifix.png Gold/Gold1-5.png Gold/HoneyPot.png
  taunts/glitch1-5.* idiot.png tauntface.png tauntflower.png
  sounds/spawn.wav attack.wav install.wav layer1-3.wav cash.wav
         thankyou.wav crucifix.wav tauntSpawn.wav tauntLeave.wav
```

### Notes

- The project looks for assets among several candidates (`assets/...`, next to the file) and fails with a clear error only if `downloading.gif` or the glitches are missing.
- By default coins are placed in the real `Desktop/Documents/Downloads/Music/Pictures/Videos/Projects` — use `--coin-drawer` for experiments.
- Overlay backend: layer-shell on wlroots (Hyprland/Sway/...); plain fullscreen on top everywhere else. On GNOME/Mutter real fullscreen is unredirected (transparency becomes black), so `auto` uses a borderless maximized window instead — override with `--fullscreen-mode fullscreen|maximize`.
- Wallpaper restore on KDE Plasma and `feh`/`swaybg` is best-effort: Plasma does not expose the previous wallpaper, so you may need to restore it manually.
- This is not malware: no encryption, no network, no persistence. Do not use it against other people without their consent.

## Credits

- **Doors** is made by **LSPLASH**. The RANSOM/A-90 entity, its name, look,
  and concept are their original work — this project is an unofficial fan
  recreation, not affiliated with or endorsed by LSPLASH. Go play the real
  game.

[Back to top](#ransomdoors)

---

<a id="russian"></a>

## 🇷🇺 Русский

**Не буду скрывать проект написан с помощью ИИ и моих криворуких пальцев.**

# RansomDoors

Это Форк оригинального RansomDoors (https://github.com/Ixars/ransomdoors)

Эта версия переписана на Python, что позволяет ему быть совместимым практический с любой системой (Моя система Arch Linux, Hyprland, Config - ML4W Lua)

### Возможности

Все что и оригинальный ransomdoors только у меня еще и баги есть)

### Требования

- Linux + Wayland/X11. Лучше всего на Hyprland и wlroots (Sway/labwc/wayfire/niri); также работает на GNOME/Mutter, KDE/KWin, COSMIC, XFCE, i3 через фолбэк (см. Примечания).
- Python 3 + `PyGObject` (GTK 3), `Pillow` (длительности GIF), `pycairo`. `GtkLayerShell 0.1` опционален — используется только на wlroots-композиторах, иначе работает фолбэк fullscreen/maximize.
- Опционально, авто-детект (побеждает первый найденный):
  - звук: `ffplay` → `pw-play` → `paplay` → `aplay`;
  - обои: `awww` → `swww` → `hyprpaper` (+`hyprctl`) → `swaybg` → `gsettings` (GNOME/MATE/Cinnamon) → `plasma-apply-wallpaperimage` (KDE) → `feh` (X11);
  - курсор/монитор: `hyprctl` → `swaymsg` → `xdotool`, плюс `wlr-randr` / `kscreen-doctor` для геометрии, иначе GDK-фолбэк;
  - `gio` (иконки монет).

### Установка и запуск

```bash
# системные зависимости (пример для Arch)
sudo pacman -S python-gobject gtk-layer-shell python-pillow python-cairo
# опциональные бэкенды (под каждую систему свой):
# sudo pacman -S ffmpeg pipewire-pulse libpulse alsa-utils awww swww hyprpaper swaybg feh xdotool wlr-randr

git clone https://github.com/VoidEmptiness/RansomDoors-Python && cd RansomDoors-Python && python3 RansomDoors.py
```

### Оплата

Номиналы: `.gold1`=10, `.gold2`=50, `.gold3`=100, `.gold4`=150, `.gold5`=200, `.gold6`=500. `.crucifix` обнуляет долг целиком.

Каждая монета — JSON `{"RANSOM_COIN": "<uuid>"}` со случайным именем, защита от повторного приёма по хешу содержимого. При оплате файл удаляется. При выходе свои монеты удаляются (кроме `--no-coin-cleanup`). Трек-лист: `~/.cache/ransom_coins.json`.

Сумма монет ≈ `--ransom-sum` (или `--coin-ransom`) + `--coin-extra 100`.

### Ключевые опции

```
--loops 1 --loss-loops 2 --thanks-loops 1 --repent-loops 1
--idle-timeout 30 --idle-min 4 --idle-max 6 --no-idle (пропуск засады)
--attack-scale 2.0 --sign-scale 2.0 --download-scale 1.0
--glitch-delay 350 --glitch-width 480
--shake-px 6 --shake-ms 120
--move-min 2 --move-max 10 --vis-min 2 --vis-max 6
--hide-chance 0.35 --show-chance 0.5 --max-visible 4 --min-visible 1 --max-cover 0.3
--ransom-sum 500 --rantime 90 --auto-quit 0
--coin-depth 6 --coin-chance 0.6 --coin-extra 100 --coin-honeypot 25 --coin-cruc 10
--coin-roots DIR (повторно) --coin-drawer --coin-seed N --coin-ransom N
--pay-file FILE (повторно, для тестов)
--seed N
--no-attack --no-loss --no-ransom --no-coins --no-floaters/--no-taunts
--no-vignette --no-sound --no-wallpaper --no-coin-cleanup --no-coin-icons
--no-fullscreen (окно 960x540 для отладки)
--fullscreen-mode auto|fullscreen|maximize (фолбэк без layer-shell; auto = maximize на GNOME/Mutter, иначе fullscreen)
--click-through (включено по умолчанию) / --no-click-through (оверлей ловит ввод)
```

Полный список: `python3 RansomDoors.py --help`.

### Структура

```
RansomDoors.py        # тонкий шим-точки входа
ransom_doors/
  __init__.py __main__.py
  app.py              # оркестрация: окно, этапы, глитчи, флоатеры, финалы, DnD
  cli.py              # argparse
  platform.py         # детект композитора, курсор, геометрия монитора, проверка layer-shell
  idle.py             # стартовая засада ransom_idle.png
  config.py           # константы, кандидаты путей, номиналы, звуки
  coins.py            # спавн .goldN/.crucifix, BFS-обход, трекинг
  gtkkit.py           # Sprite со степпингом/cover, fit_static, fake-окна (GtkLayerShell опционален)
  ransom_note.py      # GTK-реплика записки 560x400 + таймер
  sound.py            # SoundEngine (ffplay/pw-play/paplay/aplay)
  wallpaper.py        # swap/restore через awww/swww/hyprpaper/swaybg/gsettings/plasma/feh
  utils.py            # поиск ассетов, gif_info (PIL), pidfile, pick_monitor (через platform)
assets/
  downloading.gif ransom_attack.gif loss_no_vignette.gif red_vignette.gif
  thankyou.gif repent.gif ransom_idle.png Gold.png stop_sign.png
  darkred_wallpaper.png crucifix.png Gold/Gold1-5.png Gold/HoneyPot.png
  taunts/glitch1-5.* idiot.png tauntface.png tauntflower.png
  sounds/spawn.wav attack.wav install.wav layer1-3.wav cash.wav
         thankyou.wav crucifix.wav tauntSpawn.wav tauntLeave.wav
```

### Примечания

- Проект ищет ассеты по нескольким кандидатам (`assets/...`, рядом с файлом) и падает с понятной ошибкой только если нет `downloading.gif` или глитчей.
- Монеты по умолчанию кладутся в реальные `Desktop/Documents/Downloads/Music/Pictures/Videos/Projects` — для экспериментов используйте `--coin-drawer`.
- Бэкенд оверлея: layer-shell на wlroots (Hyprland/Sway/...); иначе обычный fullscreen поверх всех. На GNOME/Mutter настоящий fullscreen снимается с композита (unredirect) и прозрачность становится чёрной, поэтому `auto` использует развёрнутое окно без рамок — переключите через `--fullscreen-mode fullscreen|maximize`.
- Возврат обоев на KDE Plasma и `feh`/`swaybg` — по возможности: Plasma не отдаёт предыдущие обои, возможно придётся вернуть их вручную.
- Это не малварь: шифрования, сети и персистентности нет. Не используйте против других людей без их согласия.

### Авторы

- Doors создана LSPLASH. Сущность RANSOM/A-90, её название, внешний вид и концепция — их оригинальная работа; этот проект — неофициальное фанатское воссоздание, не связанное с LSPLASH и не одобренное ею. Поиграйте в настоящую игру.

[Наверх](#ransomdoors)
