import tempfile
import unittest
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from unittest.mock import patch

from toolbar.bridge import NativeBridge
from toolbar.windows import focus_process


class BridgeTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.bridge = NativeBridge(Path(temporary.name) / 'settings.json')

    def test_window_callback_can_save_preferences_during_resize(self):
        window = SimpleNamespace(x=20, y=40, width=760, height=64,
                                 native=SimpleNamespace(_scale=1, WindowState='Normal'),
                                 move=lambda *_: None)
        self.bridge._window = window

        def resize(width, height):
            window.width, window.height = width, height
            callback = Thread(target=self.bridge._remember_geometry)
            callback.start()
            callback.join(timeout=.5)
            self.assertFalse(callback.is_alive(), 'Fechamento bloqueado pelo redimensionamento')

        window.resize = resize
        with patch('toolbar.bridge.fit_bounds', return_value=(20,40,1120,760)):
            self.bridge.set_expanded(True)

    def test_closing_minimized_keeps_normal_geometry(self):
        self.bridge.save_preferences({'x': 100, 'y': 50})
        self.bridge._window = SimpleNamespace(x=-32000, y=-32000,
                                              native=SimpleNamespace(WindowState='Minimized'))
        self.bridge._remember_geometry()
        self.assertEqual(self.bridge.get_preferences()['x'],100)
        self.assertEqual(self.bridge.get_preferences()['y'],50)

    def test_rejected_foreground_request_is_not_reported_as_focus(self):
        with patch('toolbar.windows.process_family', return_value={123}), \
                patch('toolbar.windows.user32') as api:
            api.EnumWindows.side_effect=lambda callback,_: callback(7,0)
            api.GetWindowThreadProcessId.side_effect=lambda _handle,pid: setattr(pid._obj,'value',123)
            api.IsWindowVisible.return_value=1
            api.IsIconic.return_value=0
            api.SetForegroundWindow.return_value=0
            api.GetForegroundWindow.return_value=8
            self.assertFalse(focus_process(123))


if __name__ == '__main__':
    unittest.main()
