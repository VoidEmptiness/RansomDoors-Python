"""CLI: argparse для всех опций оверлея."""
import argparse
import sys


def build_parser():
    ap = argparse.ArgumentParser(description="downloading впереди + attack позади, затем глитчи (layer-shell оверлей)")
    ap.add_argument("--loops", type=int, default=1,
                    help="сколько раз проиграть downloading.gif (1 проход ~1.4с). По умолчанию 1.")
    ap.add_argument("--attack-scale", type=float, default=2.0,
                    help="масштаб прыгающего ransom_attack.gif 200x200 * scale. По умолчанию 2.0.")
    ap.add_argument("--sign-scale", type=float, default=2.0,
                    help="масштаб stop_sign.png 200x200 * scale позади downloading. По умолчанию 2.0.")
    ap.add_argument("--download-scale", type=float, default=1.0,
                    help="масштаб downloading.gif 700x160 * scale. По умолчанию 1.0.")
    ap.add_argument("--glitch-delay", type=int, default=350,
                    help="пауза между появлением глитчей, мс. По умолчанию 350.")
    ap.add_argument("--glitch-width", type=int, default=480,
                    help="ширина окна глитча (высота по пропорциям, влезает в экран). По умолчанию 480.")
    ap.add_argument("--seed", type=int, default=None, help="seed рандома позиций/порядка")
    ap.add_argument("--shake-px", type=int, default=6,
                    help="амплитуда тряски глитчей, px (0 — без тряски). По умолчанию 6.")
    ap.add_argument("--shake-ms", type=int, default=120,
                    help="интервал тряски глитчей, мс. По умолчанию 120.")
    ap.add_argument("--move-min", type=float, default=2.0,
                    help="мин. пауза перед прыжком глитчей на новые позиции, сек. По умолчанию 2.")
    ap.add_argument("--move-max", type=float, default=10.0,
                    help="макс. пауза перед прыжком глитчей (0 — не прыгают). По умолчанию 10.")
    ap.add_argument("--hide-chance", type=float, default=0.35,
                    help="шанс 0..1 что видимый глитч скроется за тик. По умолчанию 0.35.")
    ap.add_argument("--show-chance", type=float, default=0.5,
                    help="шанс 0..1 что скрытый глитч появится за тик. По умолчанию 0.5.")
    ap.add_argument("--vis-min", type=float, default=2.0,
                    help="мин. пауза между тиками видимости, сек. По умолчанию 2.")
    ap.add_argument("--vis-max", type=float, default=6.0,
                    help="макс. пауза между тиками видимости (0 — без скрытий). По умолчанию 6.")
    ap.add_argument("--max-visible", type=int, default=4,
                    help="максимум одновременно видимых глитчей. По умолчанию 4.")
    ap.add_argument("--max-cover", type=float, default=0.3,
                    help="макс. доля записки, которую могут закрывать глитчи (0..1). По умолчанию 0.3.")
    ap.add_argument("--min-visible", type=int, default=1,
                    help="минимум одновременно видимых глитчей. По умолчанию 1.")
    ap.add_argument("--no-ransom", action="store_true",
                    help="не показывать ransom-записку на этапе 2")
    ap.add_argument("--no-coins", action="store_true",
                    help="не разбрасывать монетки перед запиской")
    ap.add_argument("--coin-ransom", type=int, default=None,
                    help="цель суммы монет (по умолч. = --ransom-sum)")
    ap.add_argument("--coin-extra", type=int, default=100,
                    help="сверху к цели: сумма монет = счёт + extra. По умолчанию 100.")
    ap.add_argument("--coin-depth", type=int, default=6,
                    help="глубина обхода подпапок. По умолчанию 6.")
    ap.add_argument("--coin-chance", type=float, default=0.6,
                    help="шанс положить монету в папку (0..1). По умолчанию 0.6.")
    ap.add_argument("--coin-roots", action="append", default=[],
                    help="корневые папки для монет (можно несколько раз)")
    ap.add_argument("--coin-drawer", action="store_true",
                    help="монеты в /tmp/RansomDrawers/run-xxx вместо реальных папок")
    ap.add_argument("--coin-honeypot", type=float, default=25,
                    help="шанс .gold6-халявы, %%. По умолчанию 25.")
    ap.add_argument("--coin-cruc", type=float, default=10,
                    help="шанс .crucifix, %%. По умолчанию 10.")
    ap.add_argument("--coin-seed", type=int, default=None,
                    help="seed спавна монет (по умолч. случайно)")
    ap.add_argument("--no-coin-cleanup", action="store_true",
                    help="не удалять наши монетки при выходе")
    ap.add_argument("--no-coin-icons", action="store_true",
                    help="не ставить иконки монеткам (gio metadata)")
    ap.add_argument("--thanks-loops", type=int, default=1,
                    help="сколько раз проиграть thankyou.gif после оплаты. По умолчанию 1.")
    ap.add_argument("--repent-loops", type=int, default=1,
                    help="сколько раз проиграть repent.gif при победе крестом. По умолчанию 1.")
    ap.add_argument("--pay-file", action="append", default=[],
                    help="файл-монета (.goldN/.crucifix), применить как сброс без "
                         "перетаскивания (можно несколько раз). Для тестов.")
    ap.add_argument("--no-sound", action="store_true",
                    help="без звуков")
    ap.add_argument("--no-wallpaper", action="store_true",
                    help="не менять обои на время работы")
    ap.add_argument("--no-taunts", action="store_true",
                    help="без фоновых окошек (алиас --no-floaters)")
    ap.add_argument("--no-floaters", action="store_true",
                    help="без фоновых окошек")
    ap.add_argument("--ransom-sum", type=int, default=500,
                    help="сумма выкупа на записке. По умолчанию 500.")
    ap.add_argument("--rantime", type=int, default=90,
                    help="таймер записки, сек. По умолчанию 90.")
    ap.add_argument("--auto-quit", type=float, default=0,
                    help="закрыть всё через N сек после глитчей (0 — не закрывать).")
    ap.add_argument("--no-attack", action="store_true", help="без ransom_attack.gif")
    ap.add_argument("--no-vignette", action="store_true",
                    help="без красной виньетки поверх всего")
    ap.add_argument("--no-loss", action="store_true",
                    help="пропустить loss_no_vignette.gif перед downloading")
    ap.add_argument("--loss-loops", type=int, default=2,
                    help="сколько раз проиграть loss_no_vignette (1 проход ~1с). По умолчанию 2.")
    ap.add_argument("--no-shutdown", action="store_true",
                    help="не выключать комп при проигрыше (по умолчанию выключает)")
    ap.add_argument("--shutdown-cmd", default="shutdown now",
                    help="команда выключения при проигрыше. По умолчанию 'shutdown now'.")
    ap.add_argument("--click-through", action="store_true", default=True,
                    help="клики проходят сквозь оверлей (по умолчанию включено)")
    ap.add_argument("--no-click-through", action="store_true",
                    help="оверлей ловит клики/клавиатуру (Esc/правый клик закрывают)")
    ap.add_argument("--no-fullscreen", action="store_true",
                    help="обычное окно 960x540 вместо оверлея (отладка)")
    ap.add_argument("--fullscreen-mode", choices=("auto", "fullscreen", "maximize"),
                    default="auto",
                    help="fullscreen-фолбэк (без layer-shell): fullscreen — настоящий "
                         "фулскрин (на GNOME/Mutter может дать чёрный фон из-за "
                         "unredirect), maximize — развёрнутое окно без рамок "
                         "(прозрачность сохраняется, сверху видна панель). "
                         "auto: на gnome/mutter — maximize, иначе fullscreen.")
    ap.add_argument("--no-idle", action="store_true",
                    help="пропустить стартовую засаду ransom_idle.png, сразу основной скрипт")
    ap.add_argument("--idle-timeout", type=float, default=30,
                    help="секунд без мыши и клавиш до выключения засады. По умолчанию 30.")
    ap.add_argument("--idle-min", type=float, default=4.0,
                    help="мин. пауза показа/скрытия ransom_idle.png, сек. По умолчанию 4.")
    ap.add_argument("--idle-max", type=float, default=6.0,
                    help="макс. пауза показа/скрытия ransom_idle.png, сек. По умолчанию 6.")
    return ap


def parse_args(argv=None):
    a = build_parser().parse_args(argv)
    if a.loops < 1:
        print("--loops должен быть >= 1", file=sys.stderr)
        raise SystemExit(1)
    a.hide_chance = max(0.0, min(1.0, a.hide_chance))
    a.show_chance = max(0.0, min(1.0, a.show_chance))
    a.max_visible = max(1, a.max_visible)
    a.min_visible = max(1, min(a.min_visible, a.max_visible))
    a.max_cover = max(0.0, min(1.0, a.max_cover))
    a.idle_min = max(0.0, a.idle_min)
    a.idle_max = max(a.idle_min, a.idle_max)
    a.idle_timeout = max(1.0, a.idle_timeout)
    return a
