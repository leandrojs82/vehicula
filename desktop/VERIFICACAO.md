# Verificação da entrega Vehicula

Data de referência 10/11/2026.

## Ambiente

Windows de 64 bits deste computador, Python 3.13.15, pywebview 6.2.1, pythonnet 3.2.1, PyInstaller 6.22.3 e WebView2 Runtime 157.0.4341.42. As versões completas das dependências estão em requirements.txt.

## Resultados aprovados

- 11 testes da toolbar. Preferências válidas/inválidas, recuperação de configuração, gravação sem dados de planilhas, despacho de ferramentas, controle de cliques repetidos, nova abertura após saída, foco recusado pelo Windows, posição ao minimizar, preparação sem WebView2 e expansão com callback de fechamento concorrente.
- 46 testes da entrada modular atual do PreparaFrota. Processamento, datas Excel, revisão/confirmação, referências complementares, fluxo de venda e controles da interface.
- 6 testes do exportador PBIX. XLSX único/separado, CSV com BOM, valores de texto, nomes de arquivos, divisão em abas, falha parcial e preservação de exportações anteriores.
- Ensaio real no WebView2 das sete páginas HTML. Conversão ABC1234 para ABC1C34, placas válidas/inválidas, JSON com acentos, SQL IN e AIT, aspas e entradas com marcação HTML.
- Cinco arquivos gerados no ensaio do painel e lidos novamente para conferir conteúdo. CSV de JSON, XLSX do validador, CSV do Unificar Arquivo e CSV/XLSX do Verificador de Colunas.
- Planilha XLSX criada para o ensaio, adicionada pelo evento de arraste e processada no Unificar Arquivo. Conferidos os oito campos de saída e o RENAVAM 00000000123.
- Arquivos CSV/TXT compatíveis e divergentes no Verificador de Colunas. Conferidos importação, relatório e exportação.
- Recolher e expandir preservam o JSON digitado. Tema e favoritos são recuperados de preferências nativas em uma origem local própria de cada execução.
- Repetição dos ensaios HTML após recarregar a página com bloqueio de recursos HTTP externos no perfil temporário de teste. Os recursos necessários foram carregados localmente.
- O diálogo nativo de salvamento CSV foi aberto pela interface e cancelado, retornando ao painel. Para conferir automaticamente vários downloads seguidos, o perfil temporário de teste permitiu MultipleAutomaticDownloads e escolheu destinos de teste. A entrega utiliza os comandos acionados pelo usuário e o diálogo normal de salvamento.
- Abertura das duas ferramentas nativas, verificação de janela pertencente ao processo iniciado e reutilização da mesma instância no ensaio de integração.
- Primeira distribuição executada a partir de uma pasta com espaços e acentos. Barra, PreparaFrota e PBIX abriram pelo executável. Após fechar a barra, as duas ferramentas continuaram abertas e foram encerradas por seus controles.

## Power BI com dados reais

A amostra pública Adventure Works DW 2020.pbix, do [repositório PBIXRay](https://github.com/Hugoberry/pbixray), foi lida pelo módulo integrado no ambiente Python de empacotamento. Foram encontradas nove tabelas. Currency, com 105 linhas, e Product foram exportadas como XLSX único, XLSX separado e CSV. Foram conferidos nomes, abas, colunas e quantidade de registros.

## Correções da revisão

A revisão independente identificou e foram corrigidos dois problemas na integração. Entradas inválidas de placas podiam ser interpretadas como marcação HTML. A expansão também mantinha uma trava de preferências durante chamadas de janela, podendo bloquear um callback de fechamento. Os testes de regressão falharam antes e passaram depois das correções.

Também foram ajustadas a prévia SQL com aspas escapadas, a informação de foco quando recusado pelo Windows, a posição ao fechar minimizado e a identificação da ferramenta na mensagem de falha. O serviço local passou a usar uma porta própria por execução, evitando carregar recursos de uma outra instância.

## Testes herdados antigos

Os testes test_preparafrota.py, test_venda.py e test_visual.py se referem às versões monolíticas anteriores. A descoberta integral de 81 testes na pasta original também foi executada e apresentou 20 falhas e 16 erros, principalmente pela referência às funções antigas process/prepare_session e à interface anterior. A entrada atual PreparaFrota.pyw utiliza o pacote modular 5.2. As quatro suítes dessa entrada, totalizando 46 testes, passaram. Esse conjunto antigo permanece como referência no código-fonte.

## Alcance dos ensaios

A inspeção visual foi feita na configuração de tela deste computador. Escalas de 125%/150%, monitores mistos e outros computadores requerem verificação adicional. A ausência do WebView2 foi exercitada por simulação da detecção, sem remover o componente instalado no Windows. A instalação do WebView2 depende das permissões do computador de destino.

## Reproduzir testes atuais

Com o ambiente instalado conforme README.md, execute o teste da toolbar e o exportador PBIX.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m unittest discover -s tools/pbix -v
```

Para a entrada modular atual do PreparaFrota, execute as quatro suítes abaixo a partir da pasta do projeto.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tools/preparafrota/tests -p test_processing.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tools/preparafrota/tests -p test_excel_serial_dates.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tools/preparafrota/tests -p test_review_actions.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tools/preparafrota/tests -p test_ui.py -v
```
