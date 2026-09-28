# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

**Vehicula** — coleção de ferramentas web (pt-BR) para tratar placas veiculares, AITs e planilhas de dados veiculares. (O projeto se chamava CheckMultas; o repositório, a URL do GitHub Pages e as chaves `cm-*` do `localStorage` mantêm o nome antigo — ver "Workflow".) **Tudo vive em um único arquivo: `index.html`** (~2200 linhas — HTML, CSS e JS inline). Sem build, sem npm, sem framework. Única dependência externa: SheetJS 0.18.5 via CDN (`XLSX.*`), usado para ler/escrever `.xlsx`.

Publicado em GitHub Pages a partir de `main`: https://leandrojs82.github.io/checkmultas-tools/

## Executar e testar

```bash
# abrir direto no navegador
start index.html

# ou servir (config em .claude/launch.json usa a mesma porta)
python -m http.server 8765
```

Não há suíte de testes nem linter. Verificação é manual no navegador: abrir a ferramenta afetada, colar entrada de exemplo, conferir saída e o console. Teste sempre nos **dois temas** (botão na topbar) e na largura mobile (≤640px).

## Arquitetura de `index.html`

O arquivo é dividido em blocos delimitados por comentários de faixa (`/* === ... === */` e `APP N — NOME`). Ao navegar, procure por esses cabeçalhos em vez de ler o arquivo inteiro.

**CSS** (`<style>`, linhas ~11–580), nesta ordem — respeite a ordem ao adicionar regras:
`TOKENS` (custom properties em `:root` + override em `[data-theme="light"]`) → `RESET` → `SHELL` (sidebar, topbar, home) → `COMPONENTES` (vocabulário reutilizável: `.panel`, `.btn`, `.field`, `.tag`, `.table`, `.drop`, `.status`) → `TELAS` (refinamentos por ferramenta, escopados em `#page-<id>`) → `RESPONSIVO`.

Nunca use cor literal em regra nova — sempre `var(--bg-surface)`, `var(--text-2)`, `var(--accent)`, `var(--err)` etc., senão o tema claro quebra.

**Ícones**: sprite SVG `<symbol id="ic-*">` (linha ~584) consumido com `<svg><use href="#ic-nome"/></svg>`. Adicione novos símbolos ao sprite, não SVG inline solto.

**Shell / SPA**: cada ferramenta é um `<div id="page-<id>" class="app-page">`; `showPage(id, navBtn)` troca a classe `.active`, atualiza o `.nav-item` correspondente (casado por `data-id`) e o título da topbar a partir do **mapa `titles` dentro de `showPage`**. A home tem um `.home-card` por ferramenta com `data-id` e `data-group`.

**Adicionar uma ferramenta nova** exige tocar cinco pontos com o mesmo `<id>`:
1. `.nav-item` na `.nav-group` certa (`placas` ou `dados`) com `data-id` e `onclick="showPage('<id>',this)"`;
2. `.home-card` no `#allGrid` com `data-id`/`data-group` e `onclick="showPageByName('<id>')"`;
3. bloco `<div id="page-<id>" class="app-page">` no HTML;
4. entrada no mapa `titles` de `showPage` (título + subtítulo);
5. bloco JS próprio no fim do `<script>`.

Busca (`Ctrl+K`), favoritos (`localStorage` `cm-favs`) e tema (`localStorage` `cm-theme`) funcionam automaticamente por derivarem do DOM dos cards/nav-items.

**JS por ferramenta**: dois padrões coexistem — IIFE `(function(){...})()` com funções locais (conversor, jsoncsv, frota, consolidador) e funções globais com prefixo (`val_*` no validador, `sqlin_*`, `sqlait_*`). Em ferramenta existente siga o padrão dela; em ferramenta nova prefira IIFE, expondo no `window` só o que o `onclick` do HTML precisa. **Todos os IDs de elemento levam o prefixo da ferramenta** (`conv-`, `val-`, `sqlin-`, `cons-`, `frota-`) — mantenha isso, já que o namespace do DOM é único.

Feedback ao usuário é centralizado: `mostrarToast(msg, 'ok'|'err')` e `toastCopiado()`. Não crie mecanismo de notificação paralelo.

## Convenções de domínio (não invente)

- **Conversão Mercosul**: só a posição 5 muda, via tabela Denatran `0→A … 9→J` (`DIGIT_TO_LETTER`/`LETTER_TO_DIGIT`).
- **Validação**: `FORMATO_ANTIGO = /^[A-Z]{3}[0-9]{4}$/`, `FORMATO_MERCOSUL_V = /^[A-Z]{3}[0-9][A-Z][0-9]{2}$/`; o diagnóstico por posição vem do `GABARITO` (`L`/`N` por posição).
- **SQL `IN`**: sempre com aspas simples e escape `'` → `''`; alvo é PostgreSQL.
- **CSV**: delimitador `;` e BOM UTF-8 (para o Excel pt-BR abrir certo).
- **Cabeçalhos de planilha**: localizados por nome normalizado (`normalizeHeader`: NFD sem acento, upper, espaços colapsados) e mapeados por `COLUMN_MAP`; a ordem de saída é fixa em `OUTPUT_ORDER`.
- **RENAVAM**: só dígitos, `padStart(11,'0')`.
- **Leitura de CSV/TXT**: separador detectado na 1ª linha (`;`, `,` ou tab); a leitura tenta UTF-8 e refaz em Windows-1252 quando aparece caractere inválido — preserva acento de arquivo legado.

## Idioma

Toda a UI, comentários e mensagens estão em **português do Brasil**. Escreva novo código e texto no mesmo idioma.

## Workflow

- **Não commitar.** Entregue as mudanças no working tree; o usuário commita.
- A marca visível é **Vehicula** (title, logo da sidebar, banner da home, README). Nomes internos herdados do nome antigo — repositório `checkmultas-tools`, URL do Pages, chaves `cm-theme`/`cm-favs`, id `cm-toast` — **não** foram renomeados: mudar as chaves do `localStorage` apagaria tema e favoritos já salvos dos usuários.
- Ao mudar comportamento visível ou adicionar ferramenta, atualize o `README.md` (ele documenta cada ferramenta, a interface e as dependências).
- `docs/superpowers/` guarda specs e planos de redesign passados; `design_handoff_melhorias_checkmultas/` traz um handoff de UX com mockups de referência — os mockups usam cores fixas de exemplo, o código real deve usar os tokens `var(--*)`.
