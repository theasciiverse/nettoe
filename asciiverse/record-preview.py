"""Records netToe's catalog preview (hub/RECORDING.md): 100x30, about 45 s.

Runs the game under `asciinema rec` in a 100x30 pseudo-terminal, reads the
screen through pyte and plays tic-tac-toe against the computer on its
middle level: mostly the best move (a small minimax), now and then a
careless one, so both sides get to win. Network play needs two machines
and is not shown. Usage, from the repo root after asciiverse/build.sh (the
binary in out/), with pyte installed:

    python3 asciiverse/record-preview.py

The game runs by name from out/ on PATH, so the cast's header holds no local
path. The cast goes to asciiverse/nettoe.cast.
"""
import fcntl, os, pty, random, re, select, shutil, struct, sys, tempfile, termios, time

import pyte

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS, ROWS = 100, 30
LENGTH = 44.0                    # seconds of play before quitting
NAME = "Ada"

random.seed(11)

# ncurses repeats a character with REP (CSI n b) and scrolls part of the
# screen with SU and SD (CSI n S, CSI n T), which pyte does not know
_draw = pyte.Screen.draw


def _draw_remembering(self, data):
    if data:
        self.last_char = data[-1]
    _draw(self, data)


def _repeat_last(self, n=1, *rest, **kw):
    if getattr(self, "last_char", None):
        _draw(self, self.last_char * max(1, n))


def _scroll_up(self, n=1, *rest, **kw):
    """SU (CSI n S), which ncurses uses inside a scroll region."""
    top, bottom = self.margins or pyte.screens.Margins(0, self.lines - 1)
    for _ in range(max(1, n)):
        for y in range(top, bottom):
            self.buffer[y] = self.buffer[y + 1]
        self.buffer.pop(bottom, None)
    self.dirty.update(range(self.lines))


def _scroll_down(self, n=1, *rest, **kw):
    """SD (CSI n T)."""
    top, bottom = self.margins or pyte.screens.Margins(0, self.lines - 1)
    for _ in range(max(1, n)):
        for y in range(bottom, top, -1):
            self.buffer[y] = self.buffer[y - 1]
        self.buffer.pop(top, None)
    self.dirty.update(range(self.lines))


pyte.Screen.draw = _draw_remembering
pyte.Screen.repeat_last = _repeat_last
pyte.Screen.scroll_up = _scroll_up
pyte.Screen.scroll_down = _scroll_down
pyte.Stream.csi = dict(pyte.Stream.csi, b="repeat_last", S="scroll_up", T="scroll_down")


class Rec:
    def __init__(self):
        self.home = tempfile.mkdtemp(prefix="nettoe-rec-")
        env = {
            "PATH": f"{os.path.join(ROOT, 'out')}:{os.environ['PATH']}",
            "HOME": self.home,
            "XDG_DATA_HOME": os.path.join(self.home, "data"),
            "USER": "player",
            "LOGNAME": "player",
            "TERM": "xterm-256color",
            "COLORTERM": "truecolor",
            "LANG": "C.UTF-8",
        }
        self.cast = os.path.join(ROOT, "asciiverse", "nettoe.cast")
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(self.home)
            os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
                "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
                "--title", "netToe", "--command", "nettoe", self.cast], env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        self.start = time.time()

    def pump(self, t):
        end = time.time() + t
        while True:
            left = end - time.time()
            r, _, _ = select.select([self.fd], [], [], max(0.0, min(0.01, left)))
            if r:
                try:
                    self.stream.feed(os.read(self.fd, 65536))
                except OSError:
                    return False
            if left <= 0:
                return True

    def key(self, k, wait=0.0):
        os.write(self.fd, k.encode() if isinstance(k, str) else k)
        self.pump(wait)

    def type(self, text, gap=0.12):
        for ch in text:
            self.key(ch, gap)

    def text(self):
        return "\n".join(self.screen.display)

    def finish(self):
        end = time.time() + 5
        while time.time() < end:
            if not self.pump(0.1):
                break
            done, _ = os.waitpid(self.pid, os.WNOHANG)
            if done:
                break
        else:
            os.kill(self.pid, 9)    # SIGKILL: nothing more is written to the cast
        try:
            os.waitpid(self.pid, 0)
        except ChildProcessError:
            pass
        shutil.rmtree(self.home, ignore_errors=True)
        print(f"{self.cast}: {os.path.getsize(self.cast) // 1024} KB, {time.time() - self.start:.0f} s",
              file=sys.stderr)



WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def board(rec):
    """The nine cells, a1 to c3, read from the "Current game" grid."""
    cells = []
    # the game centres its screens (src/centre.h): the board starts where
    # the banner's left corner does
    m = next((l.index("+-") for l in rec.screen.display if "+-" in l), 0)
    for line in rec.screen.display:
        for row in "abc":
            if f"{row}1 | {row}2 | {row}3" in line:
                left = line[m:m + 27].split("|")
                cells += [c.strip() or " " for c in left[:3]]
    return cells if len(cells) == 9 else None


def winner(b):
    for i, j, k in WINS:
        if b[i] != " " and b[i] == b[j] == b[k]:
            return b[i]
    return None


def score(b, me, turn):
    w = winner(b)
    if w:
        return 1 if w == me else -1
    free = [i for i in range(9) if b[i] == " "]
    if not free:
        return 0
    other = "O" if turn == "X" else "X"
    results = []
    for i in free:
        b[i] = turn
        results.append(score(b, me, other))
        b[i] = " "
    return max(results) if turn == me else min(results)


def pick(b, me):
    free = [i for i in range(9) if b[i] == " "]
    if random.random() < 0.12:
        return random.choice(free)               # a careless move
    other = "O" if me == "X" else "X"
    best = []
    for i in free:
        b[i] = me
        s = score(b, me, other)
        b[i] = " "
        best.append((s, i))
    top = max(s for s, _ in best)
    return random.choice([i for s, i in best if s == top])


def main():
    rec = Rec()
    rec.pump(2.5)                                # the main menu
    rec.key("1", 0.3)
    rec.key("\r", 1.2)                          # Player vs CPU
    rec.key("2", 0.3)
    rec.key("\r", 1.0)                          # Normal
    rec.type(NAME)
    rec.key("\r", 0.5)
    end = rec.start + LENGTH
    while True:
        rec.pump(0.2)
        t = rec.text()
        last = [l for l in rec.screen.display if l.strip()][-1] if t.strip() else ""
        if "it is your turn" in last:
            b = board(rec)
            if not b:
                continue
            me = "X" if "playing X" in last else "O"
            rec.pump(0.6)
            i = pick(b, me)
            rec.type("abc"[i // 3] + str(i % 3 + 1), 0.15)
            rec.key("\r", 0.4)
        elif "play again" in last:
            rec.pump(1.8)                        # the result and the score
            if time.time() > end:
                rec.key("n", 0.3)
                rec.key("\r", 1.5)
                break
            rec.key("y", 0.3)
            rec.key("\r", 0.5)
    rec.pump(1.0)
    rec.key("q", 0.3)                            # quit from the main menu
    rec.key("\r", 0.5)
    rec.finish()


if __name__ == "__main__":
    main()
