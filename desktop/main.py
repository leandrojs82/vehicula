"""Entrada compartilhada pelo painel e pelos apps nativos."""
import argparse
import logging
import runpy
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="Vehicula")
    parser.add_argument("--tool", default=None)
    args = parser.parse_args(argv)
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    if args.tool not in (None, "preparafrota", "pbix"):
        print("Ferramenta desconhecida.", file=sys.stderr)
        return 2
    from toolbar.preferences import user_directory
    data_dir = user_directory()
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=data_dir / "errors.log", level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        if args.tool == "preparafrota":
            sys.path.insert(0, str(root / "tools/preparafrota"))
            from preparafrota.ui import run
            return run()
        if args.tool == "pbix":
            sys.path.insert(0, str(root / "tools/pbix"))
            runpy.run_path(str(root / "tools/pbix/app.py"), run_name="__main__")
            return 0
        from toolbar.shell import run
        return run()
    except Exception:
        logging.exception("Falha ao executar %s", args.tool or "painel")
        from toolbar.windows import show_error
        name = {"preparafrota": "PreparaFrota", "pbix": "PBIX para Excel"}.get(args.tool, "Vehicula")
        show_error(f"Vehicula — {name}", f"Não foi possível iniciar {name}.\n\n"
                   "Confira os arquivos do pacote e os pré-requisitos indicados no LEIA-ME.\n\n"
                   f"Detalhes em {data_dir / 'errors.log'}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
