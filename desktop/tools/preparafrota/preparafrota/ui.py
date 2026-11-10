"""Janela mínima: arquivos, uma tabela de revisão e exportação."""
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import webbrowser
from . import __version__, processor, validation
from .constants import COLUMNS, JOIN_FIELDS
from .errors import AppError, SheetRequired
from .exporter import export_csv


class App:
    def __init__(self, root):
        self.root, self.session = root, None
        self.reference_source = self.previous_update = self.last_result = None
        self.sheets, self.items = {}, {}
        self.selected = None
        root.title('PreparaFrota')
        root.geometry('1040x690')
        root.minsize(860, 580)
        root.configure(background='#f5f7f9')
        self._style()
        self.file_var = tk.StringVar(value='Selecione uma planilha semanal.')
        self.reference_var = tk.StringVar(value='Nenhuma referência selecionada')
        self.status_var = tk.StringVar(value='O tipo de arquivo será reconhecido pelos cabeçalhos.')
        self.caption_var = tk.StringVar(value='Os dados aparecerão aqui após a seleção do arquivo.')
        self.view_var = tk.StringVar(value='Prévia CSV')
        self.value_var, self.bulk_var = tk.StringVar(), tk.BooleanVar(value=False)
        self.situation_var, self.query_var = tk.StringVar(), tk.StringVar()
        self.candidate_var, self.edit_label_var = tk.StringVar(), tk.StringVar()
        self.warning_var = tk.StringVar()
        body = ttk.Frame(root, padding=22)
        body.pack(fill='both', expand=True)
        title = ttk.Frame(body)
        title.pack(fill='x', pady=(0, 18))
        ttk.Label(title, text='PreparaFrota', style='Title.TLabel').pack(side='left')
        ttk.Label(title, text=__version__, style='Muted.TLabel').pack(side='right')
        files = ttk.Frame(body)
        files.pack(fill='x')
        ttk.Button(files, text='Abrir planilha', command=self.choose_file).pack(side='left')
        ttk.Label(files, textvariable=self.file_var, wraplength=720).pack(side='left', padx=14)
        self.reference_frame = ttk.Frame(body, padding=(0, 10, 0, 0))
        ttk.Button(self.reference_frame, text='Referência…', command=self.choose_reference).pack(side='left')
        self.reuse_button = ttk.Button(self.reference_frame, text='Usar revisão anterior', command=self.reuse_reference)
        self.reuse_button.pack(side='left', padx=8)
        self.supplement_button = ttk.Button(self.reference_frame, text='Consultar faltantes…', command=self.choose_complement)
        self.reference_label = ttk.Label(self.reference_frame, textvariable=self.reference_var, wraplength=590, style='Muted.TLabel')
        self.reference_label.pack(side='left', padx=6)
        self.status_label = ttk.Label(body, textvariable=self.status_var, wraplength=950)
        self.status_label.pack(fill='x', pady=(16, 14))
        toolbar = ttk.Frame(body)
        toolbar.pack(fill='x', pady=(0, 8))
        ttk.Label(toolbar, text='Exibir').pack(side='left', padx=(0, 8))
        self.view_combo = ttk.Combobox(toolbar, textvariable=self.view_var, values=['Prévia CSV', 'Pendências', 'Movimentação', 'Avisos'], state='readonly', width=22)
        self.view_combo.pack(side='left')
        self.view_combo.bind('<<ComboboxSelected>>', lambda event: self.refresh())
        ttk.Label(toolbar, textvariable=self.caption_var, style='Muted.TLabel').pack(side='left', padx=14)
        table = ttk.Frame(body)
        table.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table, show='headings', selectmode='browse')
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(table, orient='horizontal', command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        self.tree.tag_configure('pending', background='#fff0d5', foreground='#674819')
        self.tree.tag_configure('inclusion', background='#e6f2ee', foreground='#255748')
        self.tree.tag_configure('exclusion', background='#f9e8e4', foreground='#754238')
        self.tree.bind('<<TreeviewSelect>>', self.select_item)
        self.tree.bind('<Double-1>', self.edit_preview)
        self.editor = ttk.Frame(body, padding=(0, 10, 0, 0))
        ttk.Label(self.editor, textvariable=self.edit_label_var).pack(anchor='w', pady=(0, 5))
        edit_line = ttk.Frame(self.editor)
        edit_line.pack(fill='x')
        entry = ttk.Entry(edit_line, textvariable=self.value_var)
        entry.pack(side='left', fill='x', expand=True)
        entry.bind('<Return>', lambda event: self.apply_edit())
        ttk.Button(edit_line, text='Aplicar', command=self.apply_edit).pack(side='left', padx=(8, 0))
        self.confirm_button = ttk.Button(edit_line, text='Confirmar como está', command=self.confirm_current, state='disabled')
        self.confirm_button.pack(side='left', padx=(8, 0))
        ttk.Checkbutton(self.editor, text='Preencher os demais vazios desta coluna', variable=self.bulk_var).pack(anchor='w', pady=(4, 0))
        self.lookup_editor = ttk.Frame(body, padding=(0, 10, 0, 0))
        self.candidate_combo = ttk.Combobox(self.lookup_editor, textvariable=self.candidate_var, state='readonly')
        self.candidate_combo.pack(fill='x', pady=(0, 6))
        self.candidate_combo.bind('<<ComboboxSelected>>', self.choose_candidate)
        lookup_line = ttk.Frame(self.lookup_editor)
        lookup_line.pack(fill='x')
        ttk.Label(lookup_line, text='Situação').pack(side='left')
        ttk.Entry(lookup_line, textvariable=self.situation_var, width=20).pack(side='left', padx=(6, 14))
        ttk.Label(lookup_line, text='Tipo de consulta').pack(side='left')
        ttk.Entry(lookup_line, textvariable=self.query_var, width=20).pack(side='left', padx=6)
        ttk.Button(lookup_line, text='Confirmar esta linha', command=self.confirm_lookup).pack(side='right')
        ttk.Label(self.lookup_editor, textvariable=self.warning_var, foreground='#83551c', wraplength=930).pack(anchor='w', pady=(5, 0))
        self.footer = ttk.Frame(body, padding=(0, 16, 0, 0))
        self.footer.pack(fill='x')
        ttk.Label(self.footer, text='CSV com ponto e vírgula e UTF-8 com BOM.', style='Muted.TLabel').pack(side='left')
        self.report_button = ttk.Button(self.footer, text='Conferência', command=self.open_report, state='disabled')
        self.report_button.pack(side='right', padx=(8, 0))
        self.export_button = ttk.Button(self.footer, text='Exportar CSV', style='Primary.TButton', command=self.export, state='disabled')
        self.export_button.pack(side='right')

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10), background='#f5f7f9', foreground='#203447')
        style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        style.configure('Muted.TLabel', foreground='#617382', font=('Segoe UI', 9))
        style.configure('TButton', padding=(12, 7))
        style.configure('Primary.TButton', background='#165b77', foreground='white')
        style.map('Primary.TButton', background=[('disabled', '#d8e0e5'), ('active', '#124d65')], foreground=[('disabled', '#72828c')])
        style.configure('Treeview', background='white', fieldbackground='white', rowheight=28)
        style.configure('Treeview.Heading', background='#e8eef2', font=('Segoe UI', 9, 'bold'), padding=(5, 7))
        style.map('Treeview', background=[('selected', '#275f7b')], foreground=[('selected', 'white')])

    def _attempt(self, operation):
        self.root.configure(cursor='watch')
        self.root.update_idletasks()
        try:
            while True:
                try:
                    operation()
                    return
                except SheetRequired as exc:
                    name = simpledialog.askstring('Escolher aba', Path(exc.path).name + '\n' + '\n'.join(exc.names), parent=self.root)
                    if name is None:
                        return
                    if name not in exc.names:
                        messagebox.showerror('Aba não encontrada', 'Digite um dos nomes exibidos.', parent=self.root)
                        continue
                    self.sheets[str(Path(exc.path).resolve())] = name
        except AppError as exc:
            self._error(exc)
        finally:
            self.root.configure(cursor='')

    def _error(self, error):
        logging.error('Erro: %s', error)
        messagebox.showerror('Não foi possível concluir', str(error), parent=self.root)

    def choose_file(self):
        path = filedialog.askopenfilename(title='Selecionar planilha semanal', filetypes=[('Excel', '*.xlsx')], parent=self.root)
        if path:
            self._attempt(lambda: self.load_file(path))

    def load_file(self, path):
        path = Path(path).resolve()
        reference = self.reference_source or (self.session if self.session and self.session.flow == 'atualizacao' else self.previous_update)
        ref_sheet = self.sheets.get(str(Path(reference).resolve())) if isinstance(reference, (str, Path)) else None
        candidate = processor.load_session(path, reference, self.sheets.get(str(path)), ref_sheet)
        if self.session and self.session.flow == 'atualizacao':
            self.previous_update = self.session
        self.session, self.last_result = candidate, None
        self.file_var.set(candidate.source.name)
        if candidate.flow == 'venda':
            self.reference_frame.pack(before=self.status_label, fill='x')
            self.reference_var.set(candidate.reference.label if candidate.reference else 'Selecione a atualização de placas para cruzar os dados.')
            self.reuse_button.state(['!disabled'] if self.previous_update else ['disabled'])
        else:
            self.reference_source = None
            self.previous_update = candidate
            self.reference_frame.pack_forget()
        choices = ['Prévia CSV', 'Pendências', 'Movimentação', 'Avisos'] + (['Cruzamento'] if candidate.flow == 'venda' else [])
        self.view_combo.configure(values=choices)
        self.view_var.set('Pendências' if validation.pending(candidate) else 'Prévia CSV')
        self.refresh()

    def choose_reference(self):
        path = filedialog.askopenfilename(title='Selecionar atualização de placas', filetypes=[('Excel ou CSV', '*.xlsx *.csv')], parent=self.root)
        if path:
            self._attempt(lambda: self.load_reference(path))

    def load_reference(self, reference):
        if not self.session or self.session.flow != 'venda':
            raise AppError('Abra primeiro a planilha de venda.')
        sheet = self.sheets.get(str(Path(reference).resolve())) if isinstance(reference, (str, Path)) else None
        processor.set_reference(self.session, reference, sheet)
        self.reference_source = reference
        self.reference_var.set(self.session.reference.label)
        self.last_result = None
        self.refresh()

    def reuse_reference(self):
        if self.previous_update:
            self._attempt(lambda: self.load_reference(self.previous_update))

    def choose_complement(self):
        if not self.session or not processor.missing_lookup_rows(self.session):
            return
        path = filedialog.askopenfilename(title='Consultar somente placas sem correspondência', filetypes=[('Excel ou CSV', '*.xlsx *.csv')], parent=self.root)
        if path:
            self._attempt(lambda: self.load_complement(path))

    def load_complement(self, path):
        if not self.session:
            raise AppError('Abra primeiro a planilha de venda.')
        sheet = self.sheets.get(str(Path(path).resolve()))
        count = processor.add_supplemental_reference(self.session, path, sheet)
        self.last_result = None
        self.refresh()
        remaining = len(processor.missing_lookup_rows(self.session))
        self.status_var.set(f'{count} cruzamentos completados nesta consulta. {remaining} placas continuam sem correspondência.')

    def _columns(self, columns):
        self.tree.configure(columns=[name for name, width in columns])
        for name, width in columns:
            self.tree.heading(name, text=name)
            self.tree.column(name, width=width, minwidth=65, stretch=False)

    def _insert(self, values, action=None, tag=''):
        key = str(len(self.items))
        self.items[key] = action
        self.tree.insert('', 'end', iid=key, values=values, tags=(tag,) if tag else ())

    def refresh(self):
        if not self.session:
            return
        self.editor.pack_forget()
        self.lookup_editor.pack_forget()
        self.selected = None
        self.confirm_button.state(['disabled'])
        self.bulk_var.set(False)
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        self.items = {}
        blocked = validation.pending(self.session)
        label = 'Venda' if self.session.flow == 'venda' else 'Atualização de placas'
        self.status_var.set(f'{label}. {len(self.session.rows)} registros. {len(blocked)} pendências para revisar.')
        self.export_button.state(['disabled'] if blocked else ['!disabled'])
        self.report_button.state(['!disabled'] if self.last_result else ['disabled'])
        if processor.missing_lookup_rows(self.session):
            self.supplement_button.pack(before=self.reference_label, side='left', padx=(0, 8))
            self.reference_label.configure(wraplength=380)
        else:
            self.supplement_button.pack_forget()
            self.reference_label.configure(wraplength=590)
        view = self.view_var.get()
        if view == 'Pendências':
            self._columns([('Linha', 70), ('Campo', 160), ('Valor atual', 200), ('Revisar', 510)])
            for issue in blocked:
                action = ('reference',) if issue.column == 'referência' else ('lookup', issue.row) if issue.column == 'cruzamento' else ('cell', issue.row, issue.column)
                self._insert([issue.row or '', issue.column, issue.value or '(vazio)', issue.reason], action, 'pending')
            self.caption_var.set('Selecione uma pendência para corrigir.' if blocked else 'Nenhuma pendência de preenchimento.')
        elif view == 'Movimentação':
            changes = processor.movement_preview(self.session, None)
            self._columns([('Linha', 70), ('Placa', 130), ('Antes', 320), ('Depois', 250)])
            for item in changes[:50]:
                self._insert([item['linha'], item['placa'], item['antes'] or '(coluna adicionada)', item['depois']], tag='inclusion' if item['depois'] == 'Inclusao' else 'exclusion')
            self.caption_var.set(f'Primeiras {min(50, len(changes))} de {len(changes)} alterações.')
        elif view == 'Cruzamento':
            self._columns([('Linha', 70), ('Placa', 130), ('Resultado', 280), ('Situação', 170), ('Tipo de consulta', 170), ('Arquivo consultado', 290)])
            for row in self.session.rows:
                match = self.session.matches[row.number]
                self._insert([row.number, row.values['placa_veiculo'], match.status, row.values['veiculo_situacao'], row.values['tipo consulta'], match.source_label], ('lookup', row.number), 'pending' if match.needs_review else '')
            self.caption_var.set('Selecione uma linha para conferir o par de valores.')
        elif view == 'Avisos':
            alerts = validation.warnings(self.session)
            self._columns([('Origem', 100), ('Linha', 70), ('Campo', 150), ('Valor', 170), ('Aviso', 460)])
            for issue in alerts:
                self._insert(['Planilha', issue.row, issue.column, issue.value, issue.reason], ('cell', issue.row, issue.column))
            self.caption_var.set(f'{len(alerts)} placas fora dos formatos antigo e Mercosul.')
        else:
            self._columns([('Linha', 65)] + [(name, 200 if name in ('numero_chassis_veiculo', 'empresa') else 150) for name in COLUMNS])
            bad_rows = {issue.row for issue in blocked}
            for row in self.session.rows[:200]:
                self._insert([row.number] + [row.values[name] for name in COLUMNS], ('preview', row.number), 'pending' if row.number in bad_rows else '')
            self.caption_var.set(f'Primeiros {min(200, len(self.session.rows))} registros. Duplo clique para editar.')

    def select_item(self, event=None):
        self.selected = None
        self.confirm_button.state(['disabled'])
        self.editor.pack_forget()
        self.lookup_editor.pack_forget()
        selection = self.tree.selection()
        if not selection:
            return
        action = self.items.get(selection[0])
        if action and action[0] not in ('preview',):
            self._show_editor(action)

    def _show_editor(self, action):
        self.editor.pack_forget()
        self.lookup_editor.pack_forget()
        self.selected = action
        self.confirm_button.state(['disabled'])
        if action[0] == 'reference':
            self.root.after_idle(self.choose_reference)
        elif action[0] == 'lookup':
            number = action[1]
            row, match = self.session.row(number), self.session.matches[number]
            self.situation_var.set(row.values['veiculo_situacao'])
            self.query_var.set(row.values['tipo consulta'])
            choices = ['Informar manualmente'] + [f"Registro(s) {', '.join(map(str, c.lines))}: {c.situation or '(vazio)'} / {c.query or '(vazio)'}" for c in match.candidates]
            self.candidate_combo.configure(values=choices)
            self.candidate_var.set(f'Linha {number}: escolha uma correspondência ou preencha os dois campos')
            self.warning_var.set('\n'.join(issue.reason for c in match.candidates for issue in c.issues if issue.blocking))
            self.lookup_editor.pack(before=self.footer, fill='x')
        elif action[0] == 'cell':
            _, number, column = action
            if self.session.flow == 'venda' and column in JOIN_FIELDS:
                self._show_editor(('lookup', number))
                return
            if column == 'cnpj' or (self.session.flow == 'venda' and column == 'movimentação') or (self.session.flow == 'atualizacao' and column == 'uf_venda'):
                return
            self.edit_label_var.set(f'Linha {number} / {column}')
            self.value_var.set(self.session.row(number).values[column])
            self.bulk_var.set(False)
            if self.view_var.get() == 'Pendências' and any(issue.row == number and issue.column == column for issue in validation.pending(self.session)):
                self.confirm_button.state(['!disabled'])
            self.editor.pack(before=self.footer, fill='x')

    def edit_preview(self, event):
        if self.view_var.get() != 'Prévia CSV':
            return
        item, column = self.tree.identify_row(event.y), self.tree.identify_column(event.x)
        if not item or not column:
            return
        index = int(column[1:]) - 2
        if 0 <= index < len(COLUMNS):
            self._show_editor(('cell', self.items[item][1], COLUMNS[index]))

    def apply_edit(self):
        if not self.selected or self.selected[0] != 'cell':
            return
        try:
            processor.edit_cell(self.session, self.selected[1], self.selected[2], self.value_var.get(), self.bulk_var.get())
            self.last_result = None
            self.refresh()
        except AppError as exc:
            self._error(exc)

    def confirm_current(self):
        if not self.selected or self.selected[0] != 'cell':
            return
        _, number, column = self.selected
        try:
            if self.value_var.get() != self.session.row(number).values[column]:
                raise AppError('Use Aplicar para salvar o valor digitado. Confirmar como está mantém o valor atual da planilha.')
            processor.confirm_pending(self.session, number, column)
            self.last_result = None
            self.refresh()
        except AppError as exc:
            self._error(exc)

    def choose_candidate(self, event=None):
        if not self.selected or self.selected[0] != 'lookup':
            return
        index = self.candidate_combo.current() - 1
        if index >= 0:
            candidate = self.session.matches[self.selected[1]].candidates[index]
            self.situation_var.set(candidate.situation)
            self.query_var.set(candidate.query)

    def confirm_lookup(self):
        if not self.selected or self.selected[0] != 'lookup':
            return
        try:
            processor.resolve_lookup(self.session, self.selected[1], self.situation_var.get(), self.query_var.get())
            self.last_result = None
            self.refresh()
        except AppError as exc:
            self._error(exc)

    def export(self):
        if not self.session:
            return
        path = filedialog.asksaveasfilename(title='Exportar CSV', initialdir=str(self.session.source.parent), initialfile=self.session.source.stem + '.csv', defaultextension='.csv', filetypes=[('CSV', '*.csv')], parent=self.root)
        if path:
            try:
                self.last_result = export_csv(self.session, path)
                self.refresh()
                self.status_var.set('CSV gerado: ' + str(self.last_result.csv))
            except AppError as exc:
                self._error(exc)

    def open_report(self):
        if self.last_result:
            webbrowser.open(self.last_result.report.as_uri())


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0
