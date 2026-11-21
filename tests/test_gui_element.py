import contextlib
import io
import unittest

from GUI_Element import GUI_Element


class GuiElementTests(unittest.TestCase):
    def test_click_state_changes_do_not_print_debug_messages(self):
        element = GUI_Element()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            element.set_clicked(True)
            element.set_clicked(False)
        self.assertEqual(output.getvalue(), '')
        self.assertFalse(element.clicked)


if __name__ == '__main__':
    unittest.main()
