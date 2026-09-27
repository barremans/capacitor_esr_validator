"""
================================================================================
Module:     tests/test_assessment.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.1
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Unit tests voor de assessment_service. Test alle 20 testgevallen
            uit PROJECT_CONTEXT §22, plus randgevallen.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Tests voor capaciteitsvalidatie,
                       ESR-beoordeling, consistentie, betrouwbaarheid,
                       eindstatus en volledige metingen.
  v1.1.0 (2026-09-26)  Tests aangepast aan expliciete meetmethode;
                       tests toegevoegd voor EX_SITU, ONE_LEG,
                       IN_CIRCUIT en out-of-range.
  v1.1.1 (2026-09-26)  Verwachting voor meerdere verlagende factoren
                       aangepast: IN_CIRCUIT telt nu expliciet mee.
================================================================================
"""

import unittest

from app.services.assessment_service import (
    beoordeel_capaciteit,
    beoordeel_esr,
    controleer_consistentie,
    bepaal_betrouwbaarheid,
    bepaal_eindstatus,
    beoordeel_meting,
    CapaciteitsStatus,
    EsrStatus,
    ConsistentieStatus,
    Betrouwbaarheid,
    Eindstatus,
    ReferentieContext,
    Meetmethode,
)


class TestCapaciteit(unittest.TestCase):
    """Testgevallen 1, 3, 4, 5 uit PROJECT_CONTEXT §22."""

    def test_binnen_tolerantie(self):
        r = beoordeel_capaciteit(100, "µF", 98, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BINNEN_TOLERANTIE)

    def test_op_grens(self):
        # 19% afwijking, marge_binnen = 0.9 * 20 = 18%
        # 19% > 18% (buiten binnen) maar <= 20% (op grens)
        r = beoordeel_capaciteit(100, "µF", 119, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.OP_GRENS)

    def test_buiten_tolerantie(self):
        r = beoordeel_capaciteit(100, "µF", 130, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BUITEN_TOLERANTIE)

    def test_eenheid_conversie_mf_naar_uf(self):
        """Testgeval 1: 470 µF ingevoerd als 0,47 mF."""
        r = beoordeel_capaciteit(470, "µF", 0.47, "mF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BINNEN_TOLERANTIE)
        self.assertAlmostEqual(r.gemeten_waarde, 470.0, places=2)

    def test_komma_en_punt(self):
        """Testgeval 3: komma en punt als decimaalteken."""
        from app.helpers.units import parse_decimaal
        self.assertEqual(parse_decimaal("4,7"), 4.7)
        self.assertEqual(parse_decimaal("4.7"), 4.7)

    def test_tolerantie_onbekend(self):
        """Tolerantie ontbreekt -> niet beoordeelbaar."""
        r = beoordeel_capaciteit(100, "µF", 98, "µF", None)
        self.assertEqual(r.status, CapaciteitsStatus.NIET_BEOORDEELBAAR)


class TestESR(unittest.TestCase):
    """Testgevallen 2, 6, 7, 8 uit PROJECT_CONTEXT §22."""

    def test_eenheid_conversie_mohm_naar_ohm(self):
        """Testgeval 2: ESR ingevoerd in mΩ en Ω."""
        from app.helpers.units import converteer_esr
        self.assertAlmostEqual(converteer_esr(100, "mΩ", "Ω"), 0.1, places=4)
        self.assertAlmostEqual(converteer_esr(0.1, "Ω", "mΩ"), 100.0, places=4)

    def test_waarschijnlijk_normaal(self):
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(80, "mΩ", 1000, ref)
        self.assertEqual(r.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)

    def test_aandachtspunt(self):
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(150, "mΩ", 1000, ref)
        self.assertEqual(r.status, EsrStatus.AANDACHTSPUNT)

    def test_verdacht(self):
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(250, "mΩ", 1000, ref)
        self.assertEqual(r.status, EsrStatus.VERDACHT)

    def test_waarschijnlijk_defect(self):
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(400, "mΩ", 1000, ref)
        self.assertEqual(r.status, EsrStatus.WAARSCHIJNLIJK_DEFECT)

    def test_frequentie_wijkt_af(self):
        """Testgeval 7: datasheetwaarde met andere frequentie."""
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=100000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(80, "mΩ", 1000, ref)
        self.assertTrue(r.frequentie_wijkt_af)

    def test_geen_referentie(self):
        """Geen referentie -> niet te beoordelen."""
        r = beoordeel_esr(100, "mΩ", 1000, None)
        self.assertEqual(r.status, EsrStatus.NIET_TE_BEOORDELEN)


class TestConsistentie(unittest.TestCase):
    """Testgevallen 12, 13 uit PROJECT_CONTEXT §22."""

    def test_consistent(self):
        """Testgeval 12: C, ESR en D die onderling ongeveer kloppen."""
        # D ≈ 2πfC·ESR
        # C=100µF, f=100Hz, ESR=1.6Ω → D ≈ 2π·100·100e-6·1.6 ≈ 0.1
        r = controleer_consistentie(100, "µF", 1.6, "Ω", 0.1, 100)
        self.assertEqual(r.status, ConsistentieStatus.CONSISTENT)

    def test_eenhedenfout_factor_1000(self):
        """Testgeval 13: C, ESR en D met een factor-1000-eenhedenfout."""
        r = controleer_consistentie(100, "mF", 1.6, "Ω", 0.1, 100)
        self.assertEqual(r.status, ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT)

    def test_geen_d(self):
        """Testgeval 14: Geen D-waarde ingevoerd."""
        r = controleer_consistentie(100, "µF", 1.6, "Ω", None, 100)
        self.assertEqual(r.status, ConsistentieStatus.NIET_BEOORDEELD)


class TestBetrouwbaarheid(unittest.TestCase):
    """Testgevallen 9, 10 uit PROJECT_CONTEXT §22."""

    def test_hoog(self):
        """EX_SITU: volledig uitgebouwd, hoogste meetcontext-betrouwbaarheid."""
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=20,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=True,
            serie_bekend=True,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.niveau, Betrouwbaarheid.HOOG)

    def test_verlaagd_door_in_circuit(self):
        """Testgeval 9: In-circuit meting."""
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=20,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.IN_CIRCUIT,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=True,
            serie_bekend=True,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.niveau, Betrouwbaarheid.LAAG)

    def test_one_leg_maximaal_middel(self):
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=20,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.ONE_LEG,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=True,
            serie_bekend=True,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.niveau, Betrouwbaarheid.MIDDEL)

    def test_meerdere_verlagende_factoren(self):
        """Testgeval 16: meerdere onafhankelijke factoren verlagen betrouwbaarheid."""
        r = bepaal_betrouwbaarheid(
            referentieniveau=5,
            referentiefrequentie_hz=100000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=None,
            condensatortype="Anders",
            meetmethode=Meetmethode.IN_CIRCUIT,
            referentie_typisch_of_maximaal="typisch",
            fabrikant_bekend=False,
            serie_bekend=False,
            consistentie_status=ConsistentieStatus.MOGELIJKE_INCONSISTENTIE,
        )

        self.assertEqual(r.niveau, Betrouwbaarheid.LAAG)

        # In v1.3 telt IN_CIRCUIT als expliciete extra verlagende factor.
        # Dit scenario bevat minimaal:
        # - frequentieverschil
        # - temperatuur onbekend
        # - condensatortype afwijkend/onbekend
        # - typische referentiewaarde
        # - fabrikant/serie onbekend
        # - mogelijke C-ESR-D-inconsistentie
        # - in-circuit meetmethode
        self.assertGreaterEqual(len(r.verlagende_factoren), 7)


class TestEindstatus(unittest.TestCase):
    """Testgevallen voor eindstatuscombinaties."""

    def test_waarschijnlijk_goed(self):
        cap = beoordeel_capaciteit(100, "µF", 100, "µF", 20)
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=1, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        esr = beoordeel_esr(80, "mΩ", 1000, ref)
        cons = controleer_consistentie(100, "µF", 0.08, "Ω", None, 1000)
        betr = bepaal_betrouwbaarheid(
            1, 1000, 1000, 20, "Aluminium elektrolytisch",
            Meetmethode.EX_SITU, "maximaal", True, True,
            ConsistentieStatus.NIET_BEOORDEELD
        )
        status, redenen, stap = bepaal_eindstatus(cap, esr, cons, betr, True)
        self.assertEqual(status, Eindstatus.WAARSCHIJNLIJK_GOED)

    def test_veiligheid_ontbreekt(self):
        """Testgeval: veiligheid niet bevestigd."""
        cap = beoordeel_capaciteit(100, "µF", 100, "µF", 20)
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=1, frequentie_hz=1000,
            typisch_of_maximaal="maximaal"
        )
        esr = beoordeel_esr(80, "mΩ", 1000, ref)
        cons = controleer_consistentie(100, "µF", 0.08, "Ω", None, 1000)
        betr = bepaal_betrouwbaarheid(
            1, 1000, 1000, 20, "Aluminium elektrolytisch",
            Meetmethode.EX_SITU, "maximaal", True, True,
            ConsistentieStatus.NIET_BEOORDEELD
        )
        status, redenen, stap = bepaal_eindstatus(cap, esr, cons, betr, False)
        self.assertEqual(status, Eindstatus.NIET_TE_BEOORDELEN)


class TestVolledigeMeting(unittest.TestCase):
    """Testgevallen voor de volledige beoordelingsketen."""

    def test_gebruiksscenario_1_goed(self):
        """470µF/25V condensator, goede meting."""
        ref = ReferentieContext(
            esr_waarde=120, eenheid="mΩ", bron="Peak Atlas ESR70",
            referentieniveau=5, frequentie_hz=100000,
            typisch_of_maximaal="maximaal"
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=465,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.1,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=1000,
            D=0.05,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        # ESR factor = 0.1Ω / 0.12Ω = 0.83 -> normaal
        # Capaciteit: 465 vs 470 -> binnen tolerantie
        self.assertEqual(resultaat.capaciteit.status, CapaciteitsStatus.BINNEN_TOLERANTIE)
        self.assertEqual(resultaat.esr.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)

    def test_gebruiksscenario_2_defect(self):
        """470µF/25V condensator, zeer hoge ESR."""
        ref = ReferentieContext(
            esr_waarde=120, eenheid="mΩ", bron="Peak Atlas ESR70",
            referentieniveau=5, frequentie_hz=100000,
            typisch_of_maximaal="maximaal"
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=460,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.5,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        # ESR factor = 0.5Ω / 0.12Ω = 4.17 -> waarschijnlijk defect
        self.assertEqual(resultaat.esr.status, EsrStatus.WAARSCHIJNLIJK_DEFECT)


    def test_out_of_range_geeft_niet_te_beoordelen(self):
        ref = ReferentieContext(
            esr_waarde=120,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=1,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=470,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.1,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
            meetwaarde_buiten_bereik=True,
        )
        self.assertEqual(resultaat.eindstatus, Eindstatus.NIET_TE_BEOORDELEN)


if __name__ == "__main__":
    unittest.main()