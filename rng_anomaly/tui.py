import time
import curses
import sys


class LiveUI:
    def __init__(self, enabled: bool, refresh_sec: float, pct_decimals: int = 6, scale: int = 1, gap: int = 2):
        self.enabled = enabled
        self.refresh_sec = refresh_sec
        self.screen = None
        self.last_draw = 0.0
        self.last_ones_pct = None
        self.last_zeros_pct = None
        self.color_enabled = False
        self.color_pair_one = 0
        self.color_pair_zero = 0
        self.scale = max(1, int(scale))
        self.gap = max(1, int(gap))
        try:
            self.pct_decimals = max(0, int(pct_decimals))
        except Exception:
            self.pct_decimals = 6

    def start(self):
        if not self.enabled:
            return
        try:
            self.screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            try:
                curses.curs_set(0)
            except Exception:
                pass
            self.screen.nodelay(True)
            self.screen.clear()
            try:
                if curses.has_colors():
                    curses.start_color()
                    try:
                        curses.use_default_colors()
                    except Exception:
                        pass
                    curses.init_pair(1, curses.COLOR_GREEN, -1)
                    curses.init_pair(2, curses.COLOR_CYAN, -1)
                    self.color_pair_one = 1
                    self.color_pair_zero = 2
                    self.color_enabled = True
            except Exception:
                self.color_enabled = False
        except Exception:
            self.enabled = False

    def stop(self):
        if not self.enabled:
            return
        try:
            curses.nocbreak()
            try:
                curses.curs_set(1)
            except Exception:
                pass
            curses.echo()
            curses.endwin()
        except Exception:
            pass

    def update(self, ones_pct: float | None, zeros_pct: float | None):
        if not self.enabled:
            return
        now = time.perf_counter()
        if (now - self.last_draw) < self.refresh_sec:
            return
        self.last_draw = now
        self.last_ones_pct = ones_pct
        self.last_zeros_pct = zeros_pct
        try:
            self.screen.erase()
            maxy, maxx = self.screen.getmaxyx()
            base_one = [
                "  11  ",
                " 111  ",
                "  11  ",
                "  11  ",
                "  11  ",
                "  11  ",
                " 11111",
            ]
            base_zero = [
                " 0000 ",
                "00  00",
                "00  00",
                "00  00",
                "00  00",
                "00  00",
                " 0000 ",
            ]

            def scale_art(art: list[str], k: int) -> list[str]:
                if k <= 1:
                    return art
                scaled = []
                for row in art:
                    row_scaled = "".join(ch * k for ch in row)
                    for _ in range(k):
                        scaled.append(row_scaled)
                return scaled

            one_art = scale_art(base_one, self.scale)
            zero_art = scale_art(base_zero, self.scale)
            art_height = len(one_art)
            art_width = len(one_art[0]) + self.gap + len(zero_art[0])
            start_y = max((maxy - art_height) // 2 - 1, 0)
            start_x = max((maxx - art_width) // 2, 0)
            for i, row in enumerate(one_art):
                if self.color_enabled:
                    self.screen.addstr(start_y + i, start_x, row, curses.color_pair(self.color_pair_one) | curses.A_BOLD)
                else:
                    self.screen.addstr(start_y + i, start_x, row)
            sep_x = start_x + len(one_art[0]) + self.gap
            for i, row in enumerate(zero_art):
                if self.color_enabled:
                    self.screen.addstr(start_y + i, sep_x, row, curses.color_pair(self.color_pair_zero) | curses.A_BOLD)
                else:
                    self.screen.addstr(start_y + i, sep_x, row)
            pct_y = start_y + art_height + 1
            fmt = f"{{:.{self.pct_decimals}f}}%"
            ones_txt = f"1s: {fmt.format(ones_pct*100)}" if ones_pct is not None else "1s: n/a"
            zeros_txt = f"0s: {fmt.format(zeros_pct*100)}" if zeros_pct is not None else "0s: n/a"
            spacer = " " * max(4, self.gap * 2)
            line_x = max((maxx - (len(ones_txt) + len(spacer) + len(zeros_txt))) // 2, 0)
            if self.color_enabled:
                self.screen.addstr(pct_y, line_x, ones_txt, curses.color_pair(self.color_pair_one) | curses.A_BOLD)
                self.screen.addstr(pct_y, line_x + len(ones_txt) + len(spacer) - len(spacer), spacer)
                self.screen.addstr(pct_y, line_x + len(ones_txt) + len(spacer), zeros_txt, curses.color_pair(self.color_pair_zero) | curses.A_BOLD)
            else:
                self.screen.addstr(pct_y, line_x, ones_txt + spacer + zeros_txt)
            self.screen.refresh()
        except Exception:
            pass


def build_pretty_lines(bits_total: int, ones_ratio: float | None, pretty_scale: int = 1, pretty_gap: int = 3, pct_decimals: int = 6):
    if ones_ratio is None or bits_total is None:
        ones_ratio = None
    zeros_ratio = (1 - ones_ratio) if ones_ratio is not None else None
    RESET = "\x1b[0m"
    GREEN = "\x1b[32m"
    CYAN = "\x1b[36m"
    BOLD = "\x1b[1m"

    base_one = [
        "  11  ",
        " 111  ",
        "  11  ",
        "  11  ",
        "  11  ",
        "  11  ",
        " 11111",
    ]
    base_zero = [
        " 0000 ",
        "00  00",
        "00  00",
        "00  00",
        "00  00",
        "00  00",
        " 0000 ",
    ]

    def scale_art(art, k):
        if k <= 1:
            return art
        scaled = []
        for row in art:
            row_scaled = "".join(ch * k for ch in row)
            for _ in range(k):
                scaled.append(row_scaled)
        return scaled

    k = max(1, int(pretty_scale))
    gap = max(1, int(pretty_gap))
    one_art = scale_art(base_one, k)
    zero_art = scale_art(base_zero, k)
    spacer = " " * gap
    art_plain_width = len(one_art[0]) + len(spacer) + len(zero_art[0])
    d = max(0, int(pct_decimals))
    fmt = f"{{:.{d}f}}%"
    ones_txt_plain = f"1s: {fmt.format(ones_ratio*100)}" if ones_ratio is not None else "1s:   n/a  "
    zeros_txt_plain = f"0s: {fmt.format(zeros_ratio*100)}" if zeros_ratio is not None else "0s:   n/a  "
    mid_plain = ones_txt_plain + spacer + zeros_txt_plain
    bits_txt_plain = f"bits={bits_total:,}" if bits_total is not None else "bits=n/a"
    content_width = max(art_plain_width, len(mid_plain), len(bits_txt_plain))

    top = "┌" + ("─" * content_width) + "┐"
    bottom = "└" + ("─" * content_width) + "┘"
    lines = [top]
    left_pad = (content_width - art_plain_width) // 2
    right_pad = content_width - art_plain_width - left_pad
    for i in range(len(one_art)):
        left_colored = f"{GREEN}{BOLD}{one_art[i]}{RESET}"
        right_colored = f"{CYAN}{BOLD}{zero_art[i]}{RESET}"
        lines.append("│" + (" " * left_pad) + left_colored + spacer + right_colored + (" " * right_pad) + "│")
    left_pad_pct = (content_width - len(mid_plain)) // 2
    right_pad_pct = content_width - len(mid_plain) - left_pad_pct
    ones_col = f"{GREEN}{BOLD}{ones_txt_plain}{RESET}"
    zeros_col = f"{CYAN}{BOLD}{zeros_txt_plain}{RESET}"
    pct_line = (" " * left_pad_pct) + ones_col + spacer + zeros_col + (" " * right_pad_pct)
    lines.append("│" + pct_line + "│")
    extra_left = (content_width - len(bits_txt_plain)) // 2
    extra_right = content_width - len(bits_txt_plain) - extra_left
    bits_line = (" " * extra_left) + bits_txt_plain + (" " * extra_right)
    lines.append("│" + bits_line + "│")
    lines.append(bottom)
    return lines


def stdout_live_update(pretty: bool, bits_total: int, ones_ratio: float | None, pretty_state: dict, pretty_scale: int, pretty_gap: int, pct_decimals: int):
    try:
        if pretty:
            lines = build_pretty_lines(bits_total, ones_ratio, pretty_scale, pretty_gap, pct_decimals)
            if pretty_state["printed"]:
                sys.stdout.write(f"\x1b[{pretty_state['lines']}A")
            for ln in lines:
                sys.stdout.write("\x1b[2K" + ln + "\n")
            pretty_state["printed"] = True
            pretty_state["lines"] = len(lines)
            sys.stdout.flush()
        else:
            if ones_ratio is None:
                return
            line = f"bits={bits_total:,}  1s={ones_ratio*100:.3f}%  0s={(1-ones_ratio)*100:.3f}%"
            sys.stdout.write("\r" + line)
            sys.stdout.flush()
    except Exception:
        pass


