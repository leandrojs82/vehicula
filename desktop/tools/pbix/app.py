"""Interface de desktop para o conversor PBIX."""
import os
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Empty, SimpleQueue
from tkinter import filedialog, messagebox, ttk


FUNDO = "#edf2f6"
BRANCO = "#ffffff"
TINTA = "#172b43"
SUAVE = "#486078"
BORDA = "#cdd8e4"
AZUL = "#164b83"
GELO = "#e1ecf8"
AUTOMATICAS = ("DateTableTemplate_", "LocalDateTable_")


def resumir(texto, limite):
    return texto if len(texto) <= limite else f"…{texto[-limite + 1:]}"


def carregar(arquivo, anterior):
    from exportacao import abrir_modelo

    modelo = abrir_modelo(arquivo)
    try:
        tabelas = sorted(map(str, modelo.tables), key=str.casefold)
    except Exception:
        modelo.close()
        raise
    if anterior is not None:
        anterior.close()
    return modelo, tabelas


def converter(modelo, arquivo, tabelas, pasta, formato, texto, eventos):
    from exportacao import exportar

    def informar(indice, total, tabela):
        eventos.put(f"Exportando {indice} de {total}  •  {resumir(tabela, 52)}")

    return exportar(modelo, arquivo, tabelas, pasta, formato, texto, informar)


class Aplicativo:
    def __init__(self, janela):
        self.janela = janela
        janela.title("PBIX para Excel")
        janela.configure(bg=FUNDO)
        janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.worker = ThreadPoolExecutor(max_workers=1)
        self.eventos = SimpleQueue()
        self.tarefa = None
        self.modelo = self.arquivo = self.pasta = self.resultado = None
        self.tabelas = []
        self.visiveis = []
        self.selecao = set()
        self.formato = tk.StringVar(janela, "unico")
        self.texto = tk.BooleanVar(janela)
        self.automaticas = tk.BooleanVar(janela)
        self.status = tk.StringVar(janela, "Somente tabelas com dados importados.")
        self.estilos()
        self.montar()
        self.atualizar_controles()
        janela.update_idletasks()
        janela.minsize(780, janela.winfo_reqheight() + 12)
        janela.geometry(f"860x{janela.winfo_reqheight() + 28}")
        self.abrir.focus_set()

    def estilos(self):
        estilo = ttk.Style(self.janela)
        estilo.theme_use("clam")
        estilo.configure(".", font=("Segoe UI", 10), foreground=TINTA)
        estilo.configure("TButton", background=BRANCO, bordercolor=BORDA,
                         lightcolor=BRANCO, darkcolor=BRANCO, padding=(13, 7))
        estilo.map("TButton", background=[("active", GELO), ("disabled", FUNDO)],
                   bordercolor=[("focus", AZUL)], foreground=[("disabled", "#61758a")])
        estilo.configure("Azul.TButton", background=AZUL, foreground=BRANCO,
                         bordercolor=AZUL, lightcolor=AZUL, darkcolor=AZUL,
                         font=("Segoe UI", 10, "bold"))
        estilo.map("Azul.TButton", background=[("disabled", GELO), ("active", "#123c68")],
                   foreground=[("disabled", SUAVE)], bordercolor=[("focus", "#6199d1")])
        estilo.configure("TCheckbutton", background=BRANCO, padding=(0, 3))
        estilo.configure("TRadiobutton", background=BRANCO, padding=(0, 3))
        for tipo in ("TCheckbutton", "TRadiobutton"):
            estilo.map(tipo, background=[("active", BRANCO)],
                       foreground=[("disabled", "#61758a")])
        estilo.configure("Horizontal.TProgressbar", background=AZUL,
                         troughcolor=GELO, bordercolor=GELO, lightcolor=AZUL, darkcolor=AZUL)

    def rotulo(self, pai, texto, tamanho=10, peso="normal", cor=TINTA, **opcoes):
        return tk.Label(pai, text=texto, font=("Segoe UI", tamanho, peso),
                        fg=cor, bg=pai["bg"], anchor="w", justify="left", **opcoes)

    def painel(self, pai):
        return tk.Frame(pai, bg=BRANCO, padx=18, pady=15,
                        highlightbackground=BORDA, highlightthickness=1)

    def montar(self):
        pagina = tk.Frame(self.janela, bg=FUNDO, padx=28, pady=22)
        pagina.pack(fill="both", expand=True)
        pagina.columnconfigure(0, weight=1)
        pagina.rowconfigure(2, weight=1)

        topo = tk.Frame(pagina, bg=FUNDO)
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        marca = tk.Canvas(topo, width=47, height=47, bg=FUNDO, highlightthickness=0)
        marca.pack(side="left", padx=(0, 12))
        marca.create_rectangle(0, 0, 47, 47, fill=AZUL, outline="")
        marca.create_rectangle(11, 10, 35, 35, outline=BRANCO, width=2)
        marca.create_rectangle(12, 11, 34, 17, fill="#a8c8eb", outline="")
        marca.create_line(23, 18, 23, 35, fill=BRANCO, width=2)
        marca.create_line(11, 26, 35, 26, fill=BRANCO, width=2)
        titulos = tk.Frame(topo, bg=FUNDO)
        titulos.pack(side="left")
        self.rotulo(titulos, "PBIX para Excel", 23, "bold").pack(anchor="w")
        self.rotulo(titulos, "Exporte tabelas de um relatório do Power BI.", cor=SUAVE).pack(anchor="w")

        entrada = self.painel(pagina)
        entrada.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        entrada.columnconfigure(0, weight=1)
        self.rotulo(entrada, "Arquivo de origem", 11, "bold").grid(row=0, column=0, sticky="w")
        self.nome = self.rotulo(entrada, "Nenhum arquivo selecionado", cor=SUAVE)
        self.nome.grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.abrir = ttk.Button(entrada, text="Abrir .pbix…", style="Azul.TButton",
                                command=self.escolher_arquivo)
        self.abrir.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        corpo = tk.Frame(pagina, bg=FUNDO)
        corpo.grid(row=2, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=3, uniform="painel")
        corpo.columnconfigure(1, weight=2, uniform="painel")
        corpo.rowconfigure(0, weight=1)

        tabelas = self.painel(corpo)
        tabelas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tabelas.columnconfigure(0, weight=1)
        tabelas.rowconfigure(1, weight=1)
        self.rotulo(tabelas, "Tabelas", 14, "bold").grid(row=0, column=0, sticky="w")
        lista = tk.Frame(tabelas, bg=BRANCO, highlightbackground=BORDA, highlightthickness=1)
        lista.grid(row=1, column=0, sticky="nsew", pady=(10, 8))
        self.lista = tk.Listbox(lista, selectmode="multiple", exportselection=False,
                                font=("Segoe UI", 11), width=1, height=8, borderwidth=0,
                                highlightthickness=2, highlightbackground=BRANCO,
                                highlightcolor=AZUL, bg=BRANCO, fg=TINTA,
                                selectbackground=GELO, selectforeground=AZUL, activestyle="dotbox")
        barra = ttk.Scrollbar(lista, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.lista.pack(side="left", fill="both", expand=True)
        self.lista.bind("<<ListboxSelect>>", self.mudar_selecao)
        self.lista.bind("<Control-a>", lambda _: self.marcar(True))
        self.vazio = self.rotulo(lista, "Abra um .pbix para ver as tabelas.", cor=SUAVE)
        self.vazio.place(relx=.5, rely=.5, anchor="center")

        selecao = tk.Frame(tabelas, bg=BRANCO)
        selecao.grid(row=2, column=0, sticky="ew")
        self.todos = ttk.Button(selecao, text="Selecionar todas", command=lambda: self.marcar(True))
        self.todos.pack(side="left", padx=(0, 6))
        self.nenhum = ttk.Button(selecao, text="Limpar seleção", command=lambda: self.marcar(False))
        self.nenhum.pack(side="left")
        self.contagem = self.rotulo(tabelas, "", cor=SUAVE)
        self.contagem.grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.mostrar_auto = ttk.Checkbutton(tabelas, text="Mostrar tabelas de datas automáticas",
                                           variable=self.automaticas, command=self.mostrar_tabelas)
        self.mostrar_auto.grid(row=4, column=0, sticky="w", pady=(4, 0))

        opcoes = self.painel(corpo)
        opcoes.grid(row=0, column=1, sticky="nsew")
        self.rotulo(opcoes, "Exportação", 14, "bold").pack(anchor="w")
        self.rotulo(opcoes, "Formato", 10, "bold").pack(anchor="w", pady=(12, 3))
        self.botoes_formato = []
        for valor, titulo in (
            ("unico", "Excel único, com uma aba por tabela"),
            ("separado", "Um Excel por tabela"),
            ("csv", "Um CSV por tabela"),
        ):
            botao = ttk.Radiobutton(opcoes, text=titulo, value=valor, variable=self.formato,
                                    command=self.atualizar_controles)
            botao.pack(anchor="w")
            self.botoes_formato.append(botao)
        self.como_texto = ttk.Checkbutton(opcoes, text="Gravar valores como texto", variable=self.texto)
        self.como_texto.pack(anchor="w", pady=(10, 0))
        self.nota_texto = self.rotulo(opcoes, "", cor=SUAVE, wraplength=245)
        self.nota_texto.pack(anchor="w")

        tk.Frame(opcoes, bg=BORDA, height=1).pack(fill="x", pady=13)
        self.rotulo(opcoes, "Pasta de destino", 10, "bold").pack(anchor="w")
        self.destino = self.rotulo(opcoes, "Ao lado do arquivo .pbix", cor=SUAVE)
        self.destino.pack(anchor="w", pady=(3, 7))
        self.alterar = ttk.Button(opcoes, text="Escolher pasta…", command=self.escolher_pasta)
        self.alterar.pack(anchor="w")

        rodape = tk.Frame(pagina, bg=FUNDO)
        rodape.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        rodape.columnconfigure(0, weight=1)
        self.mensagem = self.rotulo(rodape, "", cor=SUAVE, textvariable=self.status, wraplength=450)
        self.mensagem.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.abrir_saida = ttk.Button(rodape, text="Abrir resultado", command=self.abrir_resultado)
        self.abrir_saida.grid(row=0, column=1, padx=(0, 8))
        self.abrir_saida.grid_remove()
        self.exportar = ttk.Button(rodape, text="Exportar tabelas", style="Azul.TButton",
                                   command=self.iniciar_exportacao)
        self.exportar.grid(row=0, column=2, sticky="e")
        self.progresso = ttk.Progressbar(pagina, mode="indeterminate")
        self.progresso.grid(row=4, column=0, sticky="ew", pady=(9, 0))
        self.progresso.grid_remove()

    def atualizar_controles(self):
        ocupado = self.tarefa is not None
        qtd = len(self.lista.curselection())
        self.contagem.configure(text=f"{qtd} de {len(self.visiveis)} selecionadas")
        estados = (
            (self.abrir, not ocupado),
            (self.alterar, not ocupado),
            (self.lista, not ocupado and bool(self.visiveis)),
            (self.todos, not ocupado and qtd < len(self.visiveis)),
            (self.nenhum, not ocupado and qtd > 0),
            (self.mostrar_auto, not ocupado and any(t.startswith(AUTOMATICAS) for t in self.tabelas)),
            (self.como_texto, not ocupado and self.formato.get() != "csv"),
            (self.exportar, not ocupado and qtd > 0),
            (self.abrir_saida, not ocupado),
        )
        for controle, habilitado in estados:
            controle.configure(state="normal" if habilitado else "disabled")
        for botao in self.botoes_formato:
            botao.configure(state="disabled" if ocupado else "normal")
        csv = self.formato.get() == "csv"
        self.nota_texto.configure(text="CSV com separador ponto e vírgula." if csv
                                  else "Útil para preservar zeros à esquerda em identificadores.")
        if self.resultado is None:
            self.abrir_saida.grid_remove()
        else:
            self.abrir_saida.grid()

    def mudar_selecao(self, _=None):
        self.selecao.difference_update(self.visiveis)
        self.selecao.update(self.visiveis[i] for i in self.lista.curselection())
        self.atualizar_controles()

    def mostrar_tabelas(self):
        self.visiveis = [t for t in self.tabelas if self.automaticas.get() or not t.startswith(AUTOMATICAS)]
        self.lista.configure(state="normal")
        self.lista.delete(0, "end")
        for indice, tabela in enumerate(self.visiveis):
            self.lista.insert("end", tabela)
            if tabela in self.selecao:
                self.lista.selection_set(indice)
        if self.visiveis:
            self.vazio.place_forget()
        else:
            texto = "Nenhuma tabela disponível." if self.modelo is not None else "Abra um .pbix para ver as tabelas."
            self.vazio.configure(text=texto)
            self.vazio.place(relx=.5, rely=.5, anchor="center")
        self.atualizar_controles()

    def marcar(self, marcar):
        if self.tarefa is None and self.visiveis:
            if marcar:
                self.lista.selection_set(0, "end")
            else:
                self.lista.selection_clear(0, "end")
            self.mudar_selecao()
        return "break"

    def escolher_arquivo(self):
        arquivo = filedialog.askopenfilename(parent=self.janela, title="Abrir relatório do Power BI",
                                              filetypes=[("Relatório do Power BI", "*.pbix")])
        if arquivo:
            arquivo = Path(arquivo)
            self.executar("Lendo o arquivo .pbix…", carregar, (arquivo, self.modelo),
                          lambda dados: self.modelo_carregado(arquivo, dados))

    def modelo_carregado(self, arquivo, dados):
        self.arquivo = arquivo
        self.modelo, self.tabelas = dados
        self.automaticas.set(False)
        self.selecao = {t for t in self.tabelas if not t.startswith(AUTOMATICAS)}
        self.resultado = None
        self.nome.configure(text=resumir(arquivo.name, 57), fg=TINTA)
        self.status.set("Selecione as tabelas e o formato de exportação." if self.selecao
                        else "Nenhuma tabela de dados importados na lista.")
        self.mostrar_tabelas()
        if self.visiveis:
            self.lista.focus_set()

    def escolher_pasta(self):
        base = self.pasta or (self.arquivo.parent if self.arquivo else Path.home())
        pasta = filedialog.askdirectory(parent=self.janela, title="Escolher pasta de destino",
                                        initialdir=str(base), mustexist=True)
        if pasta:
            self.pasta = Path(pasta)
            self.destino.configure(text=resumir(str(self.pasta), 33))

    def iniciar_exportacao(self):
        tabelas = [self.visiveis[i] for i in self.lista.curselection()]
        pasta = self.pasta or self.arquivo.parent
        formato = self.formato.get()
        texto = formato != "csv" and self.texto.get()
        self.resultado = None
        self.executar("Preparando exportação…", converter,
                      (self.modelo, self.arquivo, tabelas, pasta, formato, texto, self.eventos),
                      self.exportacao_concluida)

    def exportacao_concluida(self, resultado):
        self.resultado = resultado
        qtd = sum(1 for item in resultado.iterdir() if item.is_file())
        arquivos = "1 arquivo salvo" if qtd == 1 else f"{qtd} arquivos salvos"
        self.status.set(f"{arquivos} em {resumir(resultado.name, 37)}.")

    def abrir_resultado(self):
        try:
            os.startfile(str(self.resultado))
        except OSError as erro:
            messagebox.showerror("Pasta indisponível", str(erro), parent=self.janela)

    def executar(self, mensagem, funcao, argumentos, concluir):
        self.status.set(mensagem)
        self.tarefa = self.worker.submit(funcao, *argumentos)
        self.atualizar_controles()
        self.progresso.grid()
        self.progresso.start(16)
        self.janela.after(80, self.verificar, concluir)

    def verificar(self, concluir):
        try:
            while True:
                self.status.set(self.eventos.get_nowait())
        except Empty:
            pass
        if not self.tarefa.done():
            self.janela.after(80, self.verificar, concluir)
            return
        tarefa = self.tarefa
        self.tarefa = None
        self.progresso.stop()
        self.progresso.grid_remove()
        try:
            concluir(tarefa.result())
        except Exception as erro:
            self.status.set("A operação falhou. Confira os detalhes e tente novamente.")
            detalhe = str(erro) or type(erro).__name__
            messagebox.showerror("Falha na operação", detalhe[:1000], parent=self.janela)
        self.atualizar_controles()

    def fechar(self):
        if self.tarefa is not None:
            return
        if self.modelo is not None:
            self.worker.submit(self.modelo.close)
        self.worker.shutdown()
        self.janela.destroy()


if __name__ == "__main__":
    janela = tk.Tk()
    Aplicativo(janela)
    janela.mainloop()

