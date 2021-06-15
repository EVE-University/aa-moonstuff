from unittest import mock
from datetime import datetime
from django.test import TestCase
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Token, Scope
from allianceauth.eveonline.models import EveCharacter
from eveuniverse.models import EveMoon, EvePlanet, EveSolarSystem, EveConstellation, EveType, EveGroup, EveCategory,\
    EveRegion


from ..tasks import filetime_to_dt, _get_tokens, _get_corp_tokens, process_scan
from ..models import TrackingCharacter, Resource
from .parser_strings import with_header


class TestTasks(TestCase):
    def setUp(self):
        self.expected_dt = datetime(1970, 1, 1)

        self.user1 = AuthUtils.create_user("Test User1")
        self.char1 = EveCharacter.objects.create(
            character_name="The First Char",
            character_id=1,
            corporation_name="The First Corp",
            corporation_id=123,
            corporation_ticker="ABC"
        )

        self.user1.profile.main_character = self.char1
        self.user1.profile.save()
        self.tracking1 = TrackingCharacter.objects.create(
            character=self.char1
        )
        self.token = Token.objects.create(
            access_token='access',
            refresh_token='refresh',
            user=self.user1,
            character_id=1,
            character_name='The First Char',
            token_type='Character',
            character_owner_hash='abcde',
        )
        scope, _ = Scope.objects.get_or_create(
            name="scope.v1"
        )
        self.token.scopes.add(scope)

        # EveUniverse Models
        EveCategory.objects.create(id=1, published=True)
        EveCategory.objects.create(id=2, published=True)
        EveGroup.objects.create(id=1884, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1921, published=True, eve_category_id=2)
        EveGroup.objects.create(id=1, published=True, eve_category_id=1)
        EveType.objects.create(id=1, published=True, eve_group_id=1)
        EveType.objects.create(id=45493, published=True, eve_group_id=1884)
        EveType.objects.create(id=45499, published=True, eve_group_id=1921)
        EveType.objects.create(id=45490, published=True, eve_group_id=1884)
        EveRegion.objects.create(id=1)
        EveConstellation.objects.create(id=1, eve_region_id=1)
        EveSolarSystem.objects.create(id=1, security_status=1, eve_constellation_id=1)
        EvePlanet.objects.create(id=1, eve_solar_system_id=1, eve_type_id=1)
        EveMoon.objects.create(id=40217116, eve_planet_id=1)

    def test_filetime_conversion(self):
        """
        Tests the function that converts filetime (LDAP time) to datetime
        :return:
        """
        ft = 116444736000000000
        dt = filetime_to_dt(ft)
        self.assertEqual(dt, self.expected_dt)

    def test_get_tokens(self):
        """
        Tests the _get_tokens function.
        :return:
        """
        tokens = _get_tokens(["scope.v1", ])
        self.assertEqual(tokens, [self.token, ])

    def test_get_corp_tokens(self):
        """
        Tests the _get_corp_tokens function.
        :return:
        """
        tokens = _get_corp_tokens(123, ["scope.v1", ])
        self.assertEqual(tokens, [self.token, ])

    def test_process_scan(self):
        """
        Tests the process_scan task.
        :return:
        """
        process_scan(with_header, 1)
        self.assertTrue(EveMoon.objects.get(id=40217116))
        self.assertTrue(len(Resource.objects.filter(moon__id=40217116)) == 3)
