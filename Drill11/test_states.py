"""Drill #11 수용 기준 자동 테스트.

pico2d 창을 열지 않고 상태 로직만 검증하기 위해, 테스트에서는
pico2d 모듈을 최소 스텁으로 대체한다.

실행: python test_states.py
"""

import sys
import types
import unittest


# ---------- pico2d 스텁 ----------
class FakeImage:
    def __init__(self):
        self.calls = []

    def clip_draw(self, *args):
        self.calls.append(args)

    def clip_composite_draw(self, *args):
        self.calls.append(args)


pico2d = types.ModuleType('pico2d')
pico2d.SDL_KEYDOWN = 1
pico2d.SDL_KEYUP = 2
pico2d.SDLK_a = 97
pico2d.SDLK_LEFT = 1073741904
pico2d.SDLK_RIGHT = 1073741903
pico2d.SDLK_SPACE = 32
pico2d.get_canvas_width = lambda: 800
pico2d.load_image = lambda name: FakeImage()
sys.modules['pico2d'] = pico2d

from boy import Boy                      # noqa: E402
from states import AutoRunState, RunState  # noqa: E402


class Event:
    def __init__(self, event_type, key):
        self.type = event_type
        self.key = key


def keydown(key):
    return Event(pico2d.SDL_KEYDOWN, key)


def keyup(key):
    return Event(pico2d.SDL_KEYUP, key)


class BoyStateTest(unittest.TestCase):
    def setUp(self):
        self.boy = Boy()

    # T1: 'a' 로 AutoRun 진입
    def test_a_starts_autorun(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.assertTrue(self.boy.is_invincible)

    # T2: 5초 경과 후 Idle 복귀
    def test_autorun_returns_to_idle_after_5_seconds(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.boy.update(4.9)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.boy.update(0.2)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertFalse(self.boy.is_invincible)
        self.assertEqual(self.boy.idle_time, 0.0)

    # T3: 자동 이동 속도 400px/s, RUN 은 250px/s
    def test_autorun_moves_faster_than_run(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        x0 = self.boy.x
        self.boy.update(0.1)
        self.assertAlmostEqual(self.boy.x - x0, AutoRunState.SPEED * 0.1)

        self.boy = Boy()
        self.boy.handle_event(keydown(pico2d.SDLK_RIGHT))
        x0 = self.boy.x
        self.boy.update(0.1)
        self.assertAlmostEqual(self.boy.x - x0, RunState.SPEED * 0.1)
        self.assertGreater(AutoRunState.SPEED, RunState.SPEED)

    # T3: 1.3배 확대 + 발 기준 보정
    def test_autorun_draws_scaled_from_feet(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.boy.draw()
        frame_x, row, w, h, x, y, draw_w, draw_h = self.boy.image.calls[-1]
        self.assertEqual((w, h), (100, 100))
        self.assertAlmostEqual(draw_w, 100 * AutoRunState.SCALE)
        self.assertAlmostEqual(draw_h, 100 * AutoRunState.SCALE)
        self.assertAlmostEqual(y, self.boy.y + 50 * (AutoRunState.SCALE - 1))

    # T4: 좌우 끝에서 자동 방향 전환
    def test_autorun_bounces_at_both_edges(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        margin = 50 * AutoRunState.SCALE

        self.boy.x = 800 - margin - 1
        self.boy.update(0.1)
        self.assertEqual(self.boy.x, 800 - margin)
        self.assertEqual(self.boy.face_dir, -1)

        self.boy.x = margin + 1
        self.boy.update(0.1)
        self.assertEqual(self.boy.x, margin)
        self.assertEqual(self.boy.face_dir, 1)

    # T5/T6: 방향키로 AutoRun 취소 -> Run
    def test_autorun_cancelled_by_arrow_keys(self):
        for key, expected_dir in ((pico2d.SDLK_LEFT, -1),
                                  (pico2d.SDLK_RIGHT, 1)):
            self.boy = Boy()
            self.boy.handle_event(keydown(pico2d.SDLK_a))
            self.boy.update(0.5)
            self.boy.handle_event(keydown(key))
            self.assertEqual(self.boy.state, 'RUN')
            self.assertEqual(self.boy.face_dir, expected_dir)
            self.assertFalse(self.boy.is_invincible)

    # T7: AutoRun 중 'a' 재입력 무시
    def test_autorun_ignores_a(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.boy.update(1.0)
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.boy.update(3.9)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.boy.update(0.2)
        self.assertEqual(self.boy.state, 'IDLE')

    # T8: SLEEP 에서 'a' 무시
    def test_sleep_ignores_a(self):
        self.boy.update(5.0)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.assertEqual(self.boy.state, 'SLEEP')

    # T9: AutoRun 취소 후에는 5초 타이머가 되살아나지 않는다
    def test_cancel_discards_autorun_timer(self):
        self.boy.handle_event(keydown(pico2d.SDLK_a))
        self.boy.update(4.9)
        self.boy.handle_event(keydown(pico2d.SDLK_LEFT))
        self.assertEqual(self.boy.state, 'RUN')
        self.boy.update(0.2)
        self.assertEqual(self.boy.state, 'RUN')

    # T10: 기존 상태 회귀
    def test_existing_states_still_work(self):
        self.boy.handle_event(keydown(pico2d.SDLK_RIGHT))
        self.assertEqual(self.boy.state, 'RUN')
        self.boy.handle_event(keyup(pico2d.SDLK_RIGHT))
        self.assertEqual(self.boy.state, 'IDLE')

        self.boy.update(5.0)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.boy.handle_event(keydown(pico2d.SDLK_SPACE))
        self.assertEqual(self.boy.state, 'IDLE')

        self.boy.handle_event(keydown(pico2d.SDLK_LEFT))
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.face_dir, -1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
