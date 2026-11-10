import logging
from threading import RLock

from .launcher import ToolLauncher
from .preferences import clean_preferences, load_preferences, save_preferences
from .windows import fit_bounds


class NativeBridge:
    def __init__(self, settings_path):
        self._settings_path = settings_path
        self._preferences = load_preferences(settings_path)
        self._window = None
        self._expanded = False
        self._launcher = ToolLauncher()
        self._lock = RLock()
        self._window_lock = RLock()

    def get_preferences(self):
        with self._lock:
            return dict(self._preferences)

    def save_preferences(self, changes):
        if not isinstance(changes, dict):
            raise ValueError("Configuração inválida.")
        with self._lock:
            self._preferences = clean_preferences({**self._preferences, **changes})
            save_preferences(self._settings_path, self._preferences)
            return dict(self._preferences)

    def open_tool(self, tool_id):
        return self._launcher.open(tool_id)

    def get_tool_status(self):
        return self._launcher.status()

    def set_expanded(self, expanded):
        if type(expanded) is not bool:
            raise ValueError("Estado da janela inválido.")
        with self._window_lock:
            if self._expanded == expanded:
                return {"expanded": expanded}
            self._remember_geometry()
            self._expanded = expanded
            width = self._preferences["expanded_width"] if expanded else 760
            height = self._preferences["expanded_height"] if expanded else 64
            scale = getattr(self._window.native, '_scale', 1)
            x, y, width, height = fit_bounds(self._window.x, self._window.y, width, height, scale)
            self._window.resize(width, height)
            self._window.move(x, y)
            return {"expanded": expanded}

    def set_on_top(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("Preferência inválida.")
        self._window.on_top = enabled
        self.save_preferences({"on_top": enabled})
        return {"on_top": enabled}

    def minimize(self):
        self._remember_geometry()
        self._window.minimize()

    def close(self):
        self._window.destroy()

    def _remember_geometry(self):
        try:
            if str(self._window.native.WindowState) == 'Minimized':
                return
            geometry = {"x": self._window.x, "y": self._window.y}
            if self._expanded:
                geometry.update(expanded_width=self._window.width, expanded_height=self._window.height)
            self.save_preferences(geometry)
        except OSError:
            logging.exception("Falha ao salvar posição da janela")
