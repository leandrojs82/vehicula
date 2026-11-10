import logging
import winreg

from .bridge import NativeBridge
from .launcher import resource_root
from .preferences import user_directory
from .windows import fit_bounds, show_error


def runtime_available():
    runtime_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{runtime_id}",
                                    0, winreg.KEY_READ | view) as key:
                    version, _ = winreg.QueryValueEx(key, "pv")
                    if version and version != "0.0.0.0":
                        return True
            except OSError:
                pass
    return False


def create_app():
    import webview
    data = user_directory()
    data.mkdir(parents=True, exist_ok=True)
    bridge = NativeBridge(data / "settings.json")
    prefs = bridge.get_preferences()
    x, y, width, height = fit_bounds(prefs["x"], prefs["y"], 760, 64)
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
    # A persistência nativa permite uma origem própria para cada execução.
    webview.settings["DEFAULT_HTTP_PORT"] = None
    window = webview.create_window("Vehicula", str(resource_root() / "web/index.html"),
                                   js_api=bridge, width=width, height=height, x=x, y=y,
                                   frameless=True, easy_drag=False, resizable=True,
                                   min_size=(min(760, width), 64), on_top=prefs["on_top"],
                                   background_color="#121214", text_select=True)
    bridge._window = window
    window.events.closing += bridge._remember_geometry
    return window, bridge


def run():
    if not runtime_available():
        show_error("Preparação do Vehicula", "Instale o Microsoft Edge WebView2 Runtime para abrir o painel.\n\n"
                   "O instalador oficial e a opção offline estão disponíveis em\n"
                   "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
                   "Depois da instalação, abra o Vehicula novamente.")
        return 1
    import webview
    create_app()
    logging.getLogger("pywebview").setLevel(logging.WARNING)
    webview.start(gui="edgechromium", http_server=True, private_mode=False,
                  storage_path=str(user_directory() / "webview"),
                  icon=str(resource_root() / "web/vehicula.ico"),
                  localization={"global.saveFile": "Salvar arquivo", "global.openFile": "Abrir arquivo",
                                "windows.fileFilter.allFiles": "Todos os arquivos"})
    return 0
