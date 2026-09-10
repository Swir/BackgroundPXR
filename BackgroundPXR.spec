# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# Collect the full GUI + AI runtime payload.  Keeping onnxruntime here in
# addition to its PyInstaller hook makes the frozen-runtime contract explicit
# and protects future dependency changes.
for package in ("customtkinter", "tkinterdnd2", "rembg", "pymatting", "onnxruntime"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

# pymatting reads its own installed version through importlib.metadata during
# import.  Those *.dist-info directories must exist in the portable build.
for package in ("pymatting", "rembg", "onnxruntime"):
    datas += copy_metadata(package)


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
