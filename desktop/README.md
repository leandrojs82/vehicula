# Vehicula

Toolbar para Windows com ferramentas locais para placas, planilhas e dados veiculares.

## Abrir

1. Extraia toda a pasta do ZIP.
2. Abra `Vehicula.exe` na pasta extraída. A subpasta `_internal` acompanha o executável.
3. Use **Ferramentas** para expandir a área de trabalho e escolher uma das sete ferramentas.
4. Use **Recolher** para retornar à barra, preservando os dados da sessão HTML.

**PreparaFrota** e **PBIX → Excel** abrem suas próprias janelas. Clicar novamente no botão restaura a janela da ferramenta. Os aplicativos já abertos continuam executando quando a barra é fechada.

O botão de alfinete ativa **Manter no topo**. Em **Preferências**, escolha tema claro, escuro ou acompanhar o Windows. Marque ferramentas favoritas pelo coração na tela inicial.

## Preparação do Windows

O pacote inclui Python e suas bibliotecas. A janela HTML utiliza o **Microsoft Edge WebView2 Runtime**. Quando o componente estiver ausente, a abertura informa a preparação necessária.

Instaladores oficiais, incluindo opção offline, em [Microsoft WebView2](https://developer.microsoft.com/microsoft-edge/webview2/). A instalação pode depender das permissões do computador. Os testes desta entrega utilizam Windows de 64 bits com WebView2 instalado.

## Ferramentas

- Conversor de Placas.
- Validador de Placas com exportação Excel.
- JSON para CSV.
- SQL IN.
- SQL IN AIT.
- Unificar Arquivo.
- Verificador de Colunas.
- PreparaFrota, com revisão da atualização e da venda.
- PBIX para Excel, com XLSX único, XLSX por tabela e CSV.

Os recursos de Excel e as fontes acompanham o pacote. O processamento ocorre no computador. As ferramentas mantêm seus próprios formatos de entrada e saída. O JSON para CSV e o Verificador de Colunas utilizam vírgula no CSV do projeto original. O Unificar Arquivo, o PreparaFrota e a exportação CSV de PBIX utilizam ponto e vírgula.

No PBIX, a extração depende de dados importados e salvos no relatório. As tabelas exclusivamente DirectQuery e relatórios ligados a modelos remotos dependem de sua fonte externa.

## Sessão e preferências

Recolher a barra mantém a sessão HTML carregada. Fechar o Vehicula encerra essa sessão. Exporte os resultados que deseja guardar antes de fechar.

Tema, favoritos, fixação e posição ficam em `%LOCALAPPDATA%/Vehicula/settings.json`. O perfil do WebView2 fica na mesma pasta. O registro de erros fica em `errors.log` e pode ajudar no diagnóstico de uma falha de abertura.

## Código-fonte

Use Python 3.13 de 64 bits para reproduzir o ambiente desta entrega.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

O arquivo `Vehicula.spec` gera o executável com PyInstaller. A pasta `tools` contém as cópias integradas dos dois apps. `web` contém o HTML e os recursos locais. `toolbar` contém a integração com o Windows.

O registro `VERIFICACAO.md` detalha os ensaios realizados, a amostra PBIX e as condições ainda não exercitadas. As licenças das bibliotecas e das fontes acompanham o código e a distribuição.
