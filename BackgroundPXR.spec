# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None

datas = []
binaries = []
hiddenimports = []

for package in ("customtkinter", "tkinterdnd2", "rembg", "pymatting"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

# pymatting calls importlib.metadata.version("pymatting") at import time.
# PyInstaller code collection alone does not guarantee dist-info metadata.
for package in ("pymatting", "rembg", "onnxruntime"):
    try:
        datas += copy_metadata(package)
    except Exception:
        pass


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BackgroundPXR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="build_assets/BackgroundPXR.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BackgroundPXR",
)
