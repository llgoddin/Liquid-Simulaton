import unittest

from ui_controls import CountRepeater


class CountRepeaterTests(unittest.TestCase):
    def test_single_press_is_immediate_then_waits_before_repeat(self):
        repeat = CountRepeater()
        self.assertEqual(repeat.press('+', 0.0), 1)
        self.assertEqual(repeat.update(0.1), 0)
        self.assertEqual(repeat.update(0.4), 1)
        self.assertEqual(repeat.update(0.41), 0)

    def test_repeat_accelerates_and_release_stops_it(self):
        repeat = CountRepeater()
        repeat.press('+', 0.0)
        counts = []
        for second in (1, 2, 3):
            counts.append(sum(repeat.update(i / 100) for i in range((second - 1) * 100 + 1, second * 100 + 1)))
        self.assertLess(counts[0], counts[1])
        self.assertLessEqual(counts[1], counts[2])
        repeat.release()
        self.assertEqual(repeat.update(20), 0)
        self.assertIsNone(repeat.action)

    def test_new_press_resets_acceleration(self):
        repeat = CountRepeater()
        repeat.press('+', 0)
        repeat.update(3)
        repeat.release()
        self.assertEqual(repeat.press('-', 4), 1)
        self.assertEqual(repeat.update(4.1), 0)
        self.assertEqual(repeat.action, '-')


if __name__ == '__main__':
    unittest.main()
