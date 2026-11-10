# ⚡ Vehicula · Ferramentas

Conjunto de utilitários web para processamento de **placas veiculares**, infrações e dados veiculares do Vehicula. Todas as ferramentas funcionam **100% no navegador** — sem servidor, sem instalação, sem dependências externas além do SheetJS (carregado via CDN).

---

## 🚀 Como usar

Basta abrir o arquivo `index.html` diretamente no navegador:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/checkmultas-tools.git

# Abra o arquivo no navegador
open index.html
# ou simplesmente dê duplo clique no arquivo
```

Nenhum `npm install`, `build` ou servidor local é necessário.

---

## 🛠️ Ferramentas incluídas

### 🔄 Conversor de Placas — Mercosul ↔ Tradicional

Converte placas entre o formato antigo (`ABC-1234`) e o formato Mercosul (`ABC1D23`) utilizando a tabela oficial do Denatran.

**Funcionalidades:**
- Detecção automática do formato de entrada
- Conversão em lote (cole várias placas de uma vez)
- Suporta entrada suja: `('HKT0416','RGA2D75','RGA3A02')`, separadas por vírgula, espaço ou linha
- Exportação SQL `IN (...)` para originais, convertidas ou ambas
- Cópia para área de transferência com um clique

**Tabela de conversão Denatran (posição 5):**

| Dígito | Letra Mercosul |
|--------|---------------|
| 0      | A             |
| 1      | B             |
| 2      | C             |
| 3      | D             |
| 4      | E             |
| 5      | F             |
| 6      | G             |
| 7      | H             |
| 8      | I             |
| 9      | J             |

---

### ✅ Validador de Placas em Lote

Valida lotes de placas nos dois formatos com diagnóstico detalhado por posição.

**Funcionalidades:**
- Suporta formato tradicional (`AAA0000`) e Mercosul (`AAA0A00`)
- Diagnóstico por posição: indica exatamente qual caractere está errado e o que era esperado
- Separa visualmente placas válidas e inválidas
- Preserva o número da linha original para rastreabilidade
- Exporta válidas e inválidas em arquivos `.xlsx` separados

---

### 📋 Conversor JSON → CSV

Converte um ou múltiplos objetos JSON em CSV compatível com Excel.

**Funcionalidades:**
- Suporta três formatos de entrada: objeto único, array `[{...}]` ou múltiplos objetos colados sequencialmente
- CSV gerado com BOM UTF-8 para abrir corretamente no Excel
- Delimitador ponto e vírgula (`;`) no padrão brasileiro
- Preview dos dados em tabela antes do download
- Extração automática das placas (`placa` / `Placa` / `PLACA`) com geração de SQL `IN (...)`

---

### 🔎 Conversor SQL IN

Transforma uma lista de valores (um por linha) em uma cláusula `IN (...)` pronta para colar em uma query.

**Funcionalidades:**
- Ignora linhas em branco e espaços nas pontas
- Escapa aspas simples (`'` → `''`)
- Saída com destaque de sintaxe e contagem de itens
- Cópia para área de transferência com um clique · `Ctrl + Enter` converte

---

### 📄 SQL IN AIT

Versão dedicada do Conversor SQL IN para listas de **AITs**: cole uma AIT por linha e receba a cláusula `IN ('...', '...')` com aspas simples, pronta para a query.

**Funcionalidades:**
- Ignora linhas em branco e espaços nas pontas
- Escapa aspas simples (`'` → `''`)
- Saída com destaque de sintaxe e contagem de AITs
- Cópia para área de transferência com um clique · `Ctrl + Enter` converte

---

### 🚛 Unificar Arquivo

Une **uma ou mais planilhas Excel** de restrição/localização de frota em um único CSV padronizado.

**Funcionalidades:**
- Upload por clique ou arrastar e soltar, com lista dinâmica de arquivos (adicione quantos precisar)
- Colunas localizadas pelo **nome do cabeçalho**, tolerante a acento, maiúsculas e espaços
- RENAVAM normalizado para 11 dígitos (apenas números, com zeros à esquerda)
- Coluna `data_atualizacao` preenchida com a data do processamento
- Pipeline visual com progresso por etapa (leitura → unificação → CSV)

**Ordem do cabeçalho de saída:**

`placa` · `renavam` · `chassi` · `uf` · `status_localiza` · `data_cadastro_localiza` · `frota` · `data_atualizacao`

---

### 🧩 Verificador de Colunas

Consolida múltiplos arquivos `.txt`, `.csv` e `.xlsx` em um único conjunto, verificando se todos têm a mesma estrutura de colunas.

**Funcionalidades:**
- Seleção de vários arquivos de uma vez; separador de CSV/TXT detectado automaticamente (`;`, `,` ou tab)
- Relatório por arquivo com número de linhas e colunas — arquivos com quantidade de colunas divergente são sinalizados
- Tabela de **tamanho máximo por coluna** com sugestão de `VARCHAR(n)` para dimensionar campos no banco
- Remoção de arquivos individuais com recálculo automático
- Exportação do consolidado em CSV ou Excel (`.xlsx`), com nome de arquivo opcional

---

## 🎨 Interface

- Menu lateral com grupos recolhíveis (**Placas** e **Dados**) e botão para ocultar/exibir
- **Busca** de ferramentas na barra superior (`Ctrl + K`), com filtro em tempo real que ignora acentos
- **Favoritos**: marque uma ferramenta com ♡ para exibi-la no topo da página inicial e no menu (persistido via `localStorage`)
- Tema **dark/light** com alternância na barra superior e persistência via `localStorage`
- Detecção automática da preferência do sistema operacional (`prefers-color-scheme`)
- Página inicial com cards de navegação — cada ferramenta abre na mesma página sem recarregar
- Layout responsivo para desktop e mobile

---

## 📦 Dependências

| Biblioteca | Versão  | Uso                                      | Carregamento |
|------------|---------|------------------------------------------|--------------|
| [SheetJS](https://sheetjs.com/) | 0.18.5 | Leitura e escrita de arquivos `.xlsx` | CDN (cdnjs) |

Nenhuma outra dependência. HTML, CSS e JavaScript puros.

---

## 🗂️ Estrutura do projeto

```
checkmultas-tools/
├── index.html   # Aplicação completa em arquivo único
└── README.md
```

Todo o CSS e JavaScript está inline no HTML para facilitar a distribuição — basta enviar o arquivo.

---

## 🔧 Contexto técnico

Estas ferramentas foram desenvolvidas para suportar operações internas com dados veiculares no padrão brasileiro:

- **Placas** nos formatos Denatran/tradicional e Mercosul
- **Dados** no padrão dos sistemas Denatran / RENAVAM
- **Exportação SQL** compatível com PostgreSQL (`IN (...)` com escape de aspas simples)
- **CSV** compatível com o formato de importação do sistema Vehicula
- **Leitura de CSV** com detecção de codificação: tenta UTF-8 e refaz em Windows-1252 quando encontra caracteres inválidos, preservando acentos de arquivos legados

---

## 📝 Licença

Uso interno. Sem licença de distribuição pública.
