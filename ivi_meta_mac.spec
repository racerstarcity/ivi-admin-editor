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

app = BUNDLE(
    pyz,
    a.scripts,
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
