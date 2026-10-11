"""GTK-реплика RansomWindow: вид 560x400 + живой обратный отсчёт."""
from .config import RANSOM_COIN_CANDIDATES, RANSOM_FACE_CANDIDATES, RANSOM_H, RANSOM_W
from .utils import find_first


def build_ransom_note(Gtk, Pango, GdkPixbuf, state, l3_started, music, finish_unpaid,
                      total, duration):
    """Возвращает (root, tick). Без drag&drop оплаты снаружи и без модалок."""
    root = Gtk.EventBox()
    root.set_name("ransom-root")
    root.set_size_request(RANSOM_W, RANSOM_H)
    box = Gtk.Fixed()
    box.set_size_request(RANSOM_W, RANSOM_H)
    root.add(box)

    def put(w, x, y):
        box.put(w, x, y)

    def bg_box(name, x, y, w, h):
        eb = Gtk.EventBox()
        eb.set_name(name)
        eb.set_size_request(w, h)
        put(eb, x, y)
        return eb

    def label(markup, font, x, y, w, h):
        lb = Gtk.Label()
        lb.set_markup(markup)
        lb.modify_font(Pango.FontDescription.from_string(font))
        lb.set_size_request(w, h)
        lb.set_line_wrap(True)
        lb.set_justify(Gtk.Justification.CENTER)
        put(lb, x, y)
        return lb

    face_path = find_first(RANSOM_FACE_CANDIDATES)
    if face_path:
        try:
            pix = GdkPixbuf.Pixbuf.new_from_file(face_path).scale_simple(
                188, 188, GdkPixbuf.InterpType.BILINEAR)
            put(Gtk.Image.new_from_pixbuf(pix), 28, 12)
        except Exception:
            pass
    label('<span foreground="white">YOUR FILES HAVE BEEN ENCRYPTED</span>',
          "Monospace Bold 21", 233, 9, 267, 154)
    bg_box("ransom-warnbg", 12, 166, 520, 109)
    label('<span foreground="white">IF YOU DO NOT PAY THIS RANSOM BEFORE THE '
          'TIMER ENDS, </span><span foreground="red">UNRECOVERABLE BY ANY MEANS.</span>',
          "Monospace Bold 13", 14, 168, 516, 105)
    bg_box("ransom-leftbg", 12, 286, 189, 62)
    sum_lbl = label(f'<span foreground="#ffcf25">{max(0, total)}</span>',
                    "Monospace Bold 24", 20, 288, 110, 59)
    coin_path = find_first(RANSOM_COIN_CANDIDATES)
    if coin_path:
        try:
            pix = GdkPixbuf.Pixbuf.new_from_file(coin_path).scale_simple(
                59, 58, GdkPixbuf.InterpType.BILINEAR)
            put(Gtk.Image.new_from_pixbuf(pix), 133, 288)
        except Exception:
            pass
    bg_box("ransom-timerbg", 218, 286, 314, 62)
    timer_lbl = label("", "Monospace Bold 22", 218, 286, 314, 62)

    st = {"left": max(0, duration), "total": max(0, total), "paid": False,
          "dur": max(0, duration)}

    def refresh():
        t = st["left"]
        timer_lbl.set_markup(
            f'<span foreground="black">TIME: {t // 60:02d}:{t % 60:02d}</span>')

    def refresh_sum():
        sum_lbl.set_markup(
            f'<span foreground="#ffcf25">{max(0, st["total"])}</span>')

    def tick():
        if st.get("paid") or state.get("finished"):
            return False
        st["left"] = max(0, st["left"] - 1)
        refresh()
        dur = st.get("dur", 0)  # фоновая музыка: layer2 со второй трети;
        if dur > 0:  # layer3 — отдельным разовым пуском впритык к концу
            el = dur - st["left"]
            if dur / 3 <= el < 2 * dur / 3 and not l3_started["v"]:
                music("layer2")
        if st["left"] <= 0:
            print("ransom note: TIME UP — не уплачено", flush=True)
            finish_unpaid()
            return False
        return True

    refresh()
    return root, {"tick": tick, "st": st, "refresh_sum": refresh_sum}
