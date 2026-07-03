# -*- mode: python ; coding: utf-8 -*-

import sys

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
    is_module_or_submodule,
)


datas = [
    ("config", "config"),
    (".streamlit", ".streamlit"),
    ("streamlit_app.py", "."),
]
binaries = []
hiddenimports = []

for import_name, metadata_name in (
    ("streamlit", "streamlit"),
    ("plotly", "plotly"),
    ("pyarrow", "pyarrow"),
    ("ccxt", "ccxt"),
    ("webview", "pywebview"),
):
    package_datas, package_binaries, package_hiddenimports = collect_all(import_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports
    datas += copy_metadata(metadata_name)

datas += collect_data_files("kaleido")
binaries += collect_dynamic_libs("kaleido")
hiddenimports += collect_submodules(
    "kaleido",
    filter=lambda name: not is_module_or_submodule(name, "kaleido.mocker"),
    on_error="ignore",
)
datas += copy_metadata("kaleido")


a = Analysis(
    ["desktop_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe_name = "QuantVibe-bin" if sys.platform == "darwin" else "QuantVibe"

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name="QuantVibe",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="QuantVibe.app",
        icon=None,
        bundle_identifier="com.answer-version.quantvibe",
    )
