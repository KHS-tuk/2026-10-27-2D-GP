"""Drill #11 상태 다이어그램 생성 스크립트.

`python docs/make_state_diagram.py` 로 실행하면 같은 폴더에
`state_diagram.png` 가 생성된다. (Pillow 필요)
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 800
BG = '#FAFAFA'
TEXT = '#222222'
MUTED = '#555555'
ARROW = '#444444'
NODE_FILL = '#FFFFFF'
NODE_LINE = '#2C3E50'
AUTO_FILL = '#FFF3E0'
AUTO_LINE = '#E67E22'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_REGULAR = r'C:\Windows\Fonts\malgun.ttf'
FONT_BOLD = r'C:\Windows\Fonts\malgunbd.ttf'


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def draw_node(draw, cx, cy, w, h, text, font, fill=NODE_FILL,
              outline=NODE_LINE, width=3):
    draw.rounded_rectangle(
        [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
        radius=16, fill=fill, outline=outline, width=width)
    draw_center_text(draw, cx, cy, text, font)


def draw_center_text(draw, cx, cy, text, font, fill=TEXT):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]),
              text, font=font, fill=fill)


def draw_label(draw, x, y, text, font, fill=MUTED):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    # 선 위에 글자가 겹치지 않도록 배경을 깔아 준다.
    draw.rectangle([x - w / 2 - 5, y - h / 2 - 4,
                    x + w / 2 + 5, y + h / 2 + 4], fill=BG)
    draw.text((x - w / 2 - bbox[0], y - h / 2 - bbox[1]),
              text, font=font, fill=fill)


def draw_arrow(draw, points, width=3, color=ARROW, head=13):
    draw.line(points, fill=color, width=width, joint='curve')
    (x1, y1), (x2, y2) = points[-2], points[-1]
    angle = math.atan2(y2 - y1, x2 - x1)
    p2 = (x2 - head * math.cos(angle - 0.45),
          y2 - head * math.sin(angle - 0.45))
    p3 = (x2 - head * math.cos(angle + 0.45),
          y2 - head * math.sin(angle + 0.45))
    draw.polygon([(x2, y2), p2, p3], fill=color)


def main():
    image = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    title_font = load_font(FONT_BOLD, 34)
    node_font = load_font(FONT_BOLD, 26)
    label_font = load_font(FONT_REGULAR, 20)
    note_font = load_font(FONT_REGULAR, 20)
    note_title_font = load_font(FONT_BOLD, 22)

    draw.text((40, 22), 'Boy 상태 다이어그램 — Drill #11 AutoRun',
              font=title_font, fill=TEXT)

    # ---------- 상태 노드 ----------
    draw_node(draw, 550, 130, 180, 80, 'IDLE', node_font)
    draw_node(draw, 950, 330, 230, 90, 'AUTORUN', node_font,
              fill=AUTO_FILL, outline=AUTO_LINE, width=5)
    draw_node(draw, 180, 330, 180, 80, 'SLEEP', node_font)
    draw_node(draw, 550, 580, 180, 80, 'RUN', node_font)

    # 시작 상태 표시
    draw.ellipse([404, 99, 416, 111], fill=TEXT)
    draw_arrow(draw, [(416, 105), (460, 105)])

    # ---------- 전이 ----------
    # IDLE -> AUTORUN
    draw_arrow(draw, [(630, 160), (850, 300)])
    draw_label(draw, 755, 205, "a 키다운", label_font)

    # AUTORUN -> IDLE (5초 경과, 위쪽 우회)
    draw_arrow(draw, [(950, 285), (950, 120), (640, 120)])
    draw_label(draw, 800, 103, "5초 이상 경과", label_font)

    # AUTORUN -> RUN
    draw_arrow(draw, [(880, 375), (630, 545)])
    draw_label(draw, 790, 495, "← / → 키다운", label_font)

    # IDLE -> SLEEP
    draw_arrow(draw, [(490, 165), (255, 295)])
    draw_label(draw, 390, 220, "5초 무입력", label_font)

    # SLEEP -> IDLE (Space, 왼쪽 우회)
    draw_arrow(draw, [(90, 330), (45, 330), (45, 150), (460, 150)])
    draw_label(draw, 205, 132, "Space", label_font)

    # IDLE -> RUN
    draw_arrow(draw, [(550, 170), (550, 540)])
    draw_label(draw, 455, 375, "← / → 키다운", label_font)

    # SLEEP -> RUN
    draw_arrow(draw, [(270, 350), (460, 555)])
    draw_label(draw, 315, 475, "← / → 키다운", label_font)

    # RUN -> IDLE
    draw_arrow(draw, [(595, 540), (595, 170)])
    draw_label(draw, 700, 430, "방향키 모두 해제", label_font)

    # ---------- AutoRun 설명 ----------
    draw.rounded_rectangle([820, 560, 1150, 730], radius=14,
                           fill=AUTO_FILL, outline=AUTO_LINE, width=2)
    draw.text((845, 578), 'AUTORUN 상태', font=note_title_font, fill=AUTO_LINE)
    notes = [
        '· 자동 좌우 이동 (400px/s)',
        '· 크기 1.3배 확대 + 무적',
        '· 좌우 끝에서 방향 반전',
        '· 5초 후 IDLE 복귀',
    ]
    for i, line in enumerate(notes):
        draw.text((845, 615 + i * 28), line, font=note_font, fill=TEXT)

    output = os.path.join(BASE_DIR, 'state_diagram.png')
    image.save(output)
    print(f'saved: {output}')


if __name__ == '__main__':
    main()
