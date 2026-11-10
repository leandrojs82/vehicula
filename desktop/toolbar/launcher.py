import logging
import subprocess
import sys
from pathlib import Path
from threading import Lock

from .windows import focus_process


TOOL_NAMES = {"preparafrota": "PreparaFrota", "pbix": "PBIX para Excel"}


def resource_root():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def tool_command(tool_id):
    if tool_id not in TOOL_NAMES:
        raise ValueError("Ferramenta desconhecida.")
    command = [sys.executable]
    if not getattr(sys, "frozen", False):
        command.append(str(resource_root() / "main.py"))
    return command + ["--tool", tool_id]


class ToolLauncher:
    def __init__(self):
        self.processes = {}
        self.lock = Lock()

    def open(self, tool_id):
        if tool_id not in TOOL_NAMES:
            return {"status": "error", "message": "Ferramenta desconhecida."}
        try:
            command = tool_command(tool_id)
            with self.lock:
                process = self.processes.get(tool_id)
                if process is not None and process.poll() is None:
                    focused = focus_process(process.pid)
                    return {"status": "focused" if focused else "opening",
                            "message": f"{TOOL_NAMES[tool_id]} {'aberto.' if focused else 'está abrindo…'}"}
                process = subprocess.Popen(command, cwd=resource_root(),
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                self.processes[tool_id] = process
            return {"status": "opening", "message": f"Abrindo {TOOL_NAMES[tool_id]}…"}
        except (OSError, ValueError) as error:
            logging.exception("Falha ao iniciar ferramenta")
            return {"status": "error", "message": f"Não foi possível abrir a ferramenta. {error}"}

    def status(self):
        with self.lock:
            return {name: process.poll() is None for name, process in self.processes.items()}
