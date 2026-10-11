"""
Diagnostisch script voor het menu-probleem (Fase 8C).

Draai met: python debug_menu.py
Geen pytest, geen fixtures — gewoon direct de ToolHubWindow bouwen
en de menubar inspecteren.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMenu

app = QApplication.instance() or QApplication([])

print("=" * 70)
print("STAP 1: importeer ToolHubWindow")
print("=" * 70)
from app.gui.main_window import ToolHubWindow

print()
print("=" * 70)
print("STAP 2: bouw ToolHubWindow(taal='nl_NL')")
print("=" * 70)
window = ToolHubWindow(taal="nl_NL")

print()
print("=" * 70)
print("STAP 3: inspecteer menubar direct na constructie")
print("=" * 70)
menubar = window.menuBar()

print(f"Aantal top-level acties in menubar: {len(menubar.actions())}")
for i, actie in enumerate(menubar.actions()):
    try:
        tekst = actie.text()
        menu = actie.menu()
        heeft_menu = menu is not None
        print(f"  [{i}] '{tekst}' (menu: {heeft_menu})")
    except RuntimeError as exc:
        print(f"  [{i}] RuntimeError: {exc}")

print()
print("=" * 70)
print("STAP 4: inspecteer elk QMenu-kinds van de menubar")
print("=" * 70)
menu_kinderen = menubar.findChildren(QMenu)
print(f"Aantal QMenu-kinderen: {len(menu_kinderen)}")
for i, menu in enumerate(menu_kinderen):
    try:
        titel = menu.title()
    except RuntimeError as exc:
        print(f"  [{i}] RuntimeError bij title(): {exc}")
        continue

    print(f"  [{i}] QMenu '{titel}'")
    acties = menu.actions()
    print(f"        Aantal acties: {len(acties)}")
    for j, actie in enumerate(acties):
        try:
            tekst = actie.text()
            print(f"        [{j}] '{tekst}'")
        except RuntimeError as exc:
            print(f"        [{j}] RuntimeError: {exc}")

print()
print("=" * 70)
print("STAP 5: roep _apply_language() opnieuw aan")
print("=" * 70)
window._apply_language()

menubar = window.menuBar()
print(f"Aantal top-level acties in menubar: {len(menubar.actions())}")
for i, actie in enumerate(menubar.actions()):
    try:
        tekst = actie.text()
        menu = actie.menu()
        heeft_menu = menu is not None
        print(f"  [{i}] '{tekst}' (menu: {heeft_menu})")
    except RuntimeError as exc:
        print(f"  [{i}] RuntimeError: {exc}")

print()
print("=" * 70)
print("STAP 6: inspecteer QMenu-kinderen NA tweede _apply_language()")
print("=" * 70)
menu_kinderen = menubar.findChildren(QMenu)
print(f"Aantal QMenu-kinderen: {len(menu_kinderen)}")
for i, menu in enumerate(menu_kinderen):
    try:
        titel = menu.title()
    except RuntimeError as exc:
        print(f"  [{i}] RuntimeError bij title(): {exc}")
        continue
    print(f"  [{i}] QMenu '{titel}'")
    for j, actie in enumerate(menu.actions()):
        try:
            tekst = actie.text()
            print(f"        [{j}] '{tekst}'")
        except RuntimeError as exc:
            print(f"        [{j}] RuntimeError: {exc}")

print()
print("=" * 70)
print("STAP 7: zoek 'Rapport maken…' recursief via menubar.actions()")
print("=" * 70)
gevonden = False
for menu_actie in menubar.actions():
    menu = menu_actie.menu()
    if menu is None:
        continue
    for actie in menu.actions():
        try:
            tekst = actie.text()
        except RuntimeError as exc:
            print(f"  RuntimeError: {exc}")
            continue
        if "Rapport" in tekst:
            print(f"  GEVONDEN: '{tekst}' shortcut={actie.shortcut().toString()}")
            gevonden = True
if not gevonden:
    print("  NIET GEVONDEN")

print()
print("KLAAR")