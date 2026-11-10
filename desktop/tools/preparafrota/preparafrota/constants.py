"""Contrato dos dois arquivos e do CSV de saída."""
CNPJ = '10215988000240'
COLUMNS = ('placa_veiculo', 'numero_chassis_veiculo', 'numero_renavam',
           'empresa', 'uf_placa', 'veiculo_situacao', 'tipo consulta',
           'movimentação', 'data base', 'cnpj', 'uf_venda')
UPDATE_REQUIRED = COLUMNS[:9]
SALE_REQUIRED = COLUMNS[:4] + ('uf origem', 'data venda', 'uf venda')
LOOKUP_FIELDS = ('placa_veiculo', 'veiculo_situacao', 'tipo consulta')
JOIN_FIELDS = LOOKUP_FIELDS[1:]
SALE_RENAME = {'uf origem': 'uf_placa', 'data venda': 'data base', 'uf venda': 'uf_venda'}
MOVEMENTS = {'Incluir Consulta': 'Inclusao', 'Manter Consulta': 'Inclusao', 'Desativar': 'Exclusao'}
EXCEL_ERRORS = {'#REF!', '#DIV/0!', '#VALUE!', '#NAME?', '#N/A', '#NUM!', '#NULL!', '#SPILL!', '#CALC!'}
IDENTIFIERS = COLUMNS[:3]
