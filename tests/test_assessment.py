"""
================================================================================
Module:     tests/test_assessment.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.6.2
Datum:      2026-10-26
Auteur:     Ontwikkelaar

Doel:       Unit tests voor de assessment_service.

Wijzigingen:
  v1.0.0 t/m v1.6.1  zie eerdere versies.
  v1.6.2 (2026-10-26) Chat 4 / 4C: één nieuwe test in TestTypeFamilie
                       die aantoont dat een niet-elektrolytisch type de
                       waarschuwing veiligheid.geen_elektrolytische_
                       referentie krijgt. De bestaande tests blijven
                       ongewijzigd groen: is_elektrolytisch_type en
                       _zelfde_technologie_familie zijn verplaatst naar
                       app.helpers.technology maar worden door
                       assessment_service opnieuw geëxporteerd.
================================================================================
"""

import unittest

from app.config.settings import BeoordelingsInstellingen
from app.services.assessment_service import (
    beoordeel_capaciteit,
    beoordeel_esr,
    controleer_consistentie,
    bepaal_betrouwbaarheid,
    bepaal_eindstatus,
    beoordeel_meting,
    is_elektrolytisch_type,
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
        r = beoordeel_capaciteit(100, "µF", 119, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.OP_GRENS)

    def test_buiten_tolerantie(self):
        r = beoordeel_capaciteit(100, "µF", 130, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BUITEN_TOLERANTIE)

    def test_exact_op_positieve_tolerantielimiet(self):
        r = beoordeel_capaciteit(100, "µF", 120, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.OP_GRENS)

    def test_exact_op_negatieve_tolerantielimiet(self):
        r = beoordeel_capaciteit(100, "µF", 80, "µF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.OP_GRENS)

    def test_net_buiten_tolerantielimiet(self):
        hoog = beoordeel_capaciteit(100, "µF", 120.01, "µF", 20)
        laag = beoordeel_capaciteit(100, "µF", 79.99, "µF", 20)
        self.assertEqual(hoog.status, CapaciteitsStatus.BUITEN_TOLERANTIE)
        self.assertEqual(laag.status, CapaciteitsStatus.BUITEN_TOLERANTIE)

    def test_eenheid_conversie_mf_naar_uf(self):
        r = beoordeel_capaciteit(470, "µF", 0.47, "mF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BINNEN_TOLERANTIE)
        self.assertAlmostEqual(r.gemeten_waarde, 470.0, places=2)

    def test_komma_en_punt(self):
        from app.helpers.units import parse_decimaal
        self.assertEqual(parse_decimaal("4,7"), 4.7)
        self.assertEqual(parse_decimaal("4.7"), 4.7)

    def test_tolerantie_onbekend(self):
        r = beoordeel_capaciteit(100, "µF", 98, "µF", None)
        self.assertEqual(r.status, CapaciteitsStatus.NIET_BEOORDEELBAAR)


class TestESR(unittest.TestCase):
    """Testgevallen 2, 6, 7, 8 uit PROJECT_CONTEXT §22."""

    def test_eenheid_conversie_mohm_naar_ohm(self):
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
        ref = ReferentieContext(
            esr_waarde=100, eenheid="mΩ", bron="Test",
            referentieniveau=5, frequentie_hz=100000,
            typisch_of_maximaal="maximaal"
        )
        r = beoordeel_esr(80, "mΩ", 1000, ref)
        self.assertTrue(r.frequentie_wijkt_af)

    def test_geen_referentie(self):
        r = beoordeel_esr(100, "mΩ", 1000, None)
        self.assertEqual(r.status, EsrStatus.NIET_TE_BEOORDELEN)


class TestConsistentie(unittest.TestCase):
    """Testgevallen 12, 13 uit PROJECT_CONTEXT §22."""

    def test_consistent(self):
        r = controleer_consistentie(100, "µF", 1.6, "Ω", 0.1, 100)
        self.assertEqual(r.status, ConsistentieStatus.CONSISTENT)

    def test_eenhedenfout_factor_1000(self):
        r = controleer_consistentie(100, "mF", 1.6, "Ω", 0.1, 100)
        self.assertEqual(r.status, ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT)

    def test_geen_d(self):
        r = controleer_consistentie(100, "µF", 1.6, "Ω", None, 100)
        self.assertEqual(r.status, ConsistentieStatus.NIET_BEOORDEELD)


class TestBetrouwbaarheid(unittest.TestCase):
    """Testgevallen 9, 10 uit PROJECT_CONTEXT §22."""

    def test_hoog(self):
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
        self.assertGreaterEqual(len(r.verlagende_factoren), 7)
        self.assertGreaterEqual(len(r.inhoudelijke_verlagers), 4)


class TestInhoudelijkeVsAdministratieveVerlagers(unittest.TestCase):
    """Fase 11B: alleen inhoudelijke verlagers verhogen het minimum van de
    eindstatus."""

    def _ref(self, freq_hz=1000, type_="Aluminium elektrolytisch"):
        return ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=1,
            frequentie_hz=freq_hz,
            typisch_of_maximaal="maximaal",
            condensatortype=type_,
        )

    def test_alleen_administratieve_verlagers_geven_waarschijnlijk_goed(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=False,
            serie_bekend=False,
        )
        self.assertEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.MIDDEL)
        self.assertEqual(resultaat.betrouwbaarheid.inhoudelijke_verlagers, ())
        self.assertEqual(resultaat.eindstatus, Eindstatus.WAARSCHIJNLIJK_GOED)

    def test_alleen_administratieve_verlagers_meerdere_geven_waarschijnlijk_goed(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=None,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=False,
            serie_bekend=False,
        )
        self.assertEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.LAAG)
        self.assertEqual(resultaat.betrouwbaarheid.inhoudelijke_verlagers, ())
        self.assertEqual(resultaat.eindstatus, Eindstatus.WAARSCHIJNLIJK_GOED)

    def test_inhoudelijke_verlager_frequentieverschil_geeft_aandachtspunt(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(freq_hz=100000),
            fabrikant_bekend=False,
            serie_bekend=False,
        )
        self.assertTrue(resultaat.betrouwbaarheid.inhoudelijke_verlagers)
        self.assertEqual(resultaat.eindstatus, Eindstatus.AANDACHTSPUNT)

    def test_inhoudelijke_verlager_in_circuit_geeft_aandachtspunt(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.IN_CIRCUIT,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertTrue(resultaat.betrouwbaarheid.inhoudelijke_verlagers)
        self.assertEqual(resultaat.eindstatus, Eindstatus.AANDACHTSPUNT)

    def test_inhoudelijke_verlager_type_mismatch_geeft_aandachtspunt(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Anders",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(type_="Aluminium elektrolytisch"),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertTrue(resultaat.betrouwbaarheid.inhoudelijke_verlagers)
        self.assertEqual(resultaat.eindstatus, Eindstatus.AANDACHTSPUNT)

    def test_bepaal_betrouwbaarheid_splitst_correct(self):
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=100000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=False,
            serie_bekend=False,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(len(r.inhoudelijke_verlagers), 1)
        self.assertIn("frequentie", r.inhoudelijke_verlagers[0].lower())
        self.assertEqual(len(r.verlagende_factoren), 3)

    def test_bepaal_betrouwbaarheid_alleen_administratief(self):
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=False,
            serie_bekend=False,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.inhoudelijke_verlagers, ())
        self.assertEqual(len(r.verlagende_factoren), 2)

    def test_bepaal_betrouwbaarheid_typische_referentie_is_administratief(self):
        r = bepaal_betrouwbaarheid(
            referentieniveau=1,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=20,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            referentie_typisch_of_maximaal="typisch",
            fabrikant_bekend=True,
            serie_bekend=True,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.inhoudelijke_verlagers, ())
        self.assertEqual(len(r.verlagende_factoren), 1)

    def test_bepaal_betrouwbaarheid_inconsistentie_is_inhoudelijk(self):
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
            consistentie_status=ConsistentieStatus.MOGELIJKE_INCONSISTENTIE,
        )
        self.assertEqual(len(r.inhoudelijke_verlagers), 1)
        self.assertEqual(len(r.verlagende_factoren), 1)


class TestReferentieValidatie(unittest.TestCase):
    """Regressies voor type-match en referentiecondities."""

    def test_referentietype_mismatch_geeft_lage_betrouwbaarheid_en_waarschuwing(self):
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Testreferentie",
            referentieniveau=1,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Anders",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.LAAG)
        self.assertTrue(
            any("referentietype" in waarschuwing.lower() or "type" in waarschuwing.lower()
                for waarschuwing in resultaat.waarschuwingen)
        )

    def test_verkeerde_condensatortechnologie_wordt_niet_stilzwijgend_hoog_betrouwbaar(self):
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Algemene aluminiumtabel",
            referentieniveau=1,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Anders",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertNotEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.HOOG)

    def test_referentie_zonder_frequentie_crasht_niet_en_blijft_conservatief(self):
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Referentie zonder frequentie",
            referentieniveau=1,
            frequentie_hz=None,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
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
        self.assertIsNotNone(resultaat)
        self.assertNotEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.HOOG)


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
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.capaciteit.status, CapaciteitsStatus.BINNEN_TOLERANTIE)
        self.assertEqual(resultaat.esr.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)
        self.assertEqual(resultaat.eindstatus, Eindstatus.AANDACHTSPUNT)

    def test_gebruiksscenario_2_defect(self):
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


    def test_out_of_range_bevat_reden_waarschuwing_en_vervolgstap(self):
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

        from app.helpers.i18n import vertaal

        self.assertEqual(resultaat.eindstatus, Eindstatus.NIET_TE_BEOORDELEN)
        self.assertEqual(
            resultaat.redenen,
            (vertaal("eindstatus_reden.buiten_bereik"),),
        )
        self.assertIn(
            vertaal("veiligheid.buiten_bereik"),
            resultaat.waarschuwingen,
        )
        self.assertEqual(
            resultaat.aanbevolen_vervolgstap,
            vertaal("eindstatus_vervolgstap.controleer_meetbereik"),
        )

    def test_open_short_met_capaciteit_buiten_tolerantie_geeft_waarschijnlijk_defect(self):
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
            gemeten_capaciteit=100,
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
            vermoedelijke_open_verbinding_of_kortsluiting=True,
        )

        from app.helpers.i18n import vertaal

        self.assertEqual(resultaat.eindstatus, Eindstatus.WAARSCHIJNLIJK_DEFECT)
        self.assertIn(
            vertaal("eindstatus_reden.capaciteit_buiten_tolerantie_defect"),
            resultaat.redenen,
        )
        self.assertIn(
            vertaal("eindstatus_reden.open_verbinding_vermoed"),
            resultaat.redenen,
        )
        self.assertEqual(
            resultaat.aanbevolen_vervolgstap,
            vertaal("eindstatus_vervolgstap.vervang_component"),
        )

    def test_out_of_range_heeft_voorrang_op_open_short_defectsignaal(self):
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
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=1.0,
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
            vermoedelijke_open_verbinding_of_kortsluiting=True,
            meetwaarde_buiten_bereik=True,
        )

        from app.helpers.i18n import vertaal

        self.assertEqual(resultaat.eindstatus, Eindstatus.NIET_TE_BEOORDELEN)
        self.assertEqual(
            resultaat.redenen,
            (vertaal("eindstatus_reden.buiten_bereik"),),
        )
        self.assertEqual(
            resultaat.aanbevolen_vervolgstap,
            vertaal("eindstatus_vervolgstap.controleer_meetbereik"),
        )
        self.assertIn(
            vertaal("veiligheid.buiten_bereik"),
            resultaat.waarschuwingen,
        )


class TestReferentiefrequentieInResultaat(unittest.TestCase):
    """Fase 10B: het Beoordeling-resultaat bewaart de gebruikte
    referentiefrequentie."""

    def _ref(self, freq_hz):
        return ReferentieContext(
            esr_waarde=400,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=5,
            frequentie_hz=freq_hz,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )

    def test_referentiefrequentie_aanwezig_bij_1khz(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=460,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.18,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(1000),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.referentiefrequentie_hz, 1000)

    def test_referentiefrequentie_aanwezig_bij_10khz(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=460,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.15,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=10000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(10000),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.referentiefrequentie_hz, 10000)

    def test_referentiefrequentie_none_zonder_referentie(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=460,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.18,
            eenheid_gemeten_esr="Ω",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=None,
            fabrikant_bekend=False,
            serie_bekend=False,
        )
        self.assertIsNone(resultaat.referentiefrequentie_hz)


class TestBeoordelingTaal(unittest.TestCase):
    """Fase 11D: het Beoordeling-object bewaart de taal."""

    def _ref(self):
        return ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=1,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )

    def _meting(self, taal):
        return beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=True,
            serie_bekend=True,
            taal=taal,
        )

    def test_taal_nl_nl_wordt_overgenomen(self):
        resultaat = self._meting("nl_NL")
        self.assertEqual(resultaat.taal, "nl_NL")

    def test_taal_en_us_wordt_overgenomen(self):
        resultaat = self._meting("en_US")
        self.assertEqual(resultaat.taal, "en_US")

    def test_default_taal_is_nl_nl(self):
        from app.helpers.i18n import STANDAARD_TAAL
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.taal, STANDAARD_TAAL)

    def test_en_us_bevat_engelse_toelichting(self):
        resultaat = self._meting("en_US")
        self.assertIn("Measured", resultaat.capaciteit.toelichting)

    def test_nl_nl_bevat_nederlandse_toelichting(self):
        resultaat = self._meting("nl_NL")
        self.assertIn("Gemeten", resultaat.capaciteit.toelichting)


# ============================================================================
# 4A — Nieuwe testsecties
# ============================================================================

class TestTypeFamilie(unittest.TestCase):
    """4A / B1-a en 4C: technologie-familie."""

    def test_alle_elektrolytische_varianten_zijn_familie(self):
        for type_ in (
            "Aluminium elektrolytisch",
            "Aluminium elektrolytisch — Low ESR",
            "Aluminium elektrolytisch — Bipolair/NP",
        ):
            with self.subTest(type_=type_):
                self.assertTrue(is_elektrolytisch_type(type_))

    def test_niet_elektrolytische_types_zijn_geen_familie(self):
        for type_ in (
            "Tantaal elektrolytisch",
            "Tantaal polymer",
            "Conductive polymer",
            "Hybrid polymer",
            "Film",
            "Keramisch / MLCC",
            "Supercondensator",
            "Onbekend",
            "Anders",
            "",
            None,
        ):
            with self.subTest(type_=type_):
                self.assertFalse(is_elektrolytisch_type(type_))

    def test_low_esr_krijgt_geen_type_verlager(self):
        r = bepaal_betrouwbaarheid(
            referentieniveau=5,
            referentiefrequentie_hz=1000,
            meetfrequentie_hz=1000,
            omgevingstemperatuur_c=20,
            condensatortype="Aluminium elektrolytisch — Low ESR",
            meetmethode=Meetmethode.EX_SITU,
            referentie_typisch_of_maximaal="maximaal",
            fabrikant_bekend=True,
            serie_bekend=True,
            consistentie_status=ConsistentieStatus.CONSISTENT,
        )
        self.assertEqual(r.niveau, Betrouwbaarheid.MIDDEL)
        self.assertEqual(r.verlagende_factoren, ())
        self.assertEqual(r.inhoudelijke_verlagers, ())

    def test_low_esr_met_standaard_referentie_is_geen_mismatch(self):
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=5,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch — Low ESR",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.esr.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)
        self.assertEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.MIDDEL)
        self.assertEqual(resultaat.betrouwbaarheid.inhoudelijke_verlagers, ())
        self.assertNotIn(
            "referentietype",
            " ".join(resultaat.waarschuwingen).lower(),
        )

    def test_tantaal_met_elektrolytische_referentie_is_wel_mismatch(self):
        from app.helpers.i18n import vertaal
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Aluminiumtabel",
            referentieniveau=5,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Tantaal elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=ref,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertEqual(resultaat.betrouwbaarheid.niveau, Betrouwbaarheid.LAAG)
        self.assertIn(
            vertaal("veiligheid.referentietype_wijkt_af"),
            resultaat.waarschuwingen,
        )

    def test_niet_elektrolytisch_type_voegt_waarschuwing_toe(self):
        """4C: bij een niet-elektrolytisch type voegt beoordeel_meting
        de waarschuwing veiligheid.geen_elektrolytische_referentie toe,
        zodat de gebruiker expliciet ziet dat de beoordeling zonder
        elektrolytische ESR-referentie is uitgevoerd."""
        from app.helpers.i18n import vertaal
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Tantaal elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=None,
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        self.assertIn(
            vertaal("veiligheid.geen_elektrolytische_referentie"),
            resultaat.waarschuwingen,
        )

    def test_elektrolytisch_type_voegt_geen_extra_waarschuwing_toe(self):
        """4C: bij een elektrolytisch type wordt de waarschuwing niet
        toegevoegd."""
        from app.helpers.i18n import vertaal
        ref = ReferentieContext(
            esr_waarde=100,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=5,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )
        resultaat = beoordeel_meting(
            nominale_capaciteit=100,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=100,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=80,
            eenheid_gemeten_esr="mΩ",
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
        self.assertNotIn(
            vertaal("veiligheid.geen_elektrolytische_referentie"),
            resultaat.waarschuwingen,
        )


class TestFysiekePlausibiliteit(unittest.TestCase):
    """4A / B2: fysiek onrealistische ESR en capaciteit."""

    def _ref(self):
        return ReferentieContext(
            esr_waarde=400,
            eenheid="mΩ",
            bron="Test",
            referentieniveau=5,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )

    def test_esr_onder_1_microohm_is_niet_te_beoordelen(self):
        r = beoordeel_esr(0.0005, "mΩ", 1000, self._ref())
        self.assertEqual(r.status, EsrStatus.NIET_TE_BEOORDELEN)
        self.assertIsNone(r.factor)
        self.assertAlmostEqual(r.gemeten_esr_ohm, 5e-7, places=12)

    def test_esr_van_100_microohm_wordt_nog_beoordeeld(self):
        r = beoordeel_esr(0.0999, "mΩ", 1000, self._ref())
        self.assertEqual(r.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)

    def test_esr_op_de_drempel_wordt_nog_beoordeeld(self):
        r = beoordeel_esr(1e-3, "mΩ", 1000, self._ref())
        self.assertEqual(r.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)

    def test_capaciteit_onder_1_picofarad_is_niet_beoordeelbaar(self):
        r = beoordeel_capaciteit(100, "µF", 0.5, "pF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.NIET_BEOORDEELBAAR)
        self.assertIsNone(r.afwijking_percent)

    def test_capaciteit_op_de_drempel_wordt_nog_beoordeeld(self):
        r = beoordeel_capaciteit(1, "pF", 1, "pF", 20)
        self.assertEqual(r.status, CapaciteitsStatus.BINNEN_TOLERANTIE)

    def test_onrealistische_esr_voegt_waarschuwing_toe_aan_beoordeling(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=470,
            eenheid_gemeten_capaciteit="µF",
            gemeten_esr=0.0005,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        from app.helpers.i18n import vertaal
        self.assertEqual(resultaat.esr.status, EsrStatus.NIET_TE_BEOORDELEN)
        self.assertIn(
            vertaal("veiligheid.esr_onrealistisch"),
            resultaat.waarschuwingen,
        )
        self.assertEqual(resultaat.eindstatus, Eindstatus.NIET_TE_BEOORDELEN)

    def test_onrealistische_capaciteit_voegt_waarschuwing_toe_aan_beoordeling(self):
        resultaat = beoordeel_meting(
            nominale_capaciteit=470,
            eenheid_nominaal="µF",
            tolerantie_percent=20,
            gemeten_capaciteit=0.5,
            eenheid_gemeten_capaciteit="pF",
            gemeten_esr=100,
            eenheid_gemeten_esr="mΩ",
            meetfrequentie_hz=1000,
            D=None,
            condensatortype="Aluminium elektrolytisch",
            meetmethode=Meetmethode.EX_SITU,
            omgevingstemperatuur_c=20,
            veiligheid_bevestigd=True,
            referentie=self._ref(),
            fabrikant_bekend=True,
            serie_bekend=True,
        )
        from app.helpers.i18n import vertaal
        self.assertEqual(
            resultaat.capaciteit.status,
            CapaciteitsStatus.NIET_BEOORDEELBAAR,
        )
        self.assertIn(
            vertaal("veiligheid.capaciteit_onrealistisch"),
            resultaat.waarschuwingen,
        )

    def test_drempels_zijn_configureerbaar(self):
        soepel = BeoordelingsInstellingen(esr_min_realistisch_ohm=0.0)
        r = beoordeel_esr(0.0005, "mΩ", 1000, self._ref(), instellingen=soepel)
        self.assertEqual(r.status, EsrStatus.WAARSCHIJNLIJK_NORMAAL)


if __name__ == "__main__":
    unittest.main()