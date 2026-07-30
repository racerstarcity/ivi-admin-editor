# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\user\\Documents\\New OpenCode Project\\web_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\Квитанция.docx', '.'),
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\Справка Эконом.docx', '.'),
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\Договор Лосинки.docx', '.'),
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\Прайс-2500.docx', '.'),
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\ЕГРИП.pdf', '.'),
        ('C:\\Users\\user\\Documents\\New OpenCode Project\\templates\\ИП ИНН.pdf', '.'),
    ],
    hiddenimports=['flask', 'docx', 'docx.shared', 'docx.enum.text', 'zipfile', 'csv', 'io', 're', 'urllib.request'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Гостиница',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
