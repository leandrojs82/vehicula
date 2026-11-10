"""Entrada visual. O processamento fica no pacote preparafrota."""
try:
    from preparafrota.ui import run
except ImportError as exc:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror('Preparação do PreparaFrota', 'Instale as dependências indicadas no LEIA-ME.md:\n\npy -3 -m pip install -r requirements.txt\n\n' + str(exc))
    root.destroy()
else:
    run()
