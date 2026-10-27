"""소년(Boy)의 상태 클래스.

각 상태는 자기 상태에서의 입력 처리, 갱신, 그리기를 담당한다.
Boy 는 활성 상태 객체(self.state_obj)에 작업을 위임하고,
상태 전환은 Boy.change_state() 로만 수행한다.
"""

from pico2d import SDLK_a, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE


class BoyState:
    """모든 상태가 공유하는 인터페이스와 기본 동작."""

    name = 'STATE'
    animation_name = 'IDLE'
    is_invincible = False

    def enter(self, boy):
        # 상태에 들어올 때 애니메이션을 처음부터 재생
        boy.frame = 0
        boy.frame_time = 0.0

    def update(self, boy, dt):
        pass

    def handle_keydown(self, boy, key):
        pass

    def handle_keyup(self, boy, key):
        pass

    def draw(self, boy):
        right_row, left_row = boy.ANIMATION_ROWS[self.animation_name]
        row = right_row if boy.face_dir == 1 else left_row
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, boy.y)


class IdleState(BoyState):
    """가만히 서 있는 상태. 5초 동안 입력이 없으면 잠든다."""

    name = 'IDLE'
    animation_name = 'IDLE'
    SLEEP_DELAY = 5.0

    def enter(self, boy):
        super().enter(boy)
        boy.idle_time = 0.0    # IDLE 로 들어올 때마다 5초 타이머를 처음부터 다시 시작

    def update(self, boy, dt):
        boy.idle_time += dt
        if boy.idle_time >= IdleState.SLEEP_DELAY:
            boy.change_state(SleepState)
            return

        boy.advance_animation(dt)

    def handle_keydown(self, boy, key):
        if key == SDLK_LEFT:
            boy.face_dir = -1
            boy.change_state(RunState)
        elif key == SDLK_RIGHT:
            boy.face_dir = 1
            boy.change_state(RunState)
        elif key == SDLK_a:
            boy.change_state(AutoRunState)
        else:
            # IDLE 에서는 어떤 키 입력이든 "입력이 있었다"로 보고 타이머를 초기화
            boy.idle_time = 0.0


class SleepState(BoyState):
    """누워서 자는 상태. Space 로 기상한다."""

    name = 'SLEEP'
    animation_name = 'IDLE'

    def handle_keydown(self, boy, key):
        if key == SDLK_SPACE:
            boy.change_state(IdleState)
        elif key == SDLK_LEFT:
            boy.face_dir = -1
            boy.change_state(RunState)
        elif key == SDLK_RIGHT:
            boy.face_dir = 1
            boy.change_state(RunState)

    def draw(self, boy):
        # 전용 수면 이미지가 없으므로 서 있는 프레임을 눕혀서 그린다.
        # (오른쪽 보기 프레임을 반시계 방향 90도 회전 -> 머리는 왼쪽, 얼굴은 위)
        boy.image.clip_composite_draw(
            boy.frame * 100, boy.ANIMATION_ROWS[SleepState.name][0], 100, 100,
            boy.SLEEP_ROTATION, '', boy.x, boy.y + boy.SLEEP_Y_OFFSET, 100, 100)


class RunState(BoyState):
    """방향키로 조작하는 달리기 상태."""

    name = 'RUN'
    animation_name = 'RUN'
    SPEED = 250

    def update(self, boy, dt):
        boy.x += boy.face_dir * RunState.SPEED * dt
        boy.clamp_to_screen()
        boy.advance_animation(dt)

    def handle_keydown(self, boy, key):
        if key == SDLK_LEFT:
            boy.face_dir = -1
        elif key == SDLK_RIGHT:
            boy.face_dir = 1

    def handle_keyup(self, boy, key):
        if key not in (SDLK_LEFT, SDLK_RIGHT):
            return

        if boy.left_down or boy.right_down:
            # 남아 있는 방향키 쪽으로 계속 달린다
            boy.face_dir = -1 if boy.left_down else 1
        else:
            # 방향키를 모두 놓으면 IDLE 로 (5초 타이머는 enter 에서 재시작)
            boy.change_state(IdleState)


class AutoRunState(BoyState):
    """'a' 키로 진입하는 자동 무적 런 상태.

    입력 없이도 계속 달리고, 일정 시간이 지나면 IDLE 로 돌아간다.
    """

    name = 'AUTORUN'
    animation_name = 'RUN'
    is_invincible = True

    SPEED = 400         # 자동 이동 속도 (픽셀/초) - RUN(250)보다 빠르다
    SCALE = 1.3         # 표시 크기 배율 - RUN(1.0)보다 크다
    DURATION = 5.0      # 자동 런 유지 시간 (초)

    def enter(self, boy):
        super().enter(boy)
        self.elapsed = 0.0
        self.direction = boy.face_dir

    def update(self, boy, dt):
        self.elapsed += dt
        if self.elapsed >= AutoRunState.DURATION:
            boy.change_state(IdleState)
            return

        boy.x += self.direction * AutoRunState.SPEED * dt
        boy.clamp_to_screen()
        boy.face_dir = self.direction
        boy.advance_animation(dt)

    def handle_keydown(self, boy, key):
        # 자동 런 중 'a' 재입력은 무시한다 (타이머를 다시 시작하지 않는다)
        pass

    def draw(self, boy):
        right_row, left_row = boy.ANIMATION_ROWS[self.animation_name]
        row = right_row if boy.face_dir == 1 else left_row
        size = 100 * AutoRunState.SCALE
        # 발 위치가 잔디에서 뜨지 않도록 확대분의 절반만큼 위로 올려 그린다.
        draw_y = boy.y + 50 * (AutoRunState.SCALE - 1)
        boy.image.clip_draw(boy.frame * 100, row, 100, 100,
                            boy.x, draw_y, size, size)

