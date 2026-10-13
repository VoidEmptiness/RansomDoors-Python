"""GTK-хелперы: Sprite с ручным степпингом, fake-окна, заголовки."""
from .config import TITLE_H, WINDOW_TITLES


def ensure_gtk():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    try:
        gi.require_version('GtkLayerShell', '0.1')
        from gi.repository import GtkLayerShell
    except Exception:
        GtkLayerShell = None  # GNOME/KDE/COSMIC или нет биндинга — фолбэк ниже
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
    import cairo
    return Gtk, Gdk, GtkLayerShell, GdkPixbuf, GLib, Pango, cairo


class Sprite:
    def __init__(self, GdkPixbuf, Gtk, gif, target_w, screen_w, screen_h,
                 cover=False):
        self._GdkPixbuf = GdkPixbuf
        self._Gtk = Gtk
        self._W = screen_w
        self._H = screen_h
        self.cover = bool(cover)
        self.anim = GdkPixbuf.PixbufAnimation.new_from_file(gif)
        self.iter = self.anim.get_iter(None)
        self.image = Gtk.Image()
        self.target_w = target_w
        self.frames = 0

    def size_for(self, pix):
        W, H = self._W, self._H
        w, h = pix.get_width(), pix.get_height()
        if self.cover:
            # Залить экран целиком без искажения пропорций: масштаб по
            # большей стороне, лишнее обрежется по центру в render().
            s = max(W / max(1, w), H / max(1, h))
            return max(1, int(w * s + 0.5)), max(1, int(h * s + 0.5))
        tw = self.target_w or w
        tw = min(tw, W)
        th = max(1, int(h * tw / max(1, w)))
        if th > H:  # влезаем по высоте
            th, tw = H, max(1, int(w * H / max(1, h)))
        return tw, th

    def render(self):
        pix = self.iter.get_pixbuf()
        tw, th = self.size_for(pix)
        if (tw, th) != (pix.get_width(), pix.get_height()):
            pix = pix.scale_simple(tw, th, self._GdkPixbuf.InterpType.BILINEAR)
        if self.cover:
            # Центрокроп ровно под экран (tw>=W, th>=H гарантировано).
            x, y = (tw - self._W) // 2, (th - self._H) // 2
            if (tw, th) != (self._W, self._H):
                pix = pix.new_subpixbuf(x, y, self._W, self._H)
            self.image.set_from_pixbuf(pix)
            return self._W, self._H
        self.image.set_from_pixbuf(pix)
        return tw, th

    def delay(self):
        try:
            d = int(self.iter.get_delay_time())
        except Exception:
            d = 100
        return d if d and d > 0 else 100

    def step(self):
        d = self.delay()
        size = self.render()
        self.frames += 1
        try:
            self.iter.advance(None)
        except Exception:
            pass
        return d, size


def fit_static(GdkPixbuf, path, max_w, W, H):
    pix = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pix.get_width(), pix.get_height()
    tw = min(max_w, W)
    th = max(1, int(h * tw / max(1, w)))
    if th > H:
        th, tw = H, max(1, int(w * H / max(1, h)))
    return pix.scale_simple(tw, th, GdkPixbuf.InterpType.BILINEAR), tw, th


def random_title(rng):
    return rng.choice(WINDOW_TITLES)


def set_title(GLib, lbl, text):
    """Текст заголовка явно тёмным: в тёмной теме системы дефолтный цвет
    метки светлый и на белой полосе его не видно."""
    try:
        lbl.set_markup(
            f'<span foreground="#1a1a1a">{GLib.markup_escape_text(text)}</span>')
    except Exception:
        try:
            lbl.set_text(text)
        except Exception:
            pass


def make_fake_window(Gtk, Pango, GLib, rng, content, cw, ch):
    """Искусственное окно как в винде: белая полоска со случайным
    названием + кнопки, под ней контент. Возвращает (frame, title_label)."""
    frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    bar = Gtk.EventBox()
    bar.set_name("fake-titlebar")
    bar.set_size_request(cw, TITLE_H)
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    hbox.set_size_request(cw, TITLE_H)
    title = Gtk.Label()
    set_title(GLib, title, random_title(rng))
    title.modify_font(Pango.FontDescription.from_string("Sans 11"))
    title.set_halign(Gtk.Align.START)
    title.set_valign(Gtk.Align.CENTER)
    title.set_xalign(0.0)  # текст прижат к левому краю полосы
    title.set_ellipsize(Pango.EllipsizeMode.END)
    title.set_size_request(max(50, cw - 16), TITLE_H)
    title.set_margin_start(8)
    title.set_margin_end(8)
    hbox.pack_start(title, True, True, 0)
    bar.add(hbox)
    frame.pack_start(bar, False, False, 0)
    frame.pack_start(content, False, False, 0)
    return frame, title, bar
