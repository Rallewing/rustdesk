import unittest
from taskbar_helper import TaskbarController


class FakeShell:
    def __init__(self, state):
        self.state = state
        self.pointer_inside = False

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def move_pointer_inside(self):
        self.pointer_inside = True


class TaskbarTests(unittest.TestCase):
    def test_hidden_taskbar_becomes_visible_and_stays_visible_until_next_toggle(self):
        shell = FakeShell(3)
        control = TaskbarController(shell)
        self.assertFalse(control.toggle())
        self.assertEqual(shell.get_state(), 2)
        self.assertTrue(control.toggle())
        self.assertEqual(shell.get_state(), 3)
        self.assertTrue(shell.pointer_inside)

    def test_external_setting_change_is_respected(self):
        shell = FakeShell(1)
        control = TaskbarController(shell)
        shell.state = 0
        self.assertTrue(control.toggle())
        self.assertEqual(shell.get_state(), 1)

    def test_exit_restores_original_taskbar_setting(self):
        shell = FakeShell(0)
        control = TaskbarController(shell)
        control.toggle()
        control.restore()
        self.assertEqual(shell.get_state(), 0)


if __name__ == '__main__':
    unittest.main()
