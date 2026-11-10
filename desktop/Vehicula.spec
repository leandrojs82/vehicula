from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

root = Path(SPECPATH)
hidden = collect_submodules('preparafrota') + ['exportacao', 'pbix_para_excel', 'xlsxwriter']
data = [(str(root / 'web'), 'web'),
        (str(root / 'tools/pbix/app.py'), 'tools/pbix'),
        (str(root / 'tools/preparafrota/PreparaFrota.pyw'), 'tools/preparafrota')]
data += copy_metadata('pbixray')

a = Analysis([str(root / 'main.py')],
             pathex=[str(root), str(root / 'tools/preparafrota'), str(root / 'tools/pbix')],
             binaries=[], datas=data, hiddenimports=hidden, hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['matplotlib', 'scipy', 'IPython', 'PyQt5', 'PyQt6', 'PySide6'],
             noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Vehicula',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'web/vehicula.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Vehicula')
