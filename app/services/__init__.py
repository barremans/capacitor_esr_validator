"""
================================================================================
Module:     app/services/__init__.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Package-marker voor de servicelaag. Bewust leeg: alle
            services worden door hun aanroepers via volledige paden
            geïmporteerd (bv. ``from app.services.history_service
            import MeasurementHistoryService``), niet via dit package.
            Zo blijft de servicelaag vrij van circulaire imports en
            van een impliciete publieke API die per ongeluk kan
            divergeren.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste versie.
  v1.1.0 (2026-10-22)  Fase 28A: package-marker teruggezet naar leeg.
                        Een eerdere per ongeluk aangebrachte wijziging
                        importeerde uit een niet-bestaande
                        ``app.services.models``-submodule en brak
                        daardoor elke import van eender welke
                        servicemodule.
================================================================================
"""