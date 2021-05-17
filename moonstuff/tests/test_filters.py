import pytz
from unittest import mock
from datetime import datetime, timedelta
from django.test import TestCase
from allianceauth.eveonline.models import EveCorporationInfo
from eveuniverse.models import EveType, EveMoon, EveGroup, EveCategory, EveSolarSystem, EvePlanet, EveConstellation, EveRegion

from moonstuff.templatetags import filters
from ..models import Resource, Refinery, Extraction


class TestFilters(TestCase):
    def setUp(self):
        # Moon and Resource Data
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
        EvePlanet.objects.create(id=2, eve_solar_system_id=1, eve_type_id=6)
        self.moon = EveMoon.objects.create(id=1, eve_planet_id=1)
        self.moon2 = EveMoon.objects.create(id=2, eve_planet_id=2)
        self.moon3 = EveMoon.objects.create(id=3, eve_planet_id=2)

        self.rs1 = Resource.objects.create(
            ore_id=1,
            quantity=0.234445456,
            moon_id=1
        )
        self.rs2 = Resource.objects.create(
            ore_id=2,
            quantity=0.1945375,
            moon_id=1
        )
        self.rs3 = Resource.objects.create(
            ore_id=3,
            quantity=0.1866783,
            moon_id=1
        )
        self.rs4 = Resource.objects.create(
            ore_id=4,
            quantity=0.15992839,
            moon_id=1
        )
        self.rs5 = Resource.objects.create(
            ore_id=5,
            quantity=0.168848493,
            moon_id=1
        )
        self.rs6 = Resource.objects.create(
            ore_id=6,
            quantity=0.00003,
            moon_id=1
        )

        self.order = [self.rs1, self.rs2, self.rs3, self.rs5, self.rs4, self.rs6]

        # Refinery Data
        EveCategory.objects.create(id=10, published=True)
        EveGroup.objects.create(id=10, published=True, eve_category_id=10)
        EveType.objects.create(id=10, published=True, eve_group_id=10, name="Type")
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
            name="Test Structure",
            corp_id=1
        )

        # Extraction Data
        # True
        self.ex1 = Extraction.objects.create(
            start_time=datetime(1970, 1, 1),
            arrival_time=datetime(1970, 1, 2),
            decay_time=datetime(1970, 1, 3),
            moon_id=1,
            refinery_id=1,
            corp_id=1,
            active=False
        )

        # False
        self.ex2 = Extraction.objects.create(
            start_time=datetime(1970, 1, 2).replace(tzinfo=pytz.utc),
            arrival_time=datetime(1970, 1, 3).replace(tzinfo=pytz.utc),
            decay_time=datetime(1970, 1, 4).replace(tzinfo=pytz.utc),
            moon_id=1,
            refinery_id=1,
            corp_id=1,
            active=True
        )

        # True
        self.ex3 = Extraction.objects.create(
            start_time=datetime.utcnow().replace(tzinfo=pytz.utc),
            arrival_time=datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=1),
            decay_time=datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=2),
            moon_id=1,
            refinery_id=1,
            corp_id=1,
            depleted=True
        )

        # False
        self.ex4 = Extraction.objects.create(
            start_time=datetime.utcnow().replace(tzinfo=pytz.utc),
            arrival_time=datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=2),
            decay_time=datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=3),
            moon_id=1,
            refinery_id=1,
            corp_id=1,
            active=False
        )

        self.ex1 = Extraction.objects.create(
            start_time=datetime(1970, 1, 1),
            arrival_time=datetime(1970, 1, 2),
            decay_time=datetime(1970, 1, 3),
            moon_id=3,
            refinery_id=2,
            corp_id=1,
            active=False
        )

    def test_get_refinery_name(self):
        """
        Test the get_refinery_name filter.
        :return:
        """
        name = filters.get_refinery_name(self.moon)
        name2 = filters.get_refinery_name(self.moon2)
        self.assertEqual("Test Structure", name)
        self.assertEqual("", name2)

    def test_get_refinery_owner_name(self):
        """
        Test the get_refinery_owner_name filter.
        :return:
        """
        name = filters.get_refinery_owner_name(self.moon)
        name2 = filters.get_refinery_owner_name(self.moon2)
        self.assertEqual("Test", name)
        self.assertEqual("", name2)

    def test_get_refinery_owner_id(self):
        """
        Test the get_refinery_owner_id filter
        :return:
        """
        corp_id = filters.get_refinery_owner_id(self.moon)
        corp_id2 = filters.get_refinery_owner_id(self.moon2)
        self.assertEqual(123, corp_id)
        self.assertEqual('', corp_id2)

    def test_get_next_extraction(self):
        """
        Test the get_next_extraction filter
        :return:
        """
        ext = filters.get_next_extraction(self.moon)
        ext2 = filters.get_next_extraction(self.moon2)
        ext3 = filters.get_next_extraction(self.moon3)
        self.assertEqual(ext, datetime.strftime(self.ex4.arrival_time, '%Y-%m-%d %H:%M'))
        self.assertEqual(ext2, '')
        self.assertEqual(ext3, '')

    def test_check_visibility(self):
        """
        Test the check_visibility filter.
        :return:
        """
        self.assertTrue(filters.check_visibility(self.ex1))
        self.assertFalse(filters.check_visibility(self.ex2))
        self.assertTrue(filters.check_visibility(self.ex3))
        self.assertFalse(filters.check_visibility(self.ex4))

    def test_card_labels(self):
        """
        Test the card_labels filter.
        :return:
        """
        labels = filters.card_labels(self.moon.resources.all())
        self.assertEqual(labels, [64, 32, 16, 8, 4, 0])

    def test_chunk_time(self):
        """
        Test the chunk_time filter.
        :return:
        """
        time = filters.chunk_time(self.ex4)
        self.assertEqual(2, time)

    def test_percent(self):
        """
        Test the percent filter.
        :return:
        """
        pct = filters.percent(0.25)
        self.assertEqual(pct, 25)

    def test_order_quantity(self):
        """
        Test the order_quantity filter.
        :return:
        """
        res = filters.order_quantity(self.moon.resources.all())
        self.assertEqual(res, self.order)

    def test_get_item(self):
        """
        Test the get_item filter.
        :return:
        """
        dct = {'a': 32, 'b': 9}
        a = filters.get_item(dct, 'a')
        n = filters.get_item(dct, 'c')
        self.assertEqual(a, 32)
        self.assertEqual(n, None)

