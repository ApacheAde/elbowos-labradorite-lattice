#!/usr/bin/env python3
"""Labradorite Lattice — neon pipe-flow arcade for ElbowOS. Python 3 + pygame.

Rotate conduit tiles so molten gold can cross the lattice.
Arrows move the cursor, Space / click rotates, R restarts.
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/LABRADORITE_LATTICE_ElbowOS.mp4")
COLS, ROWS, CELL = 5, 8, 156
OX = (W - COLS * CELL) // 2
OY = 340
N, E, S, WDIR = 0, 1, 2, 3
DELTA = [(-1, 0), (0, 1), (1, 0), (0, -1)]
TEAL, COPPER, VIOLET = (46, 230, 199), (255, 138, 76), (186, 120, 255)
GOLD, INK, CREAM = (255, 214, 72), (8, 10, 28), (244, 236, 220)
FLASH = (TEAL, COPPER, VIOLET)


def openings(kind, rot):
    if kind == "I":
        return {E, WDIR} if rot % 2 == 0 else {N, S}
    arms = {N, E}
    return {(a + rot) % 4 for a in arms}


def kind_for(opens):
    return "I" if opens in ({N, S}, {E, WDIR}) else "L"


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Labradorite Lattice")
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.rng = random.Random(11)
        self.reset()
        self.flakes = [(self.rng.randrange(W), self.rng.randrange(H), self.rng.random()) for _ in range(70)]

    def reset(self):
        self.score = getattr(self, "score", 0)
        self.path = self._path()
        self.need = {}
        for i, (r, c) in enumerate(self.path):
            opens = set()
            if i == 0:
                opens.add(N)
            else:
                pr, pc = self.path[i - 1]
                opens.add((DELTA.index((r - pr, c - pc)) + 2) % 4)
            if i == len(self.path) - 1:
                opens.add(S)
            else:
                nr, nc = self.path[i + 1]
                opens.add(DELTA.index((nr - r, nc - c)))
            self.need[(r, c)] = opens
        self.tiles = {}
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) in self.need:
                    kind = kind_for(self.need[(r, c)])
                    good = self._rot_for(kind, self.need[(r, c)])
                    self.tiles[(r, c)] = [kind, (good + 1 + (r + c) % 2) % (2 if kind == "I" else 4), good]
                else:
                    kind = "L" if (r + c) % 3 else "I"
                    self.tiles[(r, c)] = [kind, self.rng.randrange(4), None]
        self.flow = 0.0
        self.spin = {}
        self.cursor = [1, 2]
        self.clears = 0
        self.tick = 0
        self.leak = 0

    def _path(self):
        c = COLS // 2
        path = [(0, c)]
        r = 0
        while r < ROWS - 1:
            if self.rng.random() < 0.42 and 0 < c < COLS - 1:
                c += self.rng.choice((-1, 1))
                if (r, c) not in path:
                    path.append((r, c))
            r += 1
            path.append((r, c))
        return path

    def _rot_for(self, kind, opens):
        n = 2 if kind == "I" else 4
        for rot in range(n):
            if openings(kind, rot) == opens:
                return rot
        return 0

    def step_auto(self):
        self.tick += 1
        if self.leak:
            self.leak -= 1
            if self.leak == 0:
                self.reset()
            return
        head = min(int(self.flow) + 1, len(self.path) - 1)
        cell = self.path[head]
        kind, rot, good = self.tiles[cell]
        if good is not None and rot != good and cell not in self.spin:
            self.spin[cell] = 0
        for key in list(self.spin):
            self.spin[key] += 1
            if self.spin[key] >= 6:
                k, _, g = self.tiles[key]
                self.tiles[key][1] = g if g is not None else (self.tiles[key][1] + 1) % 4
                del self.spin[key]
        if self.tick % 9 == 0:
            decoy = (self.rng.randrange(ROWS), self.rng.randrange(COLS))
            if decoy not in self.need and decoy not in self.spin:
                self.spin[decoy] = 0
        self.flow += 0.085
        if self.flow >= len(self.path):
            self.score += 80 + len(self.path) * 6
            self.clears += 1
            keep = self.score
            self.reset()
            self.score = keep

    def step_play(self, keys, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                if ev.key == pygame.K_r:
                    self.score = 0
                    self.reset()
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.cursor[1] = max(0, self.cursor[1] - 1)
                if ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.cursor[1] = min(COLS - 1, self.cursor[1] + 1)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.cursor[0] = max(0, self.cursor[0] - 1)
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.cursor[0] = min(ROWS - 1, self.cursor[0] + 1)
                if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._rotate(tuple(self.cursor))
            if ev.type == pygame.MOUSEBUTTONDOWN:
                r = (ev.pos[1] - OY) // CELL
                c = (ev.pos[0] - OX) // CELL
                if 0 <= r < ROWS and 0 <= c < COLS:
                    self.cursor = [r, c]
                    self._rotate((r, c))
        if self.leak:
            self.leak -= 1
            return True
        cell = self.path[min(int(self.flow), len(self.path) - 1)]
        kind, rot, good = self.tiles[cell]
        if good is not None and rot != good and int(self.flow) > 0:
            self.leak = 28
            return True
        self.flow += 0.04
        if self.flow >= len(self.path):
            self.score += 80
            keep = self.score
            self.reset()
            self.score = keep
        return True

    def _rotate(self, cell):
        kind, rot, good = self.tiles[cell]
        n = 2 if kind == "I" else 4
        self.tiles[cell][1] = (rot + 1) % n
        if cell in self.need and openings(kind, self.tiles[cell][1]) == self.need[cell]:
            self.score += 15

    def draw(self, surf):
        surf.fill(INK)
        for y in range(0, H, 6):
            t = y / H
            col = (10 + int(18 * t), 14 + int(10 * (1 - t)), 36 + int(28 * t))
            pygame.draw.line(surf, col, (0, y), (W, y), 6)
        for x, y, s in self.flakes:
            yy = (y + self.tick * (0.6 + s)) % H
            pygame.draw.circle(surf, FLASH[int(s * 3) % 3], (int(x), int(yy)), 2)
        title = self.font.render("LABRADORITE LATTICE", True, CREAM)
        surf.blit(title, title.get_rect(center=(W // 2, 110)))
        sub = self.small.render("PIPE FLOW  \u00b7  ROTATE THE VEIN", True, TEAL)
        surf.blit(sub, sub.get_rect(center=(W // 2, 172)))
        score = self.mid.render(f"SCORE  {self.score:04d}", True, GOLD)
        surf.blit(score, score.get_rect(center=(W // 2, 236)))
        pygame.draw.rect(surf, (22, 28, 58), (OX - 18, OY - 70, COLS * CELL + 36, 56), border_radius=16)
        pygame.draw.rect(surf, GOLD, (OX + CELL * self.path[0][1] + 36, OY - 58, CELL - 72, 28), border_radius=8)
        vat_c = self.path[-1][1]
        pygame.draw.rect(surf, (22, 28, 58), (OX - 18, OY + ROWS * CELL + 14, COLS * CELL + 36, 56), border_radius=16)
        pygame.draw.rect(surf, TEAL, (OX + CELL * vat_c + 36, OY + ROWS * CELL + 28, CELL - 72, 28), border_radius=8)
        for r in range(ROWS):
            for c in range(COLS):
                self._tile(surf, r, c)
        self._flow(surf)
        tag = self.mid.render("x.com/ElbowOS", True, CREAM)
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 90)))
        hint = self.small.render("ARROWS + SPACE   \u00b7   PYTHON 3", True, (170, 180, 210))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 42)))

    def _tile(self, surf, r, c):
        kind, rot, good = self.tiles[(r, c)]
        x, y = OX + c * CELL, OY + r * CELL
        rect = pygame.Rect(x + 8, y + 8, CELL - 16, CELL - 16)
        on_path = (r, c) in self.need
        pygame.draw.rect(surf, (18, 24, 48) if on_path else (14, 18, 36), rect, border_radius=18)
        spin = self.spin.get((r, c), 0)
        ang = rot * (90 if kind == "L" else 180) + (spin / 6) * (90 if kind == "L" else 180)
        col = FLASH[(r + c) % 3]
        cx, cy = x + CELL // 2, y + CELL // 2
        opens = openings(kind, rot if spin == 0 else max(0, rot))
        if spin:
            opens = openings(kind, rot)
        self._pipes(surf, cx, cy, opens, col, ang if spin else None, kind, rot, spin)
        if [r, c] == self.cursor and PLAY:
            pygame.draw.rect(surf, GOLD, rect, 4, border_radius=18)

    def _pipes(self, surf, cx, cy, opens, col, _ang, kind, rot, spin):
        show = openings(kind, rot)
        if spin:
            show = openings(kind, (rot + 1) % (2 if kind == "I" else 4))
        reach = CELL // 2 - 14
        pygame.draw.circle(surf, col, (cx, cy), 18)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 7)
        for d in show:
            dr, dc = DELTA[d]
            ex, ey = cx + dc * reach, cy + dr * reach
            pygame.draw.line(surf, col, (cx, cy), (ex, ey), 22)
            pygame.draw.line(surf, (255, 255, 255), (cx, cy), (ex, ey), 6)
            pygame.draw.circle(surf, col, (int(ex), int(ey)), 12)

    def _flow(self, surf):
        if self.leak:
            return
        n = len(self.path)
        dist = min(self.flow, n - 0.01)
        pts = []
        for i in range(int(dist) + 1):
            r, c = self.path[i]
            pts.append((OX + c * CELL + CELL // 2, OY + r * CELL + CELL // 2))
        r, c = self.path[int(dist)]
        nr, nc = self.path[min(int(dist) + 1, n - 1)]
        frac = dist - int(dist)
        x1 = OX + c * CELL + CELL // 2
        y1 = OY + r * CELL + CELL // 2
        x2 = OX + nc * CELL + CELL // 2
        y2 = OY + nr * CELL + CELL // 2
        pts.append((x1 + (x2 - x1) * frac, y1 + (y2 - y1) * frac))
        if len(pts) > 1:
            pygame.draw.lines(surf, GOLD, False, pts, 16)
            pygame.draw.lines(surf, (255, 250, 220), False, pts, 5)
        hx, hy = pts[-1]
        pulse = 16 + int(6 * math.sin(self.tick * 0.4))
        pygame.draw.circle(surf, GOLD, (int(hx), int(hy)), pulse)
        pygame.draw.circle(surf, CREAM, (int(hx), int(hy)), 7)
        self.score += 1 if self.tick % 4 == 0 else 0

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            running = self.step_play(pygame.key.get_pressed(), pygame.event.get())
            self.tick += 1
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.step_auto()
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
