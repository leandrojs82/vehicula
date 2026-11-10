# PreparaFrota 5.2

## Confirmar uma pendência como correta

Em **Pendências**, selecione um campo e clique em **Confirmar como está** para aceitar o valor atual sem alterá-lo. A pendência sai da lista, e a decisão fica registrada no relatório, com linha, campo, valor mantido e motivo original.

A confirmação vale somente para a célula selecionada, inclusive quando o valor está vazio ou a data não pôde ser convertida. O CSV preservará esse valor exatamente como foi confirmado. Se você digitou um valor diferente na caixa, use **Aplicar** para gravá-lo. Editar uma célula confirmada invalida a confirmação anterior.

Pendências de referência e cruzamento não são liberadas por esse botão: selecione um arquivo ou confirme situação e tipo de consulta juntos. Se optar por confirmar uma placa vazia como correta, ainda será necessário informar e confirmar manualmente os dois valores dessa linha em **Cruzamento**, após selecionar a referência principal. Essas decisões ficam identificadas no relatório.

## Avisos somente para formato de placa

São aceitas placas antigas como `ABC1234` ou `ABC-1234` e Mercosul como `ABC1D23` ou `ABC-1D23`. Maiúsculas e minúsculas e espaços nas extremidades são desconsiderados na validação, sem mudar o texto exportado. Espaços internos e outros caracteres fora dos formatos são apontados.

**Avisos** mostra apenas placas preenchidas que não correspondam a nenhum desses formatos. Observações de duplicatas, frequência, comprimento predominante, espaços em outros campos e demais avisos não críticos foram desativadas. A verificação é de formato, sem consultar cadastro de veículos. Campos vazios continuam sendo tratados em Pendências até correção ou confirmação explícita.

## Consultar outro arquivo para completar cruzamentos

O botão **Consultar faltantes…** aparece somente no fluxo de venda, depois de escolher a referência principal, e somente enquanto houver placas preenchidas sem correspondência.

Selecione outro XLSX ou CSV contendo placa_veiculo, veiculo_situacao e Tipo consulta. Escolha a aba se necessário. A consulta complementar atua apenas nas linhas ainda sem correspondência e mantém todos os cruzamentos já encontrados ou confirmados manualmente. Não altera a ordem nem a quantidade de linhas da venda.

Se ainda houver placas sem resultado, pode consultar outro arquivo. Dados conflitantes ou incompletos encontrados exigem escolha manual do par, sem seleção automática da primeira linha. O arquivo consultado aparece em **Cruzamento** e no relatório. Trocar a referência principal remove as consultas complementares anteriores, para iniciar uma nova revisão.

## Conversão automática de datas numéricas

Valores como `46134.70949074074` são reconhecidos como números de série do Excel nas colunas de data. No calendário padrão, esse exemplo é convertido para `22/04/2026`. A parte decimal, que representa o horário, é removida sem arredondar a data para o dia seguinte.

A conversão aceita números e textos numéricos, com ponto ou vírgula decimal, e respeita o sistema de datas 1900 ou 1904 indicado no próprio arquivo. Também vale ao corrigir uma data manualmente na tela. Apenas a coluna de data é convertida; identificadores e outros campos são preservados.

Valores não convertíveis, fora do intervalo de datas do Excel ou correspondentes à data inexistente 29/02/1900 continuam visíveis em Pendências, com o motivo, e bloqueiam a exportação até a revisão. O valor original não é apagado nem substituído por uma data inventada. As conversões aparecem no relatório de ajustes.

Aplicativo local para preparar as planilhas semanais de atualização de placas e de UF Venda. Esta versão foi reescrita como um pacote modular, com uma única tabela de revisão e sem seleção manual do tipo de processamento.

## Instalação e abertura

Requer Python 3.10 ou superior, com Tkinter. Extraia todo o ZIP em uma pasta nova e instale as dependências nessa pasta:

```powershell
py -3 -m pip install -r requirements.txt
```

Abra **PreparaFrota.pyw** com dois cliques. Se necessário, use Abrir com > Python, ou execute `py -3 PreparaFrota.pyw`. O aplicativo é distribuído como código Python, não como um EXE independente de instalação.

## Uso semanal

1. Clique em **Abrir planilha** e escolha o Excel. O formato é reconhecido pelos cabeçalhos. Se houver mais de uma aba, escolha o nome exato da aba desejada.
2. Para uma venda, selecione a atualização de placas em **Referência…**. Também pode usar seu CSV já gerado ou a atualização revisada anteriormente na mesma sessão. A referência não é o arquivo de venda.
3. Use **Exibir** para alternar entre Pendências, Prévia CSV, Movimentação, Cruzamento e Avisos. Existe somente uma tabela na tela.
4. Selecione uma pendência para corrigir ou confirmar como está. No cruzamento, consulte as placas faltantes em outro arquivo ou escolha/informe situação e tipo de consulta e confirme a linha.
5. Quando não houver pendências, clique em **Exportar CSV**. O relatório de conferência fica na mesma pasta e pode ser aberto por **Conferência**.

A leitura da venda pode começar antes da escolha da referência; a planilha fica carregada aguardando essa seleção. Carregar uma nova atualização passa a usá-la como referência para a próxima venda, evitando a reutilização silenciosa de uma semana anterior. Se quiser outra referência, selecione-a explicitamente.

Os ajustes permanecem em memória até fechar o programa. Exporte o resultado antes de sair. Os arquivos de origem nunca são alterados. A data do nome do arquivo não é usada para substituir as datas dos registros.

## Regras da atualização de placas

- Remove Produto completamente do processamento final, inclusive da validação de campos vazios.
- Incluir Consulta e Manter Consulta tornam-se Inclusao. Desativar torna-se Exclusao. Valores desconhecidos exigem revisão antes da exportação.
- Acrescenta cnpj = 10215988000240 e uf_venda vazia.
- Padroniza DATA BASE em DD/MM/AAAA.
- Mantém textos, ordem dos registros e repetições, sem excluir linhas automaticamente.

Os campos de entrada são placa_veiculo, numero_chassis_veiculo, numero_renavam, Empresa, UF_Placa, veiculo_situacao, Tipo consulta, Movimentação e DATA BASE. Produto é opcional e descartado. Cabeçalhos são reconhecidos sem diferenciar maiúsculas e minúsculas; espaços nas extremidades do cabeçalho são desconsiderados. Isso não remove espaços dos valores.

## Regras da venda

O Excel deve conter placa_veiculo, numero_chassis_veiculo, numero_renavam, Empresa, UF Origem, Data Venda e UF Venda.

- Os quatro primeiros campos vêm da venda.
- UF Origem passa para uf_placa, na quinta posição.
- veiculo_situacao e tipo consulta vêm da **atualização de placas**, cruzados pela placa.
- movimentação é Inclusao em todas as linhas.
- Data Venda passa para data base em DD/MM/AAAA, sem o horário.
- cnpj é 10215988000240.
- UF Venda passa para uf_venda e precisa estar preenchida.

A chave de busca ignora maiúsculas, espaços e hífens. A placa que sai no CSV mantém seu texto original. Repetições na referência com o mesmo par de situação e tipo de consulta são agrupadas para consulta, sem multiplicar as linhas da venda. Pares diferentes, dados incompletos e placas ausentes exigem confirmação. Uma alteração na placa refaz o cruzamento e invalida a confirmação anterior dessa linha.

A referência em XLSX precisa conter placa_veiculo, veiculo_situacao e Tipo consulta; suas outras colunas não são usadas no cruzamento. O CSV de referência pode usar vírgula, ponto e vírgula ou tabulação, com ou sem BOM.

## Datas, identificadores e pendências

Datas reais do Excel são preservadas como datas. Números de série sem formatação de data são convertidos utilizando o calendário do arquivo. A conversão de outros textos usa `pd.to_datetime` com formatos explícitos e `errors='coerce'`, verificando o resultado antes de aplicá-lo. São aceitos dia/mês/ano e ano/mês/dia, com ano de quatro dígitos, separadores comuns e horários opcionais. Datas impossíveis, anos de dois dígitos e formatos desconhecidos permanecem visíveis como pendências.

Textos e zeros iniciais são preservados. Máscaras numéricas simples de zeros mantêm a largura de identificadores. Outros formatos numéricos de identificador pedem conversão explícita para texto no Excel. Dígitos que já tenham sido perdidos na origem não podem ser reconstruídos.

Campos vazios, células contendo apenas espaços, erros do Excel, movimentações desconhecidas e datas inválidas ficam pendentes até correção ou confirmação explícita de seu valor atual. A exceção é uf_venda no primeiro fluxo, que fica vazia por definição. Produto não exige preenchimento, pois é removido. Linhas vazias entre registros são mantidas e precisam ser revisadas; células apenas formatadas depois do último registro não viram registros vazios.

Fórmulas usam o resultado salvo no Excel, sem recalcular. Uma fórmula sem resultado fica pendente. Recalcule e salve o Excel antes de importar se necessário. Erros na referência não são aceitos automaticamente como situação ou tipo de consulta. As confirmações manuais e a origem do cruzamento ficam registradas no relatório.

Os avisos destacam somente placas fora dos formatos antigo e Mercosul, sem correção automática nem validação cadastral externa. Erros que impedem um cruzamento continuam exigindo revisão, e decisões manuais ficam registradas no relatório.

## Saída padronizada para ambos os fluxos

CSV sempre com **ponto e vírgula e UTF-8 com BOM**. Cabeçalhos em minúsculas, conforme a preferência definida nas versões anteriores:

```text
placa_veiculo;numero_chassis_veiculo;numero_renavam;empresa;uf_placa;veiculo_situacao;tipo consulta;movimentação;data base;cnpj;uf_venda
```

Aspas, separadores e quebras de linha em células são escapados corretamente. O CSV contém todos os registros, mesmo quando a prévia mostra apenas os primeiros 200. A visualização Movimentação mostra até 50 comparações entre o valor original e o final.

Saídas existentes não são sobrescritas: um sufixo como `_2` é acrescentado. Se houver pendências, nenhum arquivo final é criado. O relatório HTML registra as revisões e os avisos. Para abrir o CSV no Excel sem alterar identificadores, importe esses campos como texto em Dados > De Texto/CSV.

## Console

```powershell
py -3 main.py "Atualização de placas.xlsx" --saida "atualizacao.csv"
py -3 main.py "Fluxo UF Venda.xlsx" --referencia "Atualização de placas.xlsx" --saida "venda.csv"
```

Use `--aba` e `--aba-referencia` para arquivos com mais de uma aba. O fluxo também é reconhecido automaticamente no console. Erros de leitura e estrutura aparecem como mensagens claras. Pendências impedem a geração: abra a interface para ajustá-las. Códigos de saída: 0 para sucesso, 2 para erro e 3 para pendências.

## Organização do código

| Módulo | Responsabilidade |
|---|---|
| constants.py, models.py, errors.py | Esquemas, estruturas e erros compartilhados |
| reader.py | Leitura de XLSX e CSV, identificadores e avisos de origem |
| dates.py | Conversão preventiva e validação de datas |
| lookup.py | Índice e correspondências por placa |
| plates.py | Formatos de placa antiga e Mercosul |
| processor.py | Transformações e ajustes da sessão |
| validation.py | Pendências e avisos de consistência |
| exporter.py | CSV padronizado e relatório de conferência |
| ui.py | Interface visual com uma tabela |
| cli.py | Entrada de console |

A lógica de processamento pode ser utilizada sem abrir a interface. Os arquivos monolíticos das versões anteriores não são necessários.

## Verificação

```powershell
py -3 -m unittest discover -s tests -v
```

São 46 testes com dados fictícios, incluindo confirmações individuais, placas antigas e Mercosul, consultas complementares restritas aos faltantes, números de série de datas, calendários 1900/1904, leitura, conflitos, XML inválido, saída real CSV, uso por console e controles reais de Tkinter. Os arquivos dos testes ficam em `work`, na pasta em que o comando for executado. Os valores numéricos da imagem enviada foram reproduzidos nos testes; a planilha real não foi anexada.

Referências de implementação: [pandas.to_datetime](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html), [leitura de XLSX com openpyxl](https://openpyxl.readthedocs.io/en/stable/tutorial.html), [sistemas de datas do Excel](https://openpyxl.readthedocs.io/en/stable/datetime.html) e [formatos das placas no Detran-SP](https://operacoes.sp.gov.br/DetranWeb/saibaMaisSobreNovoModeloDePlacas).
