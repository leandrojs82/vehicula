# Handoff: Sugestões de Melhorias — CheckMultas Ferramentas

## Overview
Conjunto de 7 modelos de melhoria de UX/UI para o site CheckMultas · Ferramentas (https://leandrojs82.github.io/checkmultas-tools/). Cada modelo é um padrão isolado a ser aplicado no `index.html` existente do projeto, não uma tela nova.

## About the Design Files
O arquivo `Sugestões de Melhorias.dc.html` é uma **referência de design em HTML** — mostra a aparência e o comportamento pretendido de cada melhoria, isoladamente, fora do contexto real do app. A tarefa é **recriar esses padrões dentro do `index.html` já existente do CheckMultas**, seguindo a stack e os padrões do projeto (HTML/CSS/JS vanilla, sem framework, tema via CSS custom properties, ver seção de tokens abaixo). Não copiar o HTML do arquivo de referência diretamente — ele usa cores fixas de exemplo, o projeto real usa `var(--*)`.

## Fidelity
**Alta fidelidade** para cor, raio de borda e tipografia (usa a paleta real do projeto). **Baixa fidelidade** para o conteúdo funcional exato — os textos/dados nos mockups (ex.: "ABC1234", "posição 5") são exemplos ilustrativos; a lógica real (regex de validação, geração do tooltip, etc.) deve ser implementada pelo desenvolvedor.

## Modelos

### 1. Navegação agrupada
- **Problema:** sidebar lista os 7 apps em sequência única, sem agrupamento.
- **Solução:** inserir labels de seção maiúsculas (`Placas`, `Dados`) acima dos grupos de `.nav-item` correspondentes, e uma seção `Favoritos` fixa no topo do sidebar (não só na home) com os itens marcados.
- **Estilo do label:** `font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--text-3);`

### 2. Nomenclatura consistente de botões
- **Problema:** botões de exportação usam verbos diferentes ("Baixar CSV", "Copiar placas SQL IN", "Baixar arquivo").
- **Solução:** padronizar para `Exportar <Nome>` em todos os botões de download/cópia de resultado. Aplicar em `.btn.btn-primary` de cada app.

### 3. Placeholder com exemplo real
- **Problema:** placeholder dos textareas só instrui ("Cole suas placas e clique em Converter"), sem mostrar formato esperado.
- **Solução:** trocar `placeholder` por texto de exemplo real (ex.: `ABC1234\nABC1D23`), com uma linha de dica abaixo em `.input-hint` explicando o formato aceito.

### 4. Diagnóstico inline por posição (Validador de Placas)
- **Problema:** erro de validação só aparece em resumo geral, não indica a posição errada na própria placa.
- **Solução:** ao renderizar cada linha validada, envolver o caractere na posição incorreta em `<span>` com `background:rgba(248,113,171,.25); color:var(--err); border-radius:3px;` e adicionar rótulo lateral `posição N` em `var(--err)`.

### 5. Unificar N arquivos (não fixo em 3)
- **Problema:** app "Unificar Arquivo" aceita exatamente 3 planilhas fixas.
- **Solução:** reusar o padrão de upload múltiplo já implementado no "Verificador de Colunas" (lista dinâmica de arquivos com botão `+ Adicionar`), em vez dos 3 slots fixos (Arquivo A/B/C).

### 6. Explicação da sugestão de VARCHAR
- **Problema:** a coluna "Sugestão SQL" no Verificador de Colunas não explica de onde vem o número.
- **Solução:** adicionar ícone `?` no cabeçalho da coluna com atributo `title="Maior comprimento encontrado entre todos os arquivos."` (tooltip nativo) ou tooltip customizado se o projeto já tiver um componente de tooltip.

### 7. Confirmação visual ao copiar
- **Problema:** botões de "Copiar" (ex.: "Copiar placas SQL IN") não dão feedback de que a ação funcionou.
- **Solução:** ao disparar `navigator.clipboard.writeText`, mostrar um toast temporário (2–3s) no canto inferior direito: fundo `rgba(74,222,128,.1)`, borda `1px solid #2f5b3f`, texto `var(--ok)`, ícone `✓` + "Copiado para a área de transferência". Reusar para todos os botões de cópia do projeto (prefixar função `mostrarToast()` sem conflito com os demais apps, conforme padrão de nomenclatura do projeto).

## Design Tokens (já existentes no projeto — reusar, não recriar)
```
--bg-app       fundo da página
--bg-surface   cards e painéis
--bg-elevated  inputs, hover
--text-1       texto principal
--text-2       texto secundário
--text-3       texto mudo/placeholder
--border-s     bordas sutis
--border-m     bordas médias
--accent       laranja #ff5b1f
--ok           verde #4ade80
--err          vermelho #f87171
```

## Assets
Nenhum asset externo — apenas emojis/ícones de texto simples, iguais aos já usados no sidebar do projeto (`🔧` etc.).

## Files
- `Sugestões de Melhorias.dc.html` — referência visual dos 7 modelos (arquivo de design, não é código de produção).
- `screenshot-modelos.png` — captura de tela dos 7 modelos, para quem não puder abrir o `.dc.html`.
