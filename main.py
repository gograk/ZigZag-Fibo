#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIGZAG_FIBO — Android APK UI (Kivy)
Semua logika sinyal ada di bot_core.py (tidak diubah).
"""

import threading
from datetime import datetime

# ── Kivy config SEBELUM import kivy lainnya ─────────────
from kivy.config import Config
Config.set('graphics','width','400')
Config.set('graphics','height','800')
Config.set('kivy','window_icon','')

from kivy.app         import App
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.scrollview    import ScrollView
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.gridlayout    import GridLayout
from kivy.uix.tabbedpanel   import TabbedPanel, TabbedPanelItem
from kivy.clock             import Clock
from kivy.utils             import platform
from kivy.core.window       import Window
from kivy.graphics          import Color, Rectangle, RoundedRectangle

Window.clearcolor = (0.05, 0.05, 0.08, 1)   # latar gelap

# ── import bot core ────────────────────────────────────
import bot_core as bot

# ════════════════════════════════════════════════════════
#  ANDROID NOTIFICATION (via plyer)
# ════════════════════════════════════════════════════════
def _send_android_notif(title, body):
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=body,
            app_name="ZIGZAG_FIBO",
            timeout=5,
        )
    except Exception:
        pass   # desktop / plyer tidak tersedia → skip

bot.notify_callback = _send_android_notif

# ════════════════════════════════════════════════════════
#  HELPER WIDGET
# ════════════════════════════════════════════════════════
def lbl(text, size=14, bold=False, color=(1,1,1,1), halign='left', **kw):
    l = Label(
        text=text, font_size=size, bold=bold,
        color=color, halign=halign,
        size_hint_y=None, markup=True, **kw
    )
    l.bind(texture_size=l.setter('size'))
    return l

def section_label(text):
    return lbl(f"[b]{text}[/b]", size=13, color=(0.6,0.8,1,1), halign='left')

def card_box(orientation='vertical', padding=8, spacing=4, **kw):
    box = BoxLayout(orientation=orientation, padding=padding,
                    spacing=spacing, size_hint_y=None, **kw)
    box.bind(minimum_height=box.setter('height'))
    with box.canvas.before:
        Color(0.1, 0.12, 0.17, 1)
        box._rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[8])
    box.bind(pos=lambda w,v: setattr(w._rect,'pos',v),
             size=lambda w,v: setattr(w._rect,'size',v))
    return box

# ════════════════════════════════════════════════════════
#  TAB: DASHBOARD
# ════════════════════════════════════════════════════════
class DashTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=10, spacing=8, **kw)

        # ── Price card ──────────────────────────────────
        self.price_lbl   = lbl("XAUUSD  —", size=26, bold=True,
                               color=(1,0.85,0.2,1), halign='center')
        self.change_lbl  = lbl("", size=14, halign='center')
        self.spark_lbl   = lbl("", size=12, color=(0.5,0.9,1,1), halign='center')
        self.ws_lbl      = lbl("WS: ⏳ menghubungkan...", size=12,
                               color=(0.6,0.6,0.6,1), halign='center')

        price_card = card_box(spacing=2)
        price_card.add_widget(self.ws_lbl)
        price_card.add_widget(self.price_lbl)
        price_card.add_widget(self.change_lbl)
        price_card.add_widget(self.spark_lbl)
        self.add_widget(price_card)

        # ── RSI card ────────────────────────────────────
        self.add_widget(section_label("  RSI-14 per Timeframe"))
        self.rsi_grid = GridLayout(cols=5, size_hint_y=None, height=60, spacing=4)
        self.rsi_cells = {}
        for tf in bot.TIMEFRAMES:
            box = BoxLayout(orientation='vertical', spacing=2)
            name_l = lbl(bot.TF_LABEL[tf], size=11, halign='center', bold=True)
            val_l  = lbl("—", size=12, halign='center')
            box.add_widget(name_l)
            box.add_widget(val_l)
            self.rsi_cells[tf] = val_l
            self.rsi_grid.add_widget(box)
        self.add_widget(self.rsi_grid)

        # ── Stats card ──────────────────────────────────
        self.add_widget(section_label("  Statistik Sesi"))
        stats_card = card_box()
        self.stat_signals = lbl("Total Sinyal : 0", size=13)
        self.stat_wins    = lbl("Win (TP1)    : 0", size=13)
        self.stat_dpnl    = lbl("PnL Harian   : 0.00", size=13)
        self.stat_dd      = lbl("Max Drawdown : 0.00", size=13)
        self.stat_uptime  = lbl("Uptime       : 00:00:00", size=13)
        for w in [self.stat_signals, self.stat_wins,
                  self.stat_dpnl, self.stat_dd, self.stat_uptime]:
            stats_card.add_widget(w)
        self.add_widget(stats_card)

        # ── Log card ─────────────────────────────────────
        self.add_widget(section_label("  Log"))
        log_card = card_box()
        self.log_lbl = lbl("", size=11, color=(0.6,0.7,0.7,1))
        log_card.add_widget(self.log_lbl)
        self.add_widget(log_card)

    def refresh(self, *_):
        with bot.S.lock:
            price   = bot.S.price
            prev    = bot.S.prev_price
            hist    = list(bot.S.price_hist)
            rsi_d   = dict(bot.S.rsi)
            ws_ok   = bot.S.ws_connected
            total   = bot.S.total_signals
            wins    = bot.S.wins
            dpnl    = bot.S.daily_pnl
            dd      = bot.S.max_dd
            start   = bot.S.start_time
        from datetime import timezone
        uptime = str(datetime.now(timezone.utc)-start).split('.')[0]

        # price
        chg  = price - prev if prev else 0
        sign = "▲" if chg >= 0 else "▼"
        col  = "00ff88" if chg >= 0 else "ff4444"
        self.price_lbl.text  = f"[color=ffd700]XAUUSD  {price:,.3f}[/color]"
        self.change_lbl.text = f"[color=#{col}]{sign} {chg:+.3f}[/color]"
        self.spark_lbl.text  = bot.make_sparkline(hist)
        self.ws_lbl.text     = (
            "[color=00ff88]● WS LIVE[/color]" if ws_ok
            else "[color=ff4444]● WS OFFLINE[/color]"
        )

        # RSI
        for tf in bot.TIMEFRAMES:
            val = rsi_d.get(tf, 0.0)
            if   val >= 70: c = "ff4444"
            elif val <= 30: c = "44ddff"
            else:           c = "88ff88"
            tag = " OB" if val>=70 else (" OS" if val<=30 else "")
            self.rsi_cells[tf].text = f"[color=#{c}]{val:.0f}{tag}[/color]"

        # stats
        wr = f"{round(wins/total*100)}%" if total else "—"
        pnl_col = "00ff88" if dpnl >= 0 else "ff4444"
        self.stat_signals.text = f"Total Sinyal : {total}"
        self.stat_wins.text    = f"Win (TP1)    : {wins}  ({wr})"
        self.stat_dpnl.text    = f"[color=#{pnl_col}]PnL Harian   : {dpnl:+.2f}[/color]"
        self.stat_dd.text      = f"Max Drawdown : {dd:.2f}"
        self.stat_uptime.text  = f"Uptime       : {uptime}"

        # log
        self.log_lbl.text = "\n".join(list(bot._log_buf)[-5:])


# ════════════════════════════════════════════════════════
#  TAB: SINYAL
# ════════════════════════════════════════════════════════
class SignalTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=10, spacing=6, **kw)
        self.add_widget(section_label("  Sinyal Hari Ini"))
        sv = ScrollView(size_hint=(1,1))
        self.sig_box = BoxLayout(orientation='vertical', spacing=6,
                                 size_hint_y=None)
        self.sig_box.bind(minimum_height=self.sig_box.setter('height'))
        sv.add_widget(self.sig_box)
        self.add_widget(sv)

    def refresh(self, *_):
        with bot.S.lock:
            sigs = list(bot.S.signals_today)
        self.sig_box.clear_widgets()
        if not sigs:
            self.sig_box.add_widget(
                lbl("[color=888888]Belum ada sinyal hari ini.[/color]",
                    size=13, halign='center'))
            return
        for s in reversed(sigs[-20:]):
            is_buy = s["type"]=="buy"
            icon   = "🟢" if is_buy else "🔴"
            col    = "00ff88" if is_buy else "ff4444"
            card   = card_box(padding=8, spacing=3)
            card.add_widget(lbl(
                f"[b][color=#{col}]{icon}  {s['tf']}  {s['type'].upper()}  {s['area']}[/color][/b]",
                size=14))
            card.add_widget(lbl(
                f"Entry: [b]{s['entry']:.3f}[/b]   "
                f"SL: [color=ff6666]{s['sl']:.3f}[/color]   "
                f"TP1: [color=66ff99]{s['tp1']:.3f}[/color]",
                size=13))
            card.add_widget(lbl(f"[color=888888]{s['ts']}[/color]", size=11))
            self.sig_box.add_widget(card)


# ════════════════════════════════════════════════════════
#  TAB: LEVEL FIBO
# ════════════════════════════════════════════════════════
class FiboTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=10, spacing=6, **kw)
        sv = ScrollView(size_hint=(1,1))
        self.fibo_box = BoxLayout(orientation='vertical', spacing=8,
                                  size_hint_y=None)
        self.fibo_box.bind(minimum_height=self.fibo_box.setter('height'))
        sv.add_widget(self.fibo_box)
        self.add_widget(sv)

    def refresh(self, *_):
        with bot.S.lock:
            snap  = {tf:dict(d) for tf,d in bot.S.fibo.items() if d}
            price = bot.S.price
        self.fibo_box.clear_widgets()
        for tf in bot.TIMEFRAMES:
            d = snap.get(tf)
            if not d:
                continue
            lv = d["levels"]
            lb = bot.TF_LABEL[tf]
            card = card_box(spacing=2)
            card.add_widget(lbl(
                f"[b][color=ffd700]── {lb} ──[/color][/b]   "
                f"H:[color=ff8888]{d['high']:.3f}[/color]   "
                f"L:[color=88ff88]{d['low']:.3f}[/color]",
                size=13))
            rows = [
                (2.414, "🛑 SL Sell2", "ff4444"),
                (2.236, "🔴 Sell2 A", "ff6666"),
                (2.000, "🔴 Sell2 B", "ff6666"),
                (1.786, "🛑 SL Sell1", "ff4444"),
                (1.618, "🔴 Sell1 A", "ff8888"),
                (1.500, "🔴 Sell1 B", "ff8888"),
                (1.000, "🏁 HIGH",    "ffd700"),
                (0.500, "🎯 MID",     "ffd700"),
                (0.000, "🏁 LOW",     "ffd700"),
                (-0.500,"🟢 Buy1 A",  "88ff88"),
                (-0.618,"🟢 Buy1 B",  "88ff88"),
                (-0.786,"🛑 SL Buy1", "44ff44"),
                (-1.000,"🟢 Buy2 A",  "44ff88"),
                (-1.236,"🟢 Buy2 B",  "44ff88"),
                (-1.414,"🛑 SL Buy2", "44ff44"),
            ]
            for lvl, name, col in rows:
                val  = lv.get(lvl, 0)
                near = abs(price - val) < 2.0 and price > 0
                marker = "  ◀ HARGA" if near else ""
                card.add_widget(lbl(
                    f"  [color=#{col}]{name}[/color]   "
                    f"[b]{val:.3f}[/b][color=ffff00]{marker}[/color]",
                    size=12))
            self.fibo_box.add_widget(card)


# ════════════════════════════════════════════════════════
#  ROOT UI
# ════════════════════════════════════════════════════════
class RootWidget(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)

        # header
        header = BoxLayout(size_hint_y=None, height=48, padding=[10,4])
        with header.canvas.before:
            Color(0.07,0.09,0.14,1)
            header._rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda w,v: setattr(w._rect,'pos',v),
                    size=lambda w,v: setattr(w._rect,'size',v))
        header.add_widget(lbl(
            "[b][color=ffd700]◆ ZIGZAG_FIBO[/color]  "
            "[color=aaaaaa]XAUUSD · ZigZag+Fibo[/color][/b]",
            size=15, halign='left'))
        self.add_widget(header)

        # tabs
        tp = TabbedPanel(do_default_tab=False, tab_width=110,
                         tab_height=36, size_hint=(1,1))
        tp.background_color = (0.07,0.09,0.14,1)

        self.dash_tab   = DashTab()
        self.signal_tab = SignalTab()
        self.fibo_tab   = FiboTab()

        for title, content in [
            ("Dashboard", self.dash_tab),
            ("Sinyal",    self.signal_tab),
            ("Fibo",      self.fibo_tab),
        ]:
            ti = TabbedPanelItem(text=title)
            sv = ScrollView()
            sv.add_widget(content)
            ti.content = sv
            tp.add_widget(ti)

        self.add_widget(tp)

        # set default tab
        Clock.schedule_once(lambda dt: setattr(tp,'default_tab', tp.tab_list[-1]), 0)

        # refresh callback dari bot_core
        bot.ui_update_callback = self._schedule_refresh

        # refresh timer setiap 1 detik
        Clock.schedule_interval(self._refresh_all, 1)

    def _schedule_refresh(self):
        Clock.schedule_once(self._refresh_all, 0)

    def _refresh_all(self, *_):
        self.dash_tab.refresh()
        self.signal_tab.refresh()
        self.fibo_tab.refresh()


# ════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════
class ZigzagFiboApp(App):
    def build(self):
        self.title = "ZIGZAG_FIBO Bot"
        root = RootWidget()
        # jalankan bot di thread background
        threading.Thread(target=bot.start_bot, daemon=True, name="bot_start").start()
        return root


if __name__ == "__main__":
    ZigzagFiboApp().run()
