from unittest import mock
from django.test import TestCase
from django.db.utils import IntegrityError
from eveuniverse.models import EveMoon, EvePlanet, EveSolarSystem, EveConstellation, EveType, EveGroup, EveCategory,\
    EveRegion
from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter
from datetime import datetime

from ..models import Resource, Refinery, TrackingCharacter, Extraction, LedgerEntry


class TestResource(TestCase):
    def setUp(self):
        EveCategory.objects.create(id=1, published=True)
        EveCategory.objects.create(id=2, published=True)
        EveGroup.objects.create(id=1884, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1920, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1921, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1922, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1923, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1, published=True, eve_category_id=1)
        EveType.objects.create(id=1, published=True, eve_group_id=1884)
        EveType.objects.create(id=2, published=True, eve_group_id=1920)
        EveType.objects.create(id=3, published=True, eve_group_id=1921)
        EveType.objects.create(id=4, published=True, eve_group_id=1922)
        EveType.objects.create(id=5, published=True, eve_group_id=1923)
        EveType.objects.create(id=6, published=True, eve_group_id=1)
        EveRegion.objects.create(id=1)
        EveConstellation.objects.create(id=1, eve_region_id=1)
        EveSolarSystem.objects.create(id=1, security_status=1, eve_constellation_id=1)
        EvePlanet.objects.create(id=1, eve_solar_system_id=1, eve_type_id=6)
        EveMoon.objects.create(id=1, eve_planet_id=1)

        Resource.objects.create(
            ore_id=1,
            quantity=0.234445456,
            moon_id=1
        )
        Resource.objects.create(
            ore_id=2,
            quantity=0.1945375,
            moon_id=1
        )
        Resource.objects.create(
            ore_id=3,
            quantity=0.1866783,
            moon_id=1
        )
        Resource.objects.create(
            ore_id=4,
            quantity=0.15992839,
            moon_id=1
        )
        Resource.objects.create(
            ore_id=5,
            quantity=0.168848493,
            moon_id=1
        )
        Resource.objects.create(
            ore_id=6,
            quantity=0.00003,
            moon_id=1
        )

    def test_rarity(self):
        res = Resource.objects.filter(moon_id=1)
        self.assertTrue(len(res) == 6)
        self.assertEqual(res[0].rarity, 4)
        self.assertEqual(res[1].rarity, 8)
        self.assertEqual(res[2].rarity, 16)
        self.assertEqual(res[3].rarity, 32)
        self.assertEqual(res[4].rarity, 64)
        self.assertEqual(res[5].rarity, 0)


class TestRefinery(TestCase):
    def setUp(self):
        EveCategory.objects.create(id=1, published=True)
        EveGroup.objects.create(id=1, published=True, eve_category_id=1)
        EveType.objects.create(id=1, published=True, eve_group_id=1, name="Type")
        EveCorporationInfo.objects.create(corporation_name="Test",
                                          corporation_ticker="ABC",
                                          corporation_id=123,
                                          member_count=1
                                          )

        self.r1 = Refinery.objects.create(
            structure_id=1,
            evetype_id=1,
            name="Test Structure",
            corp_id=1
        )
        self.r2 = Refinery.objects.create(
            structure_id=2,
            evetype_id=1,
            corp_id=1
        )

    def test_str_with_name(self):
        """
        Test __str__ method
        :return:
        """
        self.assertEqual(self.r1.__str__(), "Test Structure")

    def test_str_with_missing_name(self):
        """
        Test the __str__ method on an object missing a name.
        :return:
        """
        self.assertEqual(self.r2.__str__(), "Unknown Structure ID2 (Type)")


class TestTrackingCharacter(TestCase):
    def setUp(self):
        self.character = EveCharacter.objects.create(
            character_id=1,
            character_name="Test Character",
            corporation_id=123,
            corporation_name="Test Corp",
            corporation_ticker="ABC"
        )

        self.tracker = TrackingCharacter.objects.create(
            character=self.character
        )

    def test_str(self):
        """
        Test the __str__ method
        :return:
        """
        self.assertEqual(self.tracker.__str__(), "Test Character")

    def test_only_one_trackingcharacter_per_character(self):
        """
        Test the OtO relationship between EveCharacter and TrackingCharacter.
        :return:
        """
        self.assertRaises(IntegrityError, TrackingCharacter.objects.create, character=self.character)


class TestExtraction(TestCase):
    def setUp(self):
        EveCategory.objects.create(id=1, published=True)
        EveCategory.objects.create(id=2, published=True)
        EveGroup.objects.create(id=1, published=True, eve_category_id=1)
        EveGroup.objects.create(id=2, published=True, eve_category_id=1)
        EveType.objects.create(id=1, published=True, eve_group_id=1)
        EveType.objects.create(id=2, published=True, eve_group_id=1, name="Type")
        EveRegion.objects.create(id=1)
        EveConstellation.objects.create(id=1, eve_region_id=1)
        EveSolarSystem.objects.create(id=1, security_status=1, eve_constellation_id=1)
        EvePlanet.objects.create(id=1, eve_solar_system_id=1, eve_type_id=1)
        EveMoon.objects.create(id=1, eve_planet_id=1)

        EveCorporationInfo.objects.create(corporation_name="Test",
                                          corporation_ticker="ABC",
                                          corporation_id=123,
                                          member_count=1
                                          )

        self.r1 = Refinery.objects.create(
            structure_id=1,
            evetype_id=2,
            name="Test Structure",
            corp_id=1
        )

        self.extraction_values = {
            'start_time': datetime(1970, 1, 1),
            'arrival_time': datetime(1970, 1, 2),
            'decay_time': datetime(1970, 1, 3),
            'moon_id': 1,
            'refinery_id': 1,
            'corp_id': 1
        }

        self.extraction = Extraction.objects.create(
            **self.extraction_values
        )

    def test_despawn_property(self):
        """
        Test the despawn property of the Extraction class.
        :return:
        """
        self.assertEqual(self.extraction.despawn, datetime(1970, 1, 5))

    def test_unique_start_and_moon(self):
        """
        Test the unique_together condition
        :return:
        """
        self.assertRaises(IntegrityError, Extraction.objects.create, **self.extraction_values)


class TestLedgerEntry(TestCase):
    def setUp(self):
        EveCategory.objects.create(id=1, published=True)
        EveCategory.objects.create(id=2, published=True)
        EveGroup.objects.create(id=1, published=True, eve_category_id=1)
        EveGroup.objects.create(id=2, published=True, eve_category_id=2)
        EveType.objects.create(id=1, published=True, eve_group_id=1, name="Type")
        EveType.objects.create(id=2, published=True, eve_group_id=2, name="Non-Refinery Type")
        EveCorporationInfo.objects.create(corporation_name="Test",
                                          corporation_ticker="ABC",
                                          corporation_id=123,
                                          member_count=1
                                          )

        self.r1 = Refinery.objects.create(
            structure_id=1,
            evetype_id=1,
            name="Test Structure",
            corp_id=1
        )

        self.ledger_entry_values = {
            'observer': self.r1,
            'character_id': 1,
            'last_updated': datetime(1970, 1, 1),
            'quantity': 123456789,
            'recorded_corporation_id': 1,
            'evetype_id': 2
        }

        LedgerEntry.objects.create(**self.ledger_entry_values)

    def test_unique_together(self):
        """
        Test the unique_together condition
        :return:
        """
        self.assertRaises(IntegrityError, LedgerEntry.objects.create, **self.ledger_entry_values)
