import math

from pico2d import (load_image, get_canvas_width,
                    SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT)
from states import IdleState, RunState, SleepState


class Boy:
    # 상태별 애니메이션 시트의 행(y) : (오른쪽 보기, 왼쪽 보기)
    ANIMATION_ROWS = {
        'IDLE': (300, 200),
        # 수면 전용 애니메이션이 없어 IDLE 시트의 첫 프레임을 90도 눕혀서 사용
        'SLEEP': (300, 200),
        'RUN': (100, 0),
    }

    # SLEEP 은 서 있는 프레임을 반시계 방향으로 90도 회전해 눕힌 자세로 그린다.
    SLEEP_ROTATION = math.radians(90)
    # 눕힌 자세의 몸통이 잔디 위에 닿도록 그리는 위치를 살짝 낮춘다.
    SLEEP_Y_OFFSET = -12

    # ---------- 애니메이션 설정 ----------
    FRAME_COUNT = 8         # 한 상태의 프레임 수 (가로 8칸)
    FRAME_TIME = 0.1        # 프레임 한 장당 유지 시간 (초)

    # ---------- 이동 설정 ----------
    SCREEN_MARGIN = 50      # 캐릭터 중심이 화면 가장자리에서 떨어져야 하는 거리

    def __init__(self):
        self.x, self.y = 400, 90
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        self.frame = 0
        self.frame_time = 0.0
        self.idle_time = 0.0    # IDLE 에서 마지막 입력 이후 흐른 시간
        self.left_down = False  # 왼쪽 방향키를 누르고 있는지
        self.right_down = False # 오른쪽 방향키를 누르고 있는지

        self.state_obj = None
        self.is_invincible = False
        self.change_state(IdleState)

    # ---------- 상태 전환 ----------
    @property
    def state(self):
        return self.state_obj.name

    def change_state(self, state_class):
        self.state_obj = state_class()
        self.is_invincible = state_class.is_invincible
        self.state_obj.enter(self)

    # ---------- 입력 처리 ----------
    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_down = True
            elif event.key == SDLK_RIGHT:
                self.right_down = True
            self.state_obj.handle_keydown(self, event.key)
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_down = False
            elif event.key == SDLK_RIGHT:
                self.right_down = False
            self.state_obj.handle_keyup(self, event.key)

    # ---------- 갱신 / 그리기 ----------
    def advance_animation(self, dt):
        self.frame_time += dt
        while self.frame_time >= Boy.FRAME_TIME:
            self.frame_time -= Boy.FRAME_TIME
            self.frame = (self.frame + 1) % Boy.FRAME_COUNT

    def clamp_to_screen(self, margin=None):
        if margin is None:
            margin = Boy.SCREEN_MARGIN
        self.x = max(margin, min(get_canvas_width() - margin, self.x))

    def update(self, dt):
        self.state_obj.update(self, dt)

    def draw(self):
        self.state_obj.draw(self)
