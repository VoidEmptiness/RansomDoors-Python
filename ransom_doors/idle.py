"""Стартовая засада: мигающий ransom_idle.png в окне основного скрипта.

Отдельного окна нет: картинка кладётся в fixed главного оверлея
(App.win/App.fixed) и мигает там. После триггера/таймаута картинка
убирается и тот же statements окно продолжает основной сценарий.

Логика:
- в самом начале ransom_idle.png случайно появляется на экране;
- раз в idle-min..idle-max сек скрывается, через столько же снова
  показывается в новом случайном месте;
- если в момент, пока он ВИДЕН, шевельнуть мышью или нажать клавишу —
  возвращается True (продолжать основной скрипт в том же окне);
- если idle-timeout сек нет никакой активности (ни мыши, ни клавиш) —
  возвращается False (скрипт выключается).

Мышь отслеживается глобально через API композитора (фоновый поток,
ничего не блокирует): hyprctl cursorpos (Hyprland), swaymsg (Sway),
xdotool (X11). Клавиатура — через key-press-event оверлея
(GtkLayerShell EXCLUSIVE на время засады, потом режим возвращается;
указатель при этом пропускается сквозь окно 1x1 input-shape).
Без внешнего API — запасной опрос указателя через GDK в главном потоке.
"""
import signal
import threading
import time

from .config import RANSOM_FACE_CANDIDATES
from .platform import cursor_backend_name, get_cursor_pos
from .utils import find_first


def _hypr_pos():
    """Совместимость: раньше idle опрашивал только hyprctl напрямую."""
    return get_cursor_pos()


def run_idle_ambush(app):
    """Мигание ransom_idle.png в окне app. True — триггер, False — таймаут."""
    a = app.a
    rng = app.rng
    Gtk, Gdk, GtkLayerShell, GLib = app.Gtk, app.Gdk, app.GtkLayerShell, app.GLib
    cairo = app.cairo
    win, fixed, W, H = app.win, app.fixed, app.W, app.H

    face = find_first(RANSOM_FACE_CANDIDATES)
    if not face:
        print("idle: ransom_idle.png не найден — сразу основной скрипт",
              flush=True)
        return True

    lo = max(0.0, float(getattr(a, "idle_min", 4.0)))
    hi = max(lo, float(getattr(a, "idle_max", 6.0)))
    timeout = max(1.0, float(getattr(a, "idle_timeout", 30.0)))

    def rand_ms():
        return int(rng.uniform(lo, hi) * 1000)

    try:
        pix = app.GdkPixbuf.Pixbuf.new_from_file(face)
    except Exception as e:
        print(f"idle: не смог открыть {face}: {e} — сразу основной скрипт",
              flush=True)
        return True
    iw, ih = pix.get_width(), pix.get_height()

    img = Gtk.Image.new_from_pixbuf(pix)
    img.set_size_request(iw, ih)
    placed = {"v": False}

    st = {"visible": False, "done": False, "result": False,
          "start": time.monotonic(), "last": time.monotonic(),
          "mouse_moved": False, "win_xy": None}

    def trigger(src):
        if st["done"]:
            return
        st["done"] = True
        st["result"] = True
        print(f"idle: {src} пока ransom_idle.png виден — запускаю основной скрипт",
              flush=True)
        Gtk.main_quit()

    def on_key(w, event):
        if st["done"]:
            return False
        st["last"] = time.monotonic()
        if st["visible"]:
            trigger("нажата клавиша")
        return False

    def on_button(w, event):
        if st["done"]:
            return False
        st["last"] = time.monotonic()
        if st["visible"]:
            trigger("мышь")
        return False

    def on_motion(w, event):
        # запасной путь (оконный режим без hyprctl): любое движение
        if st["done"]:
            return False
        xy = (int(event.x), int(event.y))
        if st["win_xy"] is None:
            st["win_xy"] = xy
        elif xy != st["win_xy"]:
            st["win_xy"] = xy
            st["last"] = time.monotonic()
            if st["visible"]:
                trigger("мышь")
        return False

    def do_show():
        if st["done"]:
            return False
        x = rng.randint(0, max(0, W - iw))
        y = rng.randint(0, max(0, H - ih))
        try:
            if not placed["v"]:
                fixed.put(img, x, y)
                placed["v"] = True
            else:
                fixed.move(img, x, y)
            img.show()
        except Exception:
            pass
        st["visible"] = True
        print(f"idle: ransom_idle.png показался at {x},{y}", flush=True)
        GLib.timeout_add(rand_ms(), do_hide)
        return False

    def do_hide():
        if st["done"]:
            return False
        try:
            img.hide()
        except Exception:
            pass
        st["visible"] = False
        print("idle: ransom_idle.png скрылся", flush=True)
        GLib.timeout_add(rand_ms(), do_show)
        return False

    # ---------- мышь: фоновый опрос hyprctl или GDK в главном потоке ----------
    def gdk_pos():
        try:
            disp = Gdk.Display.get_default()
            try:
                _scr, x, y, _mask = disp.get_pointer()
                return (int(x), int(y))
            except Exception:
                pass
            seat = disp.get_default_seat()
            ptr = seat.get_pointer()
            try:
                _scr, x, y = ptr.get_position()
                return (int(x), int(y))
            except Exception:
                return None
        except Exception:
            return None

    backend = cursor_backend_name()
    use_ext = backend in ("hyprctl", "swaymsg", "xdotool")
    stop = threading.Event()

    if use_ext:
        print(f"idle: слежу за мышью через {backend} (глобально)", flush=True)

        def poll():
            last = _hypr_pos()
            fails = 0
            while not stop.is_set():
                pos = _hypr_pos()
                if pos is None:
                    fails += 1
                    if fails > 25:  # бэкенд мёртв ~5с — сдаёмся
                        break
                    stop.wait(0.2)
                    continue
                fails = 0
                if last is None:
                    last = pos
                elif pos != last:
                    last = pos
                    st["mouse_moved"] = True
                stop.wait(0.08)
        threading.Thread(target=poll, daemon=True).start()
        last_gdk = {"v": None}
    else:
        print("idle: внешнего API курсора нет — слежу за мышью через GDK (только над окном)",
              flush=True)
        last_gdk = {"v": gdk_pos()}

    def check():
        if st["done"]:
            return False
        now = time.monotonic()
        if st.pop("mouse_moved", False):
            st["last"] = now
            if st["visible"]:
                trigger("мышь")
                return False
        if not use_ext:
            pos = gdk_pos()
            if pos is not None:
                if last_gdk["v"] is None:
                    last_gdk["v"] = pos
                elif pos != last_gdk["v"]:
                    last_gdk["v"] = pos
                    st["last"] = now
                    if st["visible"]:
                        trigger("мышь")
                        return False
        if now - st["last"] >= timeout:
            st["done"] = True
            st["result"] = False
            print(f"idle: {timeout:g}с без мыши и клавиш — выключаюсь",
                  flush=True)
            Gtk.main_quit()
            return False
        return True

    # ---------- сигналы: гасимся тихо, pidfile уберёт вызывающий код ----------
    old_term = signal.getsignal(signal.SIGTERM)
    old_int = signal.getsignal(signal.SIGINT)

    def _on_sig(signum, frame):
        st["done"] = True
        st["result"] = False

    try:
        signal.signal(signal.SIGTERM, _on_sig)
        signal.signal(signal.SIGINT, _on_sig)
    except Exception:
        pass

    hid_key = hid_btn = hid_motion = None
    try:
        hid_key = win.connect("key-press-event", on_key)
        hid_btn = win.connect("button-press-event", on_button)
        try:
            win.add_events(Gdk.EventMask.POINTER_MOTION_MASK
                           | Gdk.EventMask.KEY_PRESS_MASK
                           | Gdk.EventMask.BUTTON_PRESS_MASK)
        except Exception:
            pass
        hid_motion = win.connect("motion-notify-event", on_motion)

        app.idle_active = True
        if not a.no_fullscreen:
            # на время засады забираем клавиатуру себе (только layer-shell)
            try:
                if GtkLayerShell is not None and getattr(app, "using_layershell", False):
                    GtkLayerShell.set_keyboard_mode(
                        win, GtkLayerShell.KeyboardMode.EXCLUSIVE)
            except Exception:
                pass
        win.show_all()
        img.hide()
        st["visible"] = False
        if not a.no_fullscreen:
            # указатель — сквозь (1x1), клавиатура остаётся у нас (EXCLUSIVE)
            try:
                reg = cairo.Region(cairo.RectangleInt(0, 0, 1, 1))
                win.input_shape_combine_region(reg)
            except Exception:
                pass
        print(f"idle: засада — ransom_idle.png мигает раз в {lo:g}-{hi:g}с, "
              f"шевеление/клавиша пока виден = старт, "
              f"{timeout:g}с тишины = выход", flush=True)
        GLib.timeout_add(120, check)
        GLib.idle_add(do_show)
        Gtk.main()
    finally:
        stop.set()
        app.idle_active = False
        for hid in (hid_key, hid_btn, hid_motion):
            if hid is not None:
                try:
                    win.disconnect(hid)
                except Exception:
                    pass
        try:
            if placed["v"]:
                fixed.remove(img)
        except Exception:
            pass
        try:
            img.destroy()
        except Exception:
            pass
        if not a.no_fullscreen:
            # вернуть режим клавиатуры основного скрипта (только layer-shell)
            try:
                if GtkLayerShell is not None and getattr(app, "using_layershell", False):
                    GtkLayerShell.set_keyboard_mode(
                        win, GtkLayerShell.KeyboardMode.NONE if app.click_through
                        else GtkLayerShell.KeyboardMode.ON_DEMAND)
            except Exception:
                pass
            try:
                app.pin_click_through(force=True)
            except Exception:
                pass
        try:
            signal.signal(signal.SIGTERM, old_term)
            signal.signal(signal.SIGINT, old_int)
        except Exception:
            pass
    return st["result"]
