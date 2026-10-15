"""
================================================================================
Module:     tests/test_references.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-10-15
Auteur:     Ontwikkelaar

Doel:       Regressietests voor app/data/references/__init__.py.
            Test profielselectie op frequentie, fallback, kleine
            capaciteiten en de officiële ESR70-tabel. Sinds fase 10B
            ook de geschatte profielen voor 100 Hz / 1 kHz / 10 kHz.

Wijzigingen:
  v1.0.0 (2026-10-15)  Eerste versie voor fase 10A (profielen-model).
  v1.1.0 (2026-10-15)  Fase 10B: tests aangepast aan de gevulde
                       geschatte profielen. 1 kHz en 10 kHz vallen
                       niet meer terug op 100 kHz. Nieuwe tests voor
                       de schalingsfactoren (×1,15 / ×1,50 / ×2,00).

Referentie: overdracht.md §8 (fase 10), docs/validation_rules.md §2,
            docs/phase10_analysis.md.
================================================================================
"""

import unittest

from app.data.references import (
    zoek_referentie,
    _laad_profielen,
)


class TestProfielenLaden(unittest.TestCase):
    def test_profielen_worden_geladen(self):
        profielen = _laad_profielen()
        self.assertGreater(len(profielen), 0)

    def test_esr70_profiel_bestaat(self):
        profielen = _laad_profielen()
        ids = [p.id for p in profielen]
        self.assertIn("esr70_100khz", ids)

    def test_esr70_profiel_heeft_regels(self):
        profielen = _laad_profielen()
        esr70 = next(p for p in profielen if p.id == "esr70_100khz")
        self.assertGreater(len(esr70.regels), 0)

    def test_esr70_profiel_frequentie_is_100khz(self):
        profielen = _laad_profielen()
        esr70 = next(p for p in profielen if p.id == "esr70_100khz")
        self.assertEqual(esr70.frequentie_hz, 100000)


class TestOfficieleESR70Waarden(unittest.TestCase):
    """Controleer dat de officiële ESR70-waarden correct zijn ingeladen."""

    def _zoek(self, cap, volt):
        return zoek_referentie(cap, volt, meetfrequentie_hz=100000)

    def test_470uf_25v_is_400_mohm(self):
        r = self._zoek(470, 25)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 400)
        self.assertEqual(r.eenheid, "mΩ")

    def test_1000uf_25v_is_190_mohm(self):
        r = self._zoek(1000, 25)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 190)

    def test_100uf_25v_is_1900_mohm(self):
        r = self._zoek(100, 25)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 1900)

    def test_470uf_63v_is_250_mohm(self):
        r = self._zoek(470, 63)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 250)


class TestProfielSelectieOpFrequentie(unittest.TestCase):
    """Sinds 10B hebben de geschatte profielen regels; de fallback naar
    100 kHz gebeurt niet meer."""

    def test_1khz_krijgt_1khz_profiel(self):
        r = zoek_referentie(470, 25, meetfrequentie_hz=1000)
        self.assertIsNotNone(r)
        self.assertEqual(r.frequentie_hz, 1000)

    def test_10khz_krijgt_10khz_profiel(self):
        r = zoek_referentie(470, 25, meetfrequentie_hz=10000)
        self.assertIsNotNone(r)
        self.assertEqual(r.frequentie_hz, 10000)

    def test_100hz_krijgt_100hz_profiel(self):
        r = zoek_referentie(470, 25, meetfrequentie_hz=100)
        self.assertIsNotNone(r)
        self.assertEqual(r.frequentie_hz, 100)

    def test_100khz_krijgt_100khz_profiel(self):
        r = zoek_referentie(470, 25, meetfrequentie_hz=100000)
        self.assertIsNotNone(r)
        self.assertEqual(r.frequentie_hz, 100000)

    def test_zonder_frequentie_geeft_esr70(self):
        # Backward-compatible: zonder frequentie kiest het eerste profiel
        # met regels, wat het ESR70 100 kHz-profiel is.
        r = zoek_referentie(470, 25)
        self.assertIsNotNone(r)
        self.assertEqual(r.frequentie_hz, 100000)


class TestSchalingsfactoren(unittest.TestCase):
    """Controleer dat de geschatte profielen de juiste Nichicon-factor
    toepassen op de ESR70-basiswaarden."""

    def _verwacht(self, basis_mohm, factor):
        return round(basis_mohm * factor)

    def test_470uf_25v_op_1khz_is_600_mohm(self):
        """ESR70 470 µF / 25 V = 400 mΩ. ×1,50 = 600 mΩ."""
        r = zoek_referentie(470, 25, meetfrequentie_hz=1000)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 600)

    def test_470uf_25v_op_10khz_is_460_mohm(self):
        """ESR70 470 µF / 25 V = 400 mΩ. ×1,15 = 460 mΩ."""
        r = zoek_referentie(470, 25, meetfrequentie_hz=10000)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 460)

    def test_470uf_25v_op_100hz_is_800_mohm(self):
        """ESR70 470 µF / 25 V = 400 mΩ. ×2,00 = 800 mΩ."""
        r = zoek_referentie(470, 25, meetfrequentie_hz=100)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 800)

    def test_220uf_25v_op_1khz_is_1260_mohm(self):
        """ESR70 220 µF / 25 V = 840 mΩ. ×1,50 = 1260 mΩ."""
        r = zoek_referentie(220, 25, meetfrequentie_hz=1000)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 1260)

    def test_1000uf_25v_op_1khz_is_285_mohm(self):
        """ESR70 1000 µF / 25 V = 190 mΩ. ×1,50 = 285 mΩ."""
        r = zoek_referentie(1000, 25, meetfrequentie_hz=1000)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 285)

    def test_1000uf_25v_op_10khz_is_218_mohm(self):
        """ESR70 1000 µF / 25 V = 190 mΩ. ×1,15 = 218,5 → afgerond 218 mΩ
        (Python round naar even: 218.5 → 218)."""
        r = zoek_referentie(1000, 25, meetfrequentie_hz=10000)
        self.assertIsNotNone(r)
        # 190 * 1.15 = 218.5 → round() in Python geeft 218 (banker's rounding).
        # In JSON staat de handmatig afgeronde waarde 218.
        self.assertEqual(r.esr_waarde, 218)

    def test_4_7uf_50v_op_1khz_is_42000_mohm(self):
        """ESR70 4,7 µF / 50 V = 28000 mΩ. ×1,50 = 42000 mΩ."""
        r = zoek_referentie(4.7, 50, meetfrequentie_hz=1000)
        self.assertIsNotNone(r)
        self.assertEqual(r.esr_waarde, 42000)


class TestKleineCapaciteiten(unittest.TestCase):
    def test_1uf_50v_wordt_gevonden(self):
        r = zoek_referentie(1.0, 50, meetfrequentie_hz=100000)
        self.assertIsNotNone(r)
        # ESR70 begint bij 4.7 µF; 1.0 µF valt binnen 20% van 4.7? Nee.
        # Dus dichtstbijzijnde ESR70-regel is 4.7 µF → 28000 mΩ (50V)
        self.assertGreater(r.esr_waarde, 0)

    def test_0_1uf_50v_wordt_gevonden(self):
        r = zoek_referentie(0.1, 50, meetfrequentie_hz=100000)
        self.assertIsNotNone(r)


class TestOnbekendType(unittest.TestCase):
    def test_onbekend_condensatortype_geeft_none(self):
        r = zoek_referentie(470, 25, condensatortype="Keramisch")
        self.assertIsNone(r)

    def test_polymer_geeft_none(self):
        r = zoek_referentie(470, 25, condensatortype="Polymer")
        self.assertIsNone(r)


if __name__ == "__main__":
    unittest.main()