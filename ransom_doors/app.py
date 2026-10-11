"""Оркестрация оверлея: окно, этапы loss/stage1/глитчи, финалы, DnD, монеты."""
import os
import random
import sys
import threading

from . import gtkkit
from .coins import _rm, _rmdir, coin_id, get_user_folders, save_track, spawn_deep
from .config import (
    ATTACK_CANDIDATES,
    CORNER_MS,
    CORNERS,
    DOWNLOAD_CANDIDATES,
    ICON_BY_EXT,
    LAYER_NAMESPACE,
    LOSS_CANDIDATES,
    OVERLAY_TITLE,
    RANSOM_H,
    RANSOM_W,
    REPENT_CANDIDATES,
    SIGN_CANDIDATES,
    TAUNT_CANDIDATES,
    THANKS_CANDIDATES,
    TITLE_H,
    VIGNETTE_CANDIDATES,
)
from .ransom_note import build_ransom_note
from .sound import SoundEngine
from .utils import (
    find_first,
    find_glitches,
    gif_info,
    pick_monitor,
    remove_pidfile,
    toggle_existing,
    write_pidfile,
)
from .wallpaper import WallpaperManager


class App:
    def __init__(self, a):
        self.a = a
        self.rng = random.Random(a.seed)
        self.click_through = a.click_through and not a.no_click_through
        self.snd = SoundEngine(no_sound=a.no_sound)
        self.rep_info = {"path": None, "n": 0, "ms": 0, "ready": False}

        self.dl_gif = find_first(DOWNLOAD_CANDIDATES)
        self.at_gif = find_first(ATTACK_CANDIDATES)
        self.sign_png = find_first(SIGN_CANDIDATES)
        self.glitches, self.missing = find_glitches()

        # GTK-ссылки проставляются в run() до использования
        self.Gtk = self.Gdk = self.GtkLayerShell = None
        self.GdkPixbuf = self.GLib = self.Pango = self.cairo = None

        self.win = None
        self.fixed = None
        self.W, self.H = 960, 540
        self.pin_state = {"last": None}

        self.ransom_state = {"widget": None, "bx": 0, "by": 0, "px": 0, "py": 0,
                             "title": None, "api": None, "used": set(), "drag": False}
        self.state = {"done": False, "finished": False, "quit": False}
        self.idle_active = False

        self.vig_img = None
        self.vig_pos = (0, 0)
        self.vig = None
        self.vig_gone = {"v": False}

        self.attack = None
        self.corners = {"seq": [], "aw": 200, "ah": 200, "bx": 0, "by": 0}
        self.dl = None
        self.dl_n = 0
        self.dl_loop_ms = 0
        self.sign_img = None

        self.order = []
        self.glitch_items = []  # [frame, tw, fh, base_x, base_y, path, visible, title_label]
        self.floater_items = []  # [frame, base_x, base_y]

        self.stage = {"stage1": False}
        self.attack_chained = {"v": False}
        self.l3_started = {"v": False}

        self.coin_state = {"files": [], "dirs": []}
        self.wall = WallpaperManager(disabled=a.no_wallpaper)
        self.loss_gif = None

    # ---------- мелкие хелперы ----------
    def _sprite(self, gif, target_w):
        return gtkkit.Sprite(self.GdkPixbuf, self.Gtk, gif, target_w, self.W, self.H)

    def _fit_static(self, path, max_w):
        return gtkkit.fit_static(self.GdkPixbuf, path, max_w, self.W, self.H)

    def _make_fake_window(self, content, cw, ch):
        return gtkkit.make_fake_window(self.Gtk, self.Pango, self.GLib, self.rng,
                                       content, cw, ch)

    def _random_title(self):
        return gtkkit.random_title(self.rng)

    def _set_title(self, lbl, text):
        return gtkkit.set_title(self.GLib, lbl, text)

    def _repent_scan(self):
        try:
            rp = find_first(REPENT_CANDIDATES)
            if rp:
                n, ms = gif_info(rp)
                self.rep_info.update(path=rp, n=n, ms=ms, ready=True)
        except Exception:
            pass

    # ---------- input shape ----------
    def pin_click_through(self, force=False):
        """Держать input shape = прямоугольник записки (или 1x1 без неё)."""
        a = self.a
        if not (self.click_through and not a.no_fullscreen):
            return False
        try:
            rw = self.ransom_state.get("widget")
            if rw is not None and not a.no_ransom:
                key = ("r", self.ransom_state.get("px", 0), self.ransom_state.get("py", 0),
                       RANSOM_W, RANSOM_H + TITLE_H)
            else:
                key = ("tiny",)
            if not force and key == self.pin_state["last"]:
                return False
            self.pin_state["last"] = key
            if key[0] == "r":
                _, x, y, w, h = key
                reg = self.cairo.Region(self.cairo.RectangleInt(x, y, w, h))
            else:
                reg = self.cairo.Region(self.cairo.RectangleInt(0, 0, 1, 1))
            self.win.input_shape_combine_region(reg)
        except Exception:
            pass
        return False

    # ---------- виньетка ----------
    def on_vig_motion(self, w, ctx, x, y, time):
        nr = self.note_rect()
        if nr is not None:
            nx, ny, nw, nh = nr
            ax = w.get_allocation().x + x
            ay = w.get_allocation().y + y
            if nx <= ax <= nx + nw and ny <= ay <= ny + nh:
                self.ransom_state["drag"] = True
        return False

    def on_vig_leave(self, w, ctx, time):
        self.ransom_state["drag"] = False

    def on_vig_drop(self, w, ctx, x, y, data, info, time):
        self.ransom_state["drag"] = False
        nr = self.note_rect()
        ok = False
        if nr is not None:
            nx, ny, nw, nh = nr
            ax = w.get_allocation().x + x
            ay = w.get_allocation().y + y
            if nx <= ax <= nx + nw and ny <= ay <= ny + nh:
                try:
                    uris = data.get_uris() or []
                except Exception:
                    uris = []
                ok = self.apply_drop_uris(uris)
        try:
            self.Gtk.drag_finish(ctx, ok, False, time)
        except Exception:
            pass

    def hide_vignette(self):
        """Спрятать виньетку (перед thankyou) и не воскрешать."""
        self.vig_gone["v"] = True
        try:
            self.fixed.remove(self.vig_img)
        except Exception:
            pass
        try:
            if self.vig_img is not None:
                self.vig_img.hide()
        except Exception:
            pass

    def raise_vignette(self):
        """Виньетка поверх всего: перекладка в конец стека Fixed."""
        if self.vig_img is None or self.vig_gone["v"]:
            return
        try:
            self.fixed.remove(self.vig_img)
        except Exception:
            pass
        try:
            self.fixed.put(self.vig_img, self.vig_pos[0], self.vig_pos[1])
            self.vig_img.show()
        except Exception:
            pass

    def _setup_vignette(self):
        a = self.a
        if a.no_vignette:
            return
        vig_gif = find_first(VIGNETTE_CANDIDATES)
        if not vig_gif:
            print("red_vignette.gif не найден — без виньетки", flush=True)
            return
        self.vig = self._sprite(vig_gif, self.W)
        vw, vh = self.vig.render()
        self.vig_pos = ((self.W - vw) // 2, (self.H - vh) // 2)
        self.vig_img = self.vig.image
        self.fixed.put(self.vig_img, self.vig_pos[0], self.vig_pos[1])
        self.vig_img.drag_dest_set(self.Gtk.DestDefaults.ALL, [], self.Gdk.DragAction.COPY)
        self.vig_img.drag_dest_add_uri_targets()
        self.vig_img.connect("drag-data-received", self.on_vig_drop)
        self.vig_img.connect("drag-motion", self.on_vig_motion)
        self.vig_img.connect("drag-leave", self.on_vig_leave)

        def vig_tick():
            if self.vig_gone["v"]:
                return False
            d, _ = self.vig.step()
            self.GLib.timeout_add(d, vig_tick)
            return False

        vig_tick()

    # ---------- геометрия записки/глитчей ----------
    def note_rect(self):
        if self.ransom_state.get("widget") is None or self.a.no_ransom:
            return None
        return (self.ransom_state["bx"], self.ransom_state["by"],
                RANSOM_W, RANSOM_H + TITLE_H)

    def note_cover(self, nr=None, skip=None, add=None):
        if nr is None:
            nr = self.note_rect()
        if nr is None:
            return 0.0
        nx, ny, nw, nh = nr
        na = max(1, nw * nh)
        rects = []
        for it in self.glitch_items:
            if it is skip or not it[6]:
                continue
            rects.append((it[3], it[4], it[1], it[2]))
        if add is not None:
            rects.append(add)
        total = 0
        for (x, y, w, h) in rects:
            ix = min(nx + nw, x + w) - max(nx, x)
            iy = min(ny + nh, y + h) - max(ny, y)
            if ix > 0 and iy > 0:
                total += ix * iy
        return total / na

    def pick_pos(self, w, h, skip=None, tries=60):
        best = None
        for _ in range(tries):
            x = self.rng.randint(0, max(0, self.W - w))
            y = self.rng.randint(0, max(0, self.H - h))
            f = self.note_cover(skip=skip, add=(x, y, w, h))
            if f <= self.a.max_cover:
                return x, y
            if best is None or f < best[0]:
                best = (f, x, y)
        return best[1], best[2]

    def pick_note_pos(self, tries=60):
        nw, nh = RANSOM_W, RANSOM_H + TITLE_H
        best = None
        for _ in range(tries):
            x = self.rng.randint(0, max(0, self.W - nw))
            y = self.rng.randint(0, max(0, self.H - nh))
            f = self.note_cover(nr=(x, y, nw, nh))
            if f <= self.a.max_cover:
                return x, y
            if best is None or f < best[0]:
                best = (f, x, y)
        return best[1], best[2]

    # ---------- глитчи ----------
    def show_glitch(self, path):
        if self.state.get("finished"):
            return False
        try:
            scaled, tw, th = self._fit_static(path, self.a.glitch_width)
        except Exception as e:
            print(f"Не смог открыть {path}: {e}", file=sys.stderr, flush=True)
            return False
        img = self.Gtk.Image.new_from_pixbuf(scaled)
        img.set_size_request(tw, th)
        frame, title_lbl, _bar = self._make_fake_window(img, tw, th)
        fh = th + TITLE_H
        x, y = self.pick_pos(tw, fh)
        self.fixed.put(frame, x, y)
        frame.show_all()
        self.raise_vignette()
        self.glitch_items.append([frame, tw, fh, x, y, path, True, title_lbl])
        print(f"  {os.path.basename(path)} [{title_lbl.get_text()}] at {x},{y} {tw}x{fh}",
              flush=True)
        self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
        return False

    def shake_tick(self):
        if self.state.get("finished"):
            return False
        px = max(0, self.a.shake_px)
        if (self.attack is not None and self.stage.get("stage1") and not self.state.get("done")
                and px > 0):
            try:
                self.fixed.move(self.attack.image,
                                self.corners.get("bx", 0) + self.rng.randint(-px, px),
                                self.corners.get("by", 0) + self.rng.randint(-px, px))
            except Exception:
                pass
        rw = self.ransom_state.get("widget")
        if rw is not None and px > 0 and not self.ransom_state.get("drag"):
            try:
                nx = self.ransom_state["bx"] + self.rng.randint(-px, px)
                ny = self.ransom_state["by"] + self.rng.randint(-px, px)
                self.fixed.move(rw, nx, ny)
                self.ransom_state["px"], self.ransom_state["py"] = nx, ny
            except Exception:
                pass
        if self.glitch_items:
            for it in self.glitch_items:
                if not it[6]:
                    continue
                img, tw, th, bx, by = it[:5]
                try:
                    self.fixed.move(img,
                                    bx + self.rng.randint(-px, px),
                                    by + self.rng.randint(-px, px))
                except Exception:
                    pass
        self.pin_click_through()
        return True

    def next_move_ms(self):
        lo = max(0, int(self.a.move_min * 1000))
        hi = max(0, int(self.a.move_max * 1000))
        return self.rng.randint(lo, hi) if hi > lo else hi

    def relocate(self):
        if self.state.get("finished"):
            return False
        if not self.glitch_items:
            return False
        for it in self.glitch_items:
            img, tw, th = it[0], it[1], it[2]
            nx, ny = self.pick_pos(tw, th, skip=it)
            it[3], it[4] = nx, ny
            try:
                self.fixed.move(img, nx, ny)
            except Exception:
                pass
            self._set_title(it[7], self._random_title())
        print("  прыжок: " + ", ".join(
            f"{os.path.basename(it[5])}->{it[3]},{it[4]} [{it[7].get_text()}]"
            for it in self.glitch_items), flush=True)
        if self.ransom_state.get("widget") is not None:
            print(f"  записка: {self.ransom_state['bx']},{self.ransom_state['by']} "
                  f"cover={self.note_cover():.2f}", flush=True)
        rt = self.ransom_state.get("title")
        if self.ransom_state.get("widget") is not None and not self.ransom_state.get("drag"):
            self.ransom_state["bx"], self.ransom_state["by"] = self.pick_note_pos()
            try:
                self.fixed.move(self.ransom_state["widget"],
                                self.ransom_state["bx"], self.ransom_state["by"])
            except Exception:
                pass
        if rt is not None:
            self._set_title(rt, self._random_title())
        self.GLib.timeout_add(self.next_move_ms(), self.relocate)
        return False

    def next_vis_ms(self):
        lo = max(0, int(self.a.vis_min * 1000))
        hi = max(0, int(self.a.vis_max * 1000))
        return self.rng.randint(lo, hi) if hi > lo else hi

    def visible_count(self):
        return sum(1 for it in self.glitch_items if it[6])

    def enforce_cap(self):
        if self.state.get("finished"):
            return False
        vis = [it for it in self.glitch_items if it[6]]
        self.rng.shuffle(vis)
        while sum(1 for it in self.glitch_items if it[6]) > min(self.a.max_visible, len(self.glitch_items)):
            it = vis.pop()
            try:
                it[0].hide()
            except Exception:
                pass
            it[6] = False
            print(f"  скрыт сразу: {os.path.basename(it[5])}", flush=True)
        return False

    def visibility_tick(self):
        if self.state.get("finished"):
            return False
        if not self.glitch_items:
            return False
        vis = [it for it in self.glitch_items if it[6]]
        hid = [it for it in self.glitch_items if not it[6]]
        self.rng.shuffle(vis)
        self.rng.shuffle(hid)
        for it in vis:
            if self.visible_count() <= self.a.min_visible:
                break
            if self.rng.random() < self.a.hide_chance:
                try:
                    it[0].hide()
                except Exception:
                    pass
                it[6] = False
                print(f"  скрылся: {os.path.basename(it[5])} (видно {self.visible_count()})",
                      flush=True)
        for it in hid:
            if self.visible_count() >= min(self.a.max_visible, len(self.glitch_items)):
                break
            if self.rng.random() < self.a.show_chance:
                it[3], it[4] = self.pick_pos(it[1], it[2], skip=it)
                try:
                    self.fixed.move(it[0], it[3], it[4])
                except Exception:
                    pass
                try:
                    it[0].show()
                except Exception:
                    pass
                it[6] = True
                print(f"  появился: {os.path.basename(it[5])} (видно {self.visible_count()})",
                      flush=True)
        self.GLib.timeout_add(self.next_vis_ms(), self.visibility_tick)
        return False

    # ---------- флоатеры ----------
    def floater_pool(self):
        pool = list(self.glitches)
        for p in TAUNT_CANDIDATES:
            if os.path.isfile(p) and p not in pool:
                pool.append(p)
        return pool

    def spawn_floater(self):
        pool = self.floater_pool()
        if not pool:
            return
        path = self.rng.choice(pool)
        tw = self.rng.randint(200, 399)
        th = self.rng.randint(200, 399)
        try:
            pix = self.GdkPixbuf.Pixbuf.new_from_file(path)
            scaled = pix.scale_simple(tw, th, self.GdkPixbuf.InterpType.BILINEAR)
        except Exception:
            return
        img = self.Gtk.Image.new_from_pixbuf(scaled)
        img.set_size_request(tw, th)
        frame, _t, _b = self._make_fake_window(img, tw, th)
        fh = th + TITLE_H
        x, y = self.pick_pos(tw, fh)
        self.fixed.put(frame, x, y)
        frame.show_all()
        self.raise_vignette()
        self.floater_items.append([frame, x, y])
        self.snd.sfx("tauntspawn")
        print(f"  флоатер: {os.path.basename(path)} {tw}x{th} at {x},{y}",
              flush=True)
        self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
        self.GLib.timeout_add(self.rng.randint(4000, 9999), lambda: self.close_floater(frame))

    def close_floater(self, frame):
        for it in self.floater_items:
            if it[0] is frame:
                self.floater_items.remove(it)
                break
        else:
            return False
        try:
            self.fixed.remove(frame)
        except Exception:
            pass
        try:
            frame.hide()
        except Exception:
            pass
        if not self.state.get("finished"):
            self.snd.sfx("tauntleave")
        return False

    def floater_tick(self):
        if self.state.get("finished"):
            return False
        if self.rng.randint(1, 100) <= 2:
            self.spawn_floater()
        for it in self.floater_items:
            try:
                self.fixed.move(it[0],
                                it[1] + self.rng.randint(-5, 4),
                                it[2] + self.rng.randint(-5, 4))
            except Exception:
                pass
        self.GLib.timeout_add(200, self.floater_tick)
        return False

    # ---------- финалы ----------
    def hide_stage2(self):
        try:
            if self.ransom_state["widget"] is not None:
                self.fixed.remove(self.ransom_state["widget"])
        except Exception:
            pass
        try:
            if self.ransom_state["widget"] is not None:
                self.ransom_state["widget"].hide()
        except Exception:
            pass
        self.ransom_state["widget"] = None
        for it in self.glitch_items:
            try:
                self.fixed.remove(it[0])
            except Exception:
                pass
            try:
                it[0].hide()
            except Exception:
                pass
        self.glitch_items.clear()
        for it in list(self.floater_items):
            try:
                self.fixed.remove(it[0])
            except Exception:
                pass
            try:
                it[0].hide()
            except Exception:
                pass
        self.floater_items.clear()
        self.pin_click_through(force=True)

    def finish_all_paid(self, cross=False):
        if self.state.get("finished"):
            return False
        self.state["finished"] = True
        self.hide_stage2()
        print("всё уплачено — глитчи закрыты, thankyou через 1с", flush=True)
        self.snd.stop_all()
        if not cross:
            self.GLib.timeout_add(500, lambda: self.snd.sfx("thankyou"))
        self.GLib.timeout_add(1000, lambda: self.show_thankyou(cross))
        return False

    def finish_unpaid(self):
        if self.state.get("finished"):
            return False
        self.state["finished"] = True
        self.hide_stage2()
        print("время вышло — всё скрыто, loss через 1с, затем выход", flush=True)
        self.snd.stop_all()
        self.GLib.timeout_add(500, lambda: self.snd.sfx("attack"))
        self.GLib.timeout_add(1000, self.show_loss_final)
        return False

    def show_thankyou(self, cross=False):
        if cross:
            self.show_repent_only()
        else:
            self.play_final(find_first(THANKS_CANDIDATES), max(1, self.a.thanks_loops),
                            "thankyou", 560, framed=True)
        self.hide_vignette()
        return False

    def show_repent_only(self):
        rp = self.rep_info.get("path") or find_first(REPENT_CANDIDATES)
        if self.rep_info.get("ready"):
            n_frames, loop_ms = self.rep_info["n"], self.rep_info["ms"]
        else:
            try:
                n_frames, loop_ms = gif_info(rp) if rp else (0, 0)
            except Exception:
                n_frames, loop_ms = 0, 0
        if not rp or loop_ms <= 0:
            self.play_final(find_first(THANKS_CANDIDATES), max(1, self.a.thanks_loops),
                            "thankyou", 560, framed=True)
            return False
        try:
            anim = self.GdkPixbuf.PixbufAnimation.new_from_file(rp)
            nw, nh = int(anim.get_width()), int(anim.get_height())
        except Exception:
            anim, nw, nh = None, 0, 0
        if anim is not None and nw > 0 and nw <= self.W and nh <= self.H:
            img = self.Gtk.Image()
            img.set_from_animation(anim)
            self.fixed.put(img, (self.W - nw) // 2, (self.H - nh) // 2)
            img.show()
        else:
            spr = self._sprite(rp, min(1000, self.W))
            tw, th = spr.render()
            self.fixed.put(spr.image, (self.W - tw) // 2, (self.H - th) // 2)
            spr.image.show()

            def repent_tick():
                if self.state.get("quit"):
                    return False
                if n_frames and spr.frames >= n_frames:
                    return False
                d, _ = spr.step()
                self.GLib.timeout_add(d, repent_tick)
                return False

            repent_tick()
        self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
        print("repent показан (1 проход, ведёт GDK)", flush=True)
        self.snd.sfx("crucifix")

        def repent_done():
            if not self.state.get("quit"):
                self.state["quit"] = True
                print("repent показан — выхожу", flush=True)
                self.Gtk.main_quit()
            return False

        self.GLib.timeout_add(int(loop_ms * max(1, self.a.repent_loops) + 250), repent_done)
        return False

    def show_loss_final(self):
        self.play_final(find_first(LOSS_CANDIDATES), max(1, self.a.loss_loops),
                        "loss-final", self.W)
        return False

    def play_final(self, tg, loops, label, target_w, framed=False):
        if not tg or loops < 1:
            print(f"{label}: нет gif — выхожу", flush=True)
            self.Gtk.main_quit()
            return False
        _, loop_ms = gif_info(tg)
        spr = self._sprite(tg, min(target_w, self.W))
        tw, th = spr.render()
        if framed:
            frame, title_lbl, _ = self._make_fake_window(spr.image, tw, th)
            fh = th + TITLE_H
            self.fixed.put(frame, (self.W - tw) // 2, (self.H - fh) // 2)
            frame.show_all()
            self.raise_vignette()
            print(f"{label} [{title_lbl.get_text()}]", flush=True)
        else:
            self.fixed.put(spr.image, (self.W - tw) // 2, (self.H - th) // 2)
            spr.image.show()
            self.raise_vignette()
        self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))

        def final_tick():
            if self.state.get("quit"):
                return False
            d, _ = spr.step()
            self.GLib.timeout_add(d, final_tick)
            return False

        def final_done():
            if not self.state.get("quit"):
                self.state["quit"] = True
                print(f"{label} показан — выхожу", flush=True)
                self.Gtk.main_quit()
            return False

        final_tick()
        self.GLib.timeout_add(int(loop_ms * loops + 500), final_done)
        return False

    # ---------- оплата / DnD ----------
    def apply_drop_uris(self, uris):
        from .config import COIN_VALUES
        api = self.ransom_state.get("api")
        st = api["st"] if api else None
        if not api or not st or st.get("paid"):
            return False
        ok = False
        paid_cross = False
        for uri in uris or []:
            try:
                path = self.GLib.filename_from_uri(uri)[0]
            except Exception:
                continue
            if not path or not os.path.isfile(path):
                continue
            ext = os.path.splitext(os.path.basename(path))[1]
            try:
                if ext.startswith(".gold"):
                    n = int(ext.replace(".gold", "") or 0)
                    cid = coin_id(path)
                    if cid in self.ransom_state["used"]:
                        print(f"  уже была: {os.path.basename(path)}", flush=True)
                        continue
                    self.ransom_state["used"].add(cid)
                    st["total"] -= COIN_VALUES.get(n, 10)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    ok = True
                    self.snd.sfx("cash")
                elif ext == ".crucifix":
                    cid = coin_id(path)
                    if cid in self.ransom_state["used"]:
                        print(f"  уже был: {os.path.basename(path)}", flush=True)
                        continue
                    self.ransom_state["used"].add(cid)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    st["total"] = 0
                    paid_cross = True
                    ok = True
            except (ValueError, OSError):
                continue
        api["refresh_sum"]()
        print(f"ransom drop: total={max(0, st['total'])}", flush=True)
        if st["total"] <= 0:
            st["paid"] = True
            print("ransom note: %s" %
                  ("Crucifix used — cleared!" if paid_cross else "Ransom paid."),
                  flush=True)
            self.finish_all_paid(paid_cross)
        return ok

    def on_ransom_drag_motion(self, w, ctx, x, y, time):
        self.ransom_state["drag"] = True
        return False

    def on_ransom_drag_leave(self, w, ctx, time):
        self.ransom_state["drag"] = False

    def on_ransom_drop(self, w, ctx, x, y, data, info, time):
        self.ransom_state["drag"] = False
        try:
            uris = data.get_uris() or []
        except Exception:
            uris = []
        ok = self.apply_drop_uris(uris)
        try:
            self.Gtk.drag_finish(ctx, ok, False, time)
        except Exception:
            pass

    def apply_pay_files(self):
        if self.state.get("finished"):
            return False
        uris = []
        for p in self.a.pay_file or []:
            if os.path.isfile(p):
                try:
                    uris.append(self.GLib.filename_to_uri(p))
                except Exception:
                    pass
        print(f"pay-file: применяю {len(uris)} файл(а)", flush=True)
        self.apply_drop_uris(uris)
        return False

    # ---------- монеты на диске ----------
    def spawn_coins_stage(self):
        a = self.a
        if a.no_coins or a.no_ransom:
            return
        rng_c = random.Random(a.coin_seed)
        roots = list(a.coin_roots) if a.coin_roots else None
        if a.coin_drawer:
            drawer = os.path.join(
                "/tmp", "RansomDrawers", f"run-{rng_c.randrange(1 << 30):08x}")
            try:
                os.makedirs(drawer, exist_ok=True)
            except OSError as e:
                print(f"монетки: не создал {drawer}: {e}", flush=True)
                return
            self.coin_state["dirs"].append(drawer)
            roots = [drawer]
        if roots is None:
            try:
                existing, _ = get_user_folders()
            except Exception as e:
                print(f"монетки: не нашёл папки: {e}", flush=True)
                return
            roots = list(existing.values())
        if not roots:
            print("монетки: нет папок — пропуск (создайте ~/Documents или --coin-roots)",
                  flush=True)
            return
        target = a.coin_ransom if a.coin_ransom else a.ransom_sum
        try:
            gen, files, dirs = spawn_deep(
                target, roots, rng_c, max(0, a.coin_depth),
                a.coin_extra, max(0.0, min(1.0, a.coin_chance)),
                a.coin_honeypot, a.coin_cruc, False)
        except Exception as e:
            print(f"монетки: ошибка спавна: {e}", flush=True)
            return
        self.coin_state["files"].extend(files)
        self.coin_state["dirs"].extend(set(dirs))
        try:
            save_track(files, list(set(dirs)))
        except Exception:
            pass
        self.set_coin_icons(files)
        print(f"монетки: ~{gen} в {len(files)} файлах "
              f"({', '.join(roots)})", flush=True)

    def set_coin_icons(self, files):
        from .config import BASE
        a = self.a
        if a.no_coin_icons:
            return
        import shutil
        import subprocess
        from pathlib import Path
        if shutil.which("gio") is None:
            print("иконки: нет gio — пропуск", flush=True)
            return
        ok = err = 0
        for fp in files:
            rel = ICON_BY_EXT.get(os.path.splitext(os.path.basename(fp))[1])
            icon = rel and os.path.join(BASE, "assets", rel)
            if not icon or not os.path.isfile(icon):
                err += 1
                continue
            try:
                r = subprocess.run(
                    ["gio", "set", fp, "metadata::custom-icon", Path(icon).as_uri()],
                    capture_output=True, timeout=15)
                if r.returncode == 0:
                    ok += 1
                else:
                    err += 1
            except Exception:
                err += 1
        print(f"иконки: {ok} ok, {err} мимо", flush=True)

    def cleanup_coins(self):
        a = self.a
        if a.no_coin_cleanup:
            return
        files, dirs = self.coin_state["files"], self.coin_state["dirs"]
        if not files and not dirs:
            return
        nf = sum(1 for p in files if _rm(p))
        nd = sum(1 for d in sorted(set(dirs), key=len, reverse=True)
                 if _rmdir(d))
        print(f"монетки: убрано файлов: {nf}, папок: {nd}", flush=True)

    def play_layer3_once(self):
        if self.state.get("finished"):
            return False
        if self.ransom_state.get("widget") is None:
            return False
        self.l3_started["v"] = True
        self.snd.stop_music()
        self.snd.sfx("layer3")
        return False

    # ---------- этапы ----------
    def scatter(self):
        a = self.a
        print(f"downloading отыграл {a.loops} цикл(а) — скрываю GIF, разбрасываю: "
              + ", ".join(os.path.basename(p) for p in self.order), flush=True)
        self.snd.stop_music()
        for w in (self.dl.image, self.attack.image if self.attack is not None else None,
                  self.sign_img):
            if w is None:
                continue
            try:
                w.hide()
            except Exception:
                pass
            try:
                self.fixed.remove(w)
            except Exception:
                pass
        self.spawn_coins_stage()
        for i, path in enumerate(self.order):
            self.GLib.timeout_add(max(0, a.glitch_delay) * i, self.show_glitch, path)
        if not a.no_ransom:
            root, rapi = build_ransom_note(
                self.Gtk, self.Pango, self.GdkPixbuf,
                self.state, self.l3_started,
                self.snd.music, self.finish_unpaid,
                a.ransom_sum, a.rantime)
            rframe, rtitle, rbar = self._make_fake_window(root, RANSOM_W, RANSOM_H)
            rx, ry = self.pick_note_pos()
            self.fixed.put(rframe, rx, ry)
            rframe.show_all()
            self.raise_vignette()
            self.ransom_state.update(widget=rframe, title=rtitle, bx=rx, by=ry,
                                     px=rx, py=ry, api=rapi, used=set())
            root.drag_dest_set(self.Gtk.DestDefaults.ALL, [], self.Gdk.DragAction.COPY)
            root.drag_dest_add_uri_targets()
            root.connect("drag-data-received", self.on_ransom_drop)
            root.connect("drag-motion", self.on_ransom_drag_motion)
            root.connect("drag-leave", self.on_ransom_drag_leave)
            rbar.drag_dest_set(self.Gtk.DestDefaults.ALL, [], self.Gdk.DragAction.COPY)
            rbar.drag_dest_add_uri_targets()
            rbar.connect("drag-data-received", self.on_ransom_drop)
            rbar.connect("drag-motion", self.on_ransom_drag_motion)
            rbar.connect("drag-leave", self.on_ransom_drag_leave)
            self.GLib.timeout_add(1000, rapi["tick"])
            self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
            self.snd.music("layer1")
            dur3 = max(0, a.rantime)
            if dur3 > 0:
                l3 = self.snd.dur.get("layer3", dur3 / 3)
                t3 = max(0.0, dur3 - l3)
                self.GLib.timeout_add(int(t3 * 1000),
                                      lambda: self.play_layer3_once())
            if not (a.no_floaters or a.no_taunts):
                for _ in range(9):
                    self.spawn_floater()
                self.GLib.timeout_add(200, self.floater_tick)
            if a.pay_file:
                self.GLib.timeout_add(500, self.apply_pay_files)
            print(f"ransom note [{rtitle.get_text()}] at {rx},{ry} "
                  f"sum={a.ransom_sum} time={a.rantime}", flush=True)
        scatter_ms = len(self.order) * max(0, a.glitch_delay)
        if a.vis_max and a.vis_max > 0:
            self.GLib.timeout_add(scatter_ms + 200, self.enforce_cap)
            self.GLib.timeout_add(scatter_ms + 200 + self.next_vis_ms(), self.visibility_tick)
        if a.move_max and a.move_max > 0:
            self.GLib.timeout_add(self.next_move_ms(), self.relocate)
        if a.auto_quit and a.auto_quit > 0:
            total = len(self.order) * max(0, a.glitch_delay) / 1000.0 + a.auto_quit
            self.GLib.timeout_add(int(total * 1000), self.Gtk.main_quit)

    def finish(self):
        if self.state["done"]:
            return False
        self.state["done"] = True
        self.scatter()
        return False

    def dl_tick(self):
        if self.state["done"]:
            return False
        d, _ = self.dl.step()
        if self.dl.frames >= self.dl_n * self.a.loops:
            self.GLib.timeout_add(50, self.finish)
            return False
        self.GLib.timeout_add(d, self.dl_tick)
        return False

    def attack_tick(self):
        if self.state["done"]:
            return False
        d, _ = self.attack.step()
        self.GLib.timeout_add(d, self.attack_tick)
        return False

    def corner_xy(self, i):
        m = 24
        W, H = self.W, self.H
        return [(m, m),
                (W - self.corners["aw"] - m, m),
                (m, H - self.corners["ah"] - m),
                (W - self.corners["aw"] - m, H - self.corners["ah"] - m)][i % 4]

    def jump_tick(self):
        if self.state["done"]:
            return False
        if not self.corners["seq"]:
            self.corners["seq"] = [0, 1, 2, 3]
            self.rng.shuffle(self.corners["seq"])
        i = self.corners["seq"].pop(0)
        x, y = self.corner_xy(i)
        self.corners["bx"], self.corners["by"] = x, y
        try:
            self.fixed.move(self.attack.image, x, y)
        except Exception:
            pass
        print(f"attack: {CORNERS[i]} ({x},{y})", flush=True)
        self.GLib.timeout_add(CORNER_MS, self.jump_tick)
        return False

    def start_stage1(self):
        a = self.a
        if self.stage["stage1"]:
            return False
        self.stage["stage1"] = True
        if self.sign_png:
            try:
                pix = self.GdkPixbuf.Pixbuf.new_from_file(self.sign_png)
                sw = min(int(200 * a.sign_scale), self.W)
                sh = max(1, int(pix.get_height() * sw / max(1, pix.get_width())))
                self.sign_img.set_from_pixbuf(
                    pix.scale_simple(sw, sh, self.GdkPixbuf.InterpType.BILINEAR))
                self.sign_img.set_size_request(sw, sh)
                self.fixed.put(self.sign_img, (self.W - sw) // 2, (self.H - sh) // 2 - 60)
                self.sign_img.show()
            except Exception as e:
                print(f"Не смог показать stop_sign: {e}", file=sys.stderr, flush=True)
        if not a.no_attack:
            aw, ah = self.attack.render()
            self.corners["aw"], self.corners["ah"] = aw, ah
            x, y = self.corner_xy(0)
            self.fixed.put(self.attack.image, x, y)
            self.attack.image.show()
            self.attack_tick()
            self.jump_tick()
        dw, dh = self.dl.render()
        self.fixed.put(self.dl.image, (self.W - dw) // 2, (self.H - dh) // 2 + 120)
        self.dl.image.show()
        self.raise_vignette()
        if not self.attack_chained["v"]:
            self.snd.sfx("attack")
        self.snd.music("install")
        self.dl_tick()
        self.GLib.timeout_add(int(self.dl_loop_ms * a.loops + 800), self.finish)
        self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
        if a.shake_px > 0 and a.shake_ms > 0:
            self.GLib.timeout_add(max(1, a.shake_ms), self.shake_tick)
        print(f"Этап 1: {os.path.basename(self.sign_png) if self.sign_png else '—'} позади + "
              f"{os.path.basename(self.dl_gif)} впереди ({a.loops} цикла)"
              + (", attack прыгает по углам" if not a.no_attack else ""),
              flush=True)
        return False

    def start_stage1_from_loss(self, loss_image=None):
        try:
            self.fixed.remove(loss_image or self._loss_image)
        except Exception:
            pass
        try:
            (loss_image or self._loss_image).hide()
        except Exception:
            pass
        self.start_stage1()
        return False

    def loss_tick(self):
        d, _ = self._loss.step()
        if self._loss.frames >= self._loss_n * max(1, self.a.loss_loops):
            self.GLib.timeout_add(50, self.start_stage1_from_loss)
            return False
        self.GLib.timeout_add(d, self.loss_tick)
        return False

    def on_key(self, win_, event):
        if self.idle_active:
            return False
        if event.keyval in (self.Gdk.KEY_Escape, self.Gdk.KEY_q, self.Gdk.KEY_Q):
            self.Gtk.main_quit()

    def on_button(self, win_, event):
        if self.idle_active:
            return False
        if not self.click_through and event.button == 3:
            self.Gtk.main_quit()

    def _setup_window(self):
        a = self.a
        Gtk, Gdk, GtkLayerShell = self.Gtk, self.Gdk, self.GtkLayerShell
        win = Gtk.Window()
        win.set_title(OVERLAY_TITLE)
        win.set_decorated(False)
        win.set_app_paintable(True)
        win.set_skip_taskbar_hint(True)
        if self.click_through and not a.no_fullscreen:
            try:
                win.set_accept_focus(False)
                win.set_focus_on_map(False)
            except Exception:
                pass

        screen = win.get_screen()
        win.set_visual(screen.get_rgba_visual())
        css = Gtk.CssProvider()
        css.load_from_data(b"window { background-color: transparent; border: none; }")
        Gtk.StyleContext.add_provider_for_screen(
            screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        ransom_css = Gtk.CssProvider()
        ransom_css.load_from_data(b"""
#ransom-root { background-color: #f82b1c; }
#ransom-root-dead { background-color: #640000; }
#ransom-warnbg { background-color: black; border: 2px solid white; }
#ransom-leftbg { background-color: black; border: 2px solid #ffcf25; }
#ransom-timerbg { background-color: red; border: 2px solid white; }
#fake-titlebar { background-color: white; border-width: 0 0 1px 0; border-style: solid; border-color: #808080; }
""")
        Gtk.StyleContext.add_provider_for_screen(
            screen, ransom_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if not a.no_fullscreen:
            GtkLayerShell.init_for_window(win)
            GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
            for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                         GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
                GtkLayerShell.set_anchor(win, edge, True)
            GtkLayerShell.set_exclusive_zone(win, -1)
            GtkLayerShell.set_namespace(win, LAYER_NAMESPACE)
            GtkLayerShell.set_keyboard_mode(
                win, GtkLayerShell.KeyboardMode.NONE if self.click_through
                else GtkLayerShell.KeyboardMode.ON_DEMAND)
            display = Gdk.Display.get_default()
            monitor = pick_monitor(display)
            geo = monitor.get_geometry()
            print(f"Монитор: x={geo.x} y={geo.y} {geo.width}x{geo.height}", flush=True)
            GtkLayerShell.set_monitor(win, monitor)
            W, H = geo.width, geo.height
            win.set_default_size(W, H)
        else:
            W, H = 960, 540
            win.set_default_size(W, H)
        self.W, self.H = W, H
        self.win = win
        self.fixed = Gtk.Fixed()
        win.add(self.fixed)
        win.connect("key-press-event", self.on_key)
        win.connect("button-press-event", self.on_button)

    def run(self):
        import sys as _sys
        a = self.a
        self.snd.init()
        threading.Thread(target=self._repent_scan, daemon=True).start()

        if not self.dl_gif:
            print("Не найден downloading.gif: " + ", ".join(DOWNLOAD_CANDIDATES), file=_sys.stderr)
            return 1
        if not self.at_gif and not a.no_attack:
            print("Не найден ransom_attack.gif: " + ", ".join(ATTACK_CANDIDATES), file=_sys.stderr)
            return 1
        if not self.sign_png:
            print("Внимание: не найден stop_sign.png: " + ", ".join(SIGN_CANDIDATES),
                  file=_sys.stderr, flush=True)
        if self.missing:
            print("Внимание: не найдены: " + ", ".join(self.missing), file=_sys.stderr, flush=True)
        if not self.glitches:
            print("Нет ни одного glitch*.jpg — нечего разбрасывать.", file=_sys.stderr)
            return 1

        if toggle_existing():
            return 0
        write_pidfile()

        Gtk, Gdk, GtkLayerShell, GdkPixbuf, GLib, Pango, cairo = gtkkit.ensure_gtk()
        self.Gtk, self.Gdk, self.GtkLayerShell = Gtk, Gdk, GtkLayerShell
        self.GdkPixbuf, self.GLib, self.Pango, self.cairo = GdkPixbuf, GLib, Pango, cairo

        self._setup_window()

        # --- засада 0: мигающий ransom_idle.png в том же окне; ---
        # --- триггер = основной скрипт дальше, таймаут = выход ---
        if not a.no_idle:
            from .idle import run_idle_ambush
            try:
                triggered = run_idle_ambush(self)
            except Exception as e:
                print(f"idle-засада упала ({e}) — сразу основной скрипт", flush=True)
                triggered = True
            if not triggered:
                remove_pidfile()
                return 0
            print("idle: триггер — запускаю основной скрипт", flush=True)

        self._setup_vignette()

        if not a.no_attack:
            self.attack = self._sprite(self.at_gif, int(200 * a.attack_scale))

        self.dl_n, self.dl_loop_ms = gif_info(self.dl_gif)
        self.dl = self._sprite(self.dl_gif, int(700 * a.download_scale))
        self.sign_img = Gtk.Image()

        self.order = list(self.glitches)
        self.rng.shuffle(self.order)

        # --- этап 0: loss_no_vignette.gif на весь экран, затем этап 1 ---
        self.loss_gif = find_first(LOSS_CANDIDATES)
        if a.no_loss or not self.loss_gif or a.loss_loops < 1:
            if not self.loss_gif and not a.no_loss:
                print("loss_no_vignette.gif не найден — сразу этап 1", flush=True)
            self.start_stage1()
        else:
            self._loss_n, self._loss_loop_ms = gif_info(self.loss_gif)
            self._loss = self._sprite(self.loss_gif, self.W)
            lw, lh = self._loss.render()
            self._loss_image = self._loss.image
            self.fixed.put(self._loss.image, (self.W - lw) // 2, (self.H - lh) // 2)
            self._loss.image.show()
            self.raise_vignette()
            self.snd.sfx("spawn")
            self.attack_chained["v"] = True
            self.GLib.timeout_add(int(self.snd.dur.get("spawn", 1.2) * 1000),
                                  lambda: self.snd.sfx("attack") if not self.state.get("quit") else False)
            self.loss_tick()
            self.GLib.timeout_add(int(self._loss_loop_ms * max(1, a.loss_loops) + 800),
                                  self.start_stage1_from_loss)
            self.GLib.timeout_add(60, lambda: self.pin_click_through(force=True))
            print(f"Этап 0: {os.path.basename(self.loss_gif)} на весь экран "
                  f"({max(1, a.loss_loops)} цикла), затем этап 1", flush=True)

        self.win.show_all()

        if self.click_through and not a.no_fullscreen:
            self.pin_click_through(force=True)
            print("Click-through включён. Закрыть: повторный запуск или pkill -f show_downloading_attack.",
                  flush=True)
        else:
            print("Esc / правый клик закроют оверлей.", flush=True)

        import signal as _signal

        def _on_term(signum, frame):
            remove_pidfile()
            _sys.exit(0)

        _signal.signal(_signal.SIGTERM, _on_term)
        _signal.signal(_signal.SIGINT, _on_term)

        self.wall.swap()
        try:
            Gtk.main()
        finally:
            self.snd.stop_all()
            self.cleanup_coins()
            self.wall.restore()
            remove_pidfile()
        return 0
