import math

from pico2d import (load_image, get_canvas_width,
                    SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT)
from transitions import Machine


class Boy:
    # ---------- 상태 정의 ----------
    IDLE = 'IDLE'
    SLEEP = 'SLEEP'
    RUN = 'RUN'
    STATES = [IDLE, SLEEP, RUN]

    # 상태별 애니메이션 시트의 행(y) : (오른쪽 보기, 왼쪽 보기)
    ANIMATION_ROWS = {
        IDLE: (300, 200),
        # 수면 전용 애니메이션이 없어 IDLE 시트의 첫 프레임을 90도 눕혀서 사용
        SLEEP: (300, 200),
        RUN: (100, 0),
    }

    # SLEEP 은 서 있는 프레임을 반시계 방향으로 90도 회전해 눕힌 자세로 그린다.
    SLEEP_ROTATION = math.radians(90)
    # 눕힌 자세의 몸통이 잔디 위에 닿도록 그리는 위치를 살짝 낮춘다.
    SLEEP_Y_OFFSET = -12

    # ---------- 애니메이션 설정 ----------
    FRAME_COUNT = 8         # 한 상태의 프레임 수 (가로 8칸)
    FRAME_TIME = 0.1        # 프레임 한 장당 유지 시간 (초)

    # ---------- 이동 / 상태 전이 설정 ----------
    RUN_SPEED = 250         # 달릴 때 이동 속도 (픽셀/초)
    SCREEN_MARGIN = 50      # 캐릭터 중심이 화면 가장자리에서 떨어져야 하는 거리
    SLEEP_DELAY = 5.0       # IDLE 에서 입력 없이 이 시간(초)이 지나면 SLEEP

    def __init__(self):
        self.x, self.y = 400, 90
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        self.frame = 0
        self.frame_time = 0.0
        self.idle_time = 0.0    # IDLE 에서 마지막 입력 이후 흐른 시간
        self.left_down = False  # 왼쪽 방향키를 누르고 있는지
        self.right_down = False # 오른쪽 방향키를 누르고 있는지

        # ---------- 상태 머신 ----------
        self.machine = Machine(
            model=self,
            states=Boy.STATES,
            initial=Boy.IDLE,
        )
        # IDLE 에서 5초 동안 입력이 없으면 SLEEP 으로
        self.machine.add_transition('sleep', Boy.IDLE, Boy.SLEEP)
        # SLEEP 에서 SPACE 를 누르면 IDLE 로
        self.machine.add_transition('wake', Boy.SLEEP, Boy.IDLE)
        # IDLE / SLEEP 에서 방향키를 누르면 RUN 으로 (SLEEP 이면 즉시 기상해서 달린다)
        self.machine.add_transition('run', [Boy.IDLE, Boy.SLEEP], Boy.RUN)
        # RUN 에서 방향키를 모두 놓으면 IDLE 로
        self.machine.add_transition('stop', Boy.RUN, Boy.IDLE)

        # 상태로 "들어올 때" 애니메이션과 타이머를 초기화
        self.machine.on_enter_IDLE('enter_IDLE')
        self.machine.on_enter_SLEEP('enter_SLEEP')
        self.machine.on_enter_RUN('enter_RUN')
        self.enter_IDLE()

    # ---------- 상태 콜백 ----------
    def enter_IDLE(self):
        self.frame = 0
        self.frame_time = 0.0
        self.idle_time = 0.0    # IDLE 로 들어올 때마다 5초 타이머를 처음부터 다시 시작

    def enter_SLEEP(self):
        self.frame = 0
        self.frame_time = 0.0

    def enter_RUN(self):
        self.frame = 0
        self.frame_time = 0.0

    # ---------- 입력 처리 ----------
    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_LEFT:
                self.left_down = True
                self.start_running(-1)
            elif event.key == SDLK_RIGHT:
                self.right_down = True
                self.start_running(1)
            elif event.key == SDLK_SPACE and self.state == Boy.SLEEP:
                self.wake()
            elif self.state == Boy.IDLE:
                # IDLE 에서는 어떤 키 입력이든 "입력이 있었다"로 보고 타이머를 초기화
                self.idle_time = 0.0
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_down = False
                self.update_running_direction()
            elif event.key == SDLK_RIGHT:
                self.right_down = False
                self.update_running_direction()

    def start_running(self, direction):
        self.face_dir = direction
        if self.state != Boy.RUN:
            self.run()

    def update_running_direction(self):
        if self.state != Boy.RUN:
            return

        if self.left_down or self.right_down:
            # 남아 있는 방향키 쪽으로 계속 달린다
            self.face_dir = -1 if self.left_down else 1
        else:
            # 방향키를 모두 놓으면 IDLE 로 (5초 타이머는 enter_IDLE 에서 재시작)
            self.stop()

    # ---------- 갱신 / 그리기 ----------
    def advance_animation(self, dt):
        self.frame_time += dt
        while self.frame_time >= Boy.FRAME_TIME:
            self.frame_time -= Boy.FRAME_TIME
            self.frame = (self.frame + 1) % Boy.FRAME_COUNT

    def update(self, dt):
        if self.state == Boy.RUN:
            self.x += self.face_dir * Boy.RUN_SPEED * dt
            # 캐릭터가 화면 밖으로 나가지 않도록 제한
            self.x = max(Boy.SCREEN_MARGIN,
                         min(get_canvas_width() - Boy.SCREEN_MARGIN, self.x))
            self.advance_animation(dt)
            return

        if self.state != Boy.IDLE:
            return

        self.idle_time += dt
        if self.idle_time >= Boy.SLEEP_DELAY:
            self.sleep()
            return

        # IDLE 애니메이션 반복 재생
        self.advance_animation(dt)

    def draw(self):
        if self.state == Boy.SLEEP:
            # 전용 수면 이미지가 없으므로 서 있는 프레임을 눕혀서 그린다.
            # (오른쪽 보기 프레임을 반시계 방향 90도 회전 -> 머리는 왼쪽, 얼굴은 위)
            self.image.clip_composite_draw(
                self.frame * 100, Boy.ANIMATION_ROWS[Boy.SLEEP][0], 100, 100,
                Boy.SLEEP_ROTATION, '', self.x, self.y + Boy.SLEEP_Y_OFFSET, 100, 100)
            return

        right_row, left_row = Boy.ANIMATION_ROWS[self.state]
        row = right_row if self.face_dir == 1 else left_row
        self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
