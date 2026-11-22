# -*- coding: utf-8 -*-
"""
俄罗斯方块 Tetris
完整的经典俄罗斯方块游戏，使用 pygame 开发。
功能：7 种标准方块、旋转、移动、软降/硬降、消行计分、等级加速、
      下一个方块预览、落点虚影、暂停、游戏结束与重新开始。
"""

import os
import random
import sys

import pygame

# ---------------------------------------------------------------- 初始化
pygame.init()

# ---------------------------------------------------------------- 常量
CELL = 30                       # 每格像素
COLS, ROWS = 10, 20             # 游戏区行列
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
WIN_W, WIN_H = 820, 700
BOARD_X, BOARD_Y = 40, 40       # 游戏区左上角屏幕坐标
PANEL_X = 520                   # 侧边信息面板起始 X
FPS = 60

# ---------------------------------------------------------------- 配色
BG = (18, 18, 28)
PANEL = (32, 34, 52)
GRID = (42, 44, 64)
WHITE = (236, 236, 246)
GRAY = (158, 160, 182)
ACCENT = (90, 200, 250)
SHADOW = (0, 0, 0)

SHAPE_COLORS = {
    "I": (0, 212, 224),
    "O": (246, 212, 64),
    "T": (172, 92, 232),
    "S": (92, 212, 116),
    "Z": (236, 84, 96),
    "J": (72, 132, 236),
    "L": (246, 152, 64),
}

SHAPES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
}


# ---------------------------------------------------------------- 字体
def load_font(size, bold=False):
    """优先加载 Windows 中文字体，否则回退到系统字体。"""
    candidates = []
    if bold:
        candidates += ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]
    else:
        candidates += ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    return pygame.font.SysFont("arial", size, bold=bold)


FONT_TITLE = load_font(34, bold=True)
FONT_BIG = load_font(26, bold=True)
FONT_MID = load_font(20)
FONT_SMALL = load_font(16)


# ---------------------------------------------------------------- 游戏状态
board = [[0 for _ in range(COLS)] for _ in range(ROWS)]  # 0=空，否则为方块类型字符
bag = []                                                 # 随机袋，保证 7 种均匀出现


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.color = SHAPE_COLORS[kind]
        spawn_x = COLS // 2 - len(self.shape[0]) // 2
        # I 型特殊处理，让它居中更自然
        if kind == "I":
            spawn_x = COLS // 2 - 2
        self.x = spawn_x
        self.y = 0

    def rotate(self):
        """顺时针旋转，并做简单的贴墙修正（wall kick）。"""
        if self.kind == "O":
            return
        old = self.shape
        new = [list(row) for row in zip(*old[::-1])]
        self.shape = new
        if collide(new, self.x, self.y):
            for dx in (-1, 1, -2, 2):
                if not collide(new, self.x + dx, self.y):
                    self.x += dx
                    return
            self.shape = old  # 无处可转则还原


def next_kind():
    global bag
    if not bag:
        bag = list(SHAPES.keys())
        random.shuffle(bag)
    return bag.pop()


def collide(shape, px, py):
    """检测方块在 (px,py) 处是否与边界或已固定方块冲突。"""
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                gx, gy = px + x, py + y
                if gx < 0 or gx >= COLS or gy >= ROWS:
                    return True
                if gy >= 0 and board[gy][gx]:
                    return True
    return False


def merge(piece):
    """把方块固定到棋盘上。"""
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell and piece.y + y >= 0:
                board[piece.y + y][piece.x + x] = piece.kind


def clear_lines():
    """消除满行，返回消除行数。"""
    full = [i for i in range(ROWS) if all(board[i])]
    for i in full:
        del board[i]
        board.insert(0, [0 for _ in range(COLS)])
    return len(full)


def ghost_y(piece):
    """计算当前方块硬降后的落点 Y。"""
    gy = piece.y
    while not collide(piece.shape, piece.x, gy + 1):
        gy += 1
    return gy


# ---------------------------------------------------------------- 全局变量
current = None
next_piece = None
score = 0
lines = 0
level = 1
game_over = False
paused = False
fall_time = 0.0

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def reset_game():
    global board, current, next_piece, score, lines, level
    global game_over, paused, fall_time, bag
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    bag = []
    current = Piece(next_kind())
    next_piece = Piece(next_kind())
    score = 0
    lines = 0
    level = 1
    game_over = False
    paused = False
    fall_time = 0.0


def fall_speed():
    """随等级提升的下落速度（秒/格）。"""
    return max(0.05, 0.55 - (level - 1) * 0.05)


def hard_drop():
    global score
    while not collide(current.shape, current.x, current.y + 1):
        current.y += 1
        score += 2
    lock_piece()


def lock_piece():
    global current, next_piece, level, game_over
    merge(current)
    cleared = clear_lines()
    if cleared:
        score += LINE_SCORES.get(cleared, 0) * level
        lines += cleared
        level = lines // 10 + 1
    current = next_piece
    next_piece = Piece(next_kind())
    if collide(current.shape, current.x, current.y):
        game_over = True


# ---------------------------------------------------------------- 绘制
def draw_cell(surface, x, y, color, ghost=False):
    rect = pygame.Rect(x, y, CELL, CELL)
    if ghost:
        s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, 55), (0, 0, CELL, CELL))
        pygame.draw.rect(s, (*color, 130), (0, 0, CELL, CELL), 2)
        surface.blit(s, rect)
        return
    pygame.draw.rect(surface, color, rect)
    # 立体高光
    pygame.draw.line(surface, (255, 255, 255), (x + 2, y + 2), (x + CELL - 3, y + 2), 2)
    pygame.draw.line(surface, (255, 255, 255), (x + 2, y + 2), (x + 2, y + CELL - 3), 2)
    pygame.draw.line(surface, SHADOW, (x + 2, y + CELL - 3), (x + CELL - 3, y + CELL - 3), 2)
    pygame.draw.line(surface, SHADOW, (x + CELL - 3, y + 2), (x + CELL - 3, y + CELL - 3), 2)


def draw_board(surface):
    # 棋盘底板
    pygame.draw.rect(surface, PANEL, (BOARD_X - 4, BOARD_Y - 4, BOARD_W + 8, BOARD_H + 8))
    # 网格
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(
                surface, GRID,
                (BOARD_X + c * CELL, BOARD_Y + r * CELL, CELL - 1, CELL - 1)
            )
    # 已固定方块
    for r in range(ROWS):
        for c in range(COLS):
            kind = board[r][c]
            if kind:
                draw_cell(surface, BOARD_X + c * CELL, BOARD_Y + r * CELL, SHAPE_COLORS[kind])

    if current and not game_over:
        # 落点虚影
        gy = ghost_y(current)
        for y, row in enumerate(current.shape):
            for x, cell in enumerate(row):
                if cell and gy + y >= 0:
                    draw_cell(surface, BOARD_X + (current.x + x) * CELL,
                              BOARD_Y + (gy + y) * CELL, current.color, ghost=True)
        # 当前方块
        for y, row in enumerate(current.shape):
            for x, cell in enumerate(row):
                if cell and current.y + y >= 0:
                    draw_cell(surface, BOARD_X + (current.x + x) * CELL,
                              BOARD_Y + (current.y + y) * CELL, current.color)

    # 边框
    pygame.draw.rect(surface, ACCENT, (BOARD_X - 4, BOARD_Y - 4, BOARD_W + 8, BOARD_H + 8), 2)


def draw_next(surface):
    txt = FONT_BIG.render("下一个", True, WHITE)
    surface.blit(txt, (PANEL_X, 250))
    box = pygame.Rect(PANEL_X, 292, 160, 130)
    pygame.draw.rect(surface, PANEL, box)
    pygame.draw.rect(surface, ACCENT, box, 2)
    if next_piece:
        shape = next_piece.shape
        # 去掉空行空列以居中
        rows = [i for i, row in enumerate(shape) if any(row)]
        cols = [j for j in range(len(shape[0])) if any(shape[i][j] for i in range(len(shape)))]
        if rows and cols:
            h = len(rows)
            w = len(cols)
            ox = PANEL_X + (box.width - w * 24) // 2 - cols[0] * 24
            oy = box.y + (box.height - h * 24) // 2 - rows[0] * 24
            for i in rows:
                for j in cols:
                    if shape[i][j]:
                        r = pygame.Rect(ox + j * 24, oy + i * 24, 22, 22)
                        pygame.draw.rect(surface, next_piece.color, r)
                        pygame.draw.rect(surface, (255, 255, 255), r, 1)


def draw_panel(surface):
    surface.blit(FONT_TITLE.render("俄罗斯方块", True, ACCENT), (PANEL_X, 40))

    surface.blit(FONT_MID.render("分数", True, GRAY), (PANEL_X, 110))
    surface.blit(FONT_BIG.render(str(score), True, WHITE), (PANEL_X, 134))

    surface.blit(FONT_MID.render("等级", True, GRAY), (PANEL_X + 150, 110))
    surface.blit(FONT_BIG.render(str(level), True, WHITE), (PANEL_X + 150, 134))

    surface.blit(FONT_MID.render("消除行数", True, GRAY), (PANEL_X, 185))
    surface.blit(FONT_BIG.render(str(lines), True, WHITE), (PANEL_X + 110, 185))

    draw_next(surface)

    # 操作说明
    help_y = 450
    surface.blit(FONT_MID.render("操作说明", True, ACCENT), (PANEL_X, help_y))
    helps = [
        "← →    左右移动",
        "↑ / X   旋转方块",
        "↓       加速下落",
        "空格    直接落底",
        "P       暂停 / 继续",
        "R       重新开始",
    ]
    for i, text in enumerate(helps):
        surface.blit(FONT_SMALL.render(text, True, GRAY), (PANEL_X, help_y + 34 + i * 28))


def draw_overlay(surface, title, subtitle):
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))
    t = FONT_TITLE.render(title, True, WHITE)
    s = FONT_MID.render(subtitle, True, ACCENT)
    surface.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - 25)))
    surface.blit(s, s.get_rect(center=(WIN_W // 2, WIN_H // 2 + 25)))


# ---------------------------------------------------------------- 主循环
def main():
    global fall_time, paused
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("俄罗斯方块 - Tetris")
    clock = pygame.time.Clock()
    reset_game()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    continue
                if event.key == pygame.K_p:
                    if not game_over:
                        paused = not paused
                    continue
                if game_over or paused:
                    continue
                if event.key == pygame.K_LEFT:
                    if not collide(current.shape, current.x - 1, current.y):
                        current.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if not collide(current.shape, current.x + 1, current.y):
                        current.x += 1
                elif event.key == pygame.K_UP or event.key == pygame.K_x:
                    current.rotate()
                elif event.key == pygame.K_DOWN:
                    if not collide(current.shape, current.x, current.y + 1):
                        current.y += 1
                        score += 1
                elif event.key == pygame.K_SPACE:
                    hard_drop()

        if not game_over and not paused:
            fall_time += dt
            if fall_time >= fall_speed():
                fall_time = 0.0
                if not collide(current.shape, current.x, current.y + 1):
                    current.y += 1
                else:
                    lock_piece()

        # 绘制
        screen.fill(BG)
        draw_board(screen)
        draw_panel(screen)
        if paused:
            draw_overlay(screen, "已暂停", "按 P 继续游戏")
        elif game_over:
            draw_overlay(screen, "游戏结束", "按 R 重新开始")
        pygame.display.flip()


if __name__ == "__main__":
    main()
