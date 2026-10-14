# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# Electronics Diagnostic Tool Hub / ESR Tester
# File:    ESR_Tester.spec
# Role:    PyInstaller build-specificatie — bundelt main.py, app/, i18n/,
#          docs/ en assets/ tot een zelfstandige Windows-build.
#
#          Wordt aangeroepen via build_installer.bat.
#
# Version: 2.0.0
# Author:  Bart Bossuyt
# Changes: 2.0.0 (2026-10-13) - Fase 9C+9D. icon= toegevoegd aan het EXE(...)-
#                               blok, zodat het icoon in de app-EXE zelf
#                               terechtkomt. Pad: assets\icons\logo.ico.
#                               Verder identiek aan v1.0.0.
# Changes: 1.0.0 (2026-10-13) - Fase 9B.2. Eerste versie, afgeleid van het
#                               ArticleSearch-patroon, maar zonder MSAL,
#                               zonder Azure, zonder check_github_secret.py,
#                               en zonder icon= (icoon volgde in 9G; nu
#                               opgenomen in 2.0.0). Inclusief VC++
#                               runtime-DLL's, pandas, PySide6, pypdf,
#                               requests, bs4, docx, openpyxl.
# =============================================================================

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

# --- pandas zonder tests ---
pandas_datas, pandas_binaries, pandas_hidden = collect_all("pandas")
pandas_hidden = [h for h in pandas_hidden if not h.startswith("pandas.tests")]

# --- VC++ runtime in _internal plaatsen ---
extra_bins = []
windir = os.environ.get("WINDIR", r"C:\Windows")
candidates = [
    os.path.join(windir, "System32", "vcruntime140.dll"),
    os.path.join(windir, "System32", "vcruntime140_1.dll"),
    os.path.join(windir, "System32", "msvcp140.dll"),
    r".\.venv\Scripts\vcruntime140.dll",
    r".\.venv\Scripts\vcruntime140_1.dll",
    r".\.venv\Scripts\msvcp140.dll",
]
for p in candidates:
    if os.path.exists(p):
        extra_bins.append((p, "_internal"))

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=pandas_binaries + extra_bins,
    datas=pandas_datas,
    hiddenimports=[
        *pandas_hidden,
        "requests",
        "urllib3",
        "bs4",
        "docx",
        "openpyxl",
        "pypdf",
    ],
    excludes=["pandas.tests", "tkinter", "matplotlib", "numpy.tests"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ESR_Tester",
    icon=r"assets\icons\logo.ico",
    console=False,
    disable_windowed_traceback=False,
)

# --- Resource-mappen mee in de bundel ---
from PyInstaller.building.datastruct import Tree

collect_datas = []

for mapnaam in ("app", "i18n", "docs", "assets"):
    if os.path.isdir(mapnaam):
        collect_datas.append(
            Tree(mapnaam, prefix=mapnaam, excludes=["**/__pycache__/*"])
        )

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *collect_datas,
    strip=False,
    upx=False,
    name="ESR_Tester",
)