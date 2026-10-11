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

- Linux + Wayland, preferably Hyprland (`hyprctl` to pick the focused monitor, otherwise — the monitor under the cursor).
- Python 3 + `PyGObject` (GTK 3), `GtkLayerShell 0.1`, `Pillow` (GIF durations), `pycairo`.
- Optional: `ffplay` (music loops) or `paplay`, `awww` (wallpaper), `gio` (coin icons).

### Installation and Launch

Not yet available, working on cross-platform support.

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
--no-click-through (overlay captures input)
```

Full list: `python3 RansomDoors.py --help`.

### Structure

```
RansomDoors.py        # thin entry-point shim
ransom_doors/
  __init__.py __main__.py
  app.py              # orchestration: window, stages, glitches, floaters, finals, DnD
  cli.py              # argparse
  idle.py             # starting ambush ransom_idle.png
  config.py           # constants, path candidates, denominations, sounds
  coins.py            # spawn .goldN/.crucifix, BFS traversal, tracking
  gtkkit.py           # Sprite with stepping, fit_static, fake windows
  ransom_note.py      # GTK replica of the note 560x400 + timer
  sound.py            # SoundEngine (ffplay/paplay)
  wallpaper.py        # swap/restore via awww
  utils.py            # asset lookup, gif_info (PIL), pidfile, pick_monitor
assets/
  downloading.gif ransom_attack.gif loss_no_vignette.gif red_vignette.gif
  thankyou.gif repent.gif ransom_idle.png Gold.png stop_sign.png
  darkred_wallpaper.png crucifix.png Gold/Gold1-5.png Gold/HoneyPot.png
  taunts/glitch1-5.* idiot.png tauntface.png tauntflower.png
  sounds/spawn.wav attack.wav install.wav layer1-3.wav cash.wav
         thankyou.wav crucifix.wav tauntSpawn.wav tauntLeave.wav
```

### Notes

- The project looks for assets among several candidates (`assets/...`, next to the code) and fails with a clear error only if `downloading.gif` or the glitches are missing.
- By default coins are placed in the real `Desktop/Documents/Downloads/Music/Pictures/Videos/Projects` — use `--coin-drawer` for experiments.
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

- Linux + Wayland, желательно Hyprland (`hyprctl` для выбора фокусного монитора, иначе — монитор под курсором).
- Python 3 + `PyGObject` (GTK 3), `GtkLayerShell 0.1`, `Pillow` (длительности GIF), `pycairo`.
- Опционально: `ffplay` (музыка-лупы) или `paplay`, `awww` (обои), `gio` (иконки монет).

### Установка и запуск

Пока что нету, делаю кросплатформеность

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
--no-click-through (оверлей ловит ввод)
```

Полный список: `python3 RansomDoors.py --help`.

### Структура

```
RansomDoors.py        # тонкий шим-точки входа
ransom_doors/
  __init__.py __main__.py
  app.py              # оркестрация: окно, этапы, глитчи, флоатеры, финалы, DnD
  cli.py              # argparse
  idle.py             # стартовая засада ransom_idle.png
  config.py           # константы, кандидаты путей, номиналы, звуки
  coins.py            # спавн .goldN/.crucifix, BFS-обход, трекинг
  gtkkit.py           # Sprite со степпингом, fit_static, fake-окна
  ransom_note.py      # GTK-реплика записки 560x400 + таймер
  sound.py            # SoundEngine (ffplay/paplay)
  wallpaper.py        # swap/restore через awww
  utils.py            # поиск ассетов, gif_info (PIL), pidfile, pick_monitor
assets/
  downloading.gif ransom_attack.gif loss_no_vignette.gif red_vignette.gif
  thankyou.gif repent.gif ransom_idle.png Gold.png stop_sign.png
  darkred_wallpaper.png crucifix.png Gold/Gold1-5.png Gold/HoneyPot.png
  taunts/glitch1-5.* idiot.png tauntface.png tauntflower.png
  sounds/spawn.wav attack.wav install.wav layer1-3.wav cash.wav
         thankyou.wav crucifix.wav tauntSpawn.wav tauntLeave.wav
```

### Примечания

- Проект ищет ассеты по нескольким кандидатам (`assets/...`, рядом с кодом) и падает с понятной ошибкой только если нет `downloading.gif` или глитчей.
- Монеты по умолчанию кладутся в реальные `Desktop/Documents/Downloads/Music/Pictures/Videos/Projects` — для экспериментов используйте `--coin-drawer`.
- Это не малварь: шифрования, сети и персистентности нет. Не используйте против других людей без их согласия.

### Авторы

- Doors создана LSPLASH. Сущность RANSOM/A-90, её название, внешний вид и концепция — их оригинальная работа; этот проект — неофициальное фанатское воссоздание, не связанное с LSPLASH и не одобренное ею. Поиграйте в настоящую игру.

[Наверх](#ransomdoors)
