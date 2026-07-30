# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['serve_data.py'],
    pathex=[],
    binaries=[],
    datas=[('ivi.icns', '.')],
    hiddenimports=[],
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
    name='ivi_meta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    [],
    name='ivi_meta',
)

app = BUNDLE(
    coll,
    a.binaries,
    a.datas,
    [],
    name='IVI Admin Editor',
    icon='ivi.icns',
    bundle_identifier='com.ivieditor.admin',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleDisplayName': 'IVI Admin Editor',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
    },
)
