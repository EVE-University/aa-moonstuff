import requests
import yaml
import datetime
import pytz

from allianceauth.services.hooks import get_extension_logger
from allianceauth.notifications import notify
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from celery import shared_task
from eveuniverse.tasks import update_or_create_eve_object
from eveuniverse.models import EveUniverseEntityModel, EveMarketPrice
from django.db.models import Q
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.utils.translation import gettext as gt
from esi.models import Token

from .providers import esi, ESI_CHARACTER_SCOPES
from .models import Material, MaterialCheckSum, EveType, Resource, EveMoon, TrackingCharacter, Refinery, Extraction
from .parser import ScanParser

logger = get_extension_logger(__name__)


def _get_tokens(scopes):
    try:
        tokens = list()
        characters = TrackingCharacter.objects.all()
        for character in characters:
            tokens.append(Token.get_token(character.character.character_id, scopes))
        return tokens
    except Exception as e:
        print(e)
        return False


@shared_task()
def load_types_and_mats(category_ids=None, group_ids=None, type_ids=None, force_loading_dogma=False):
    logger.debug(f'Calling eveuniverse load functions for the following args:'
                 f' cats: {category_ids}'
                 f' groups: {group_ids}'
                 f' types: {type_ids}'
                 f' dogma? {force_loading_dogma}')

    # Synchronously load SDE data to ensure it exists before we spawn the material loading task.
    # This is basically the logic for the _load_eve_xxx functions from eveuniverse thrown in here to force synchronicity
    if category_ids:
        for category_id in category_ids:
            enabled_sections = (
                [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
            )
            update_or_create_eve_object(
                model_name="EveCategory",
                id=category_id,
                include_children=True,
                wait_for_children=False,
                enabled_sections=enabled_sections,
            )

    if group_ids:
        for group_id in group_ids:
            enabled_sections = (
                [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
            )
            update_or_create_eve_object(
                model_name="EveGroup",
                id=group_id,
                include_children=True,
                wait_for_children=False,
                enabled_sections=enabled_sections,
            )

    if type_ids:
        for type_id in type_ids:
            enabled_sections = (
                [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
            )
            update_or_create_eve_object(
                model_name="EveType",
                id=type_id,
                include_children=False,
                wait_for_children=False,
                enabled_sections=enabled_sections,
            )

    logger.debug('Done loading eve types! Scheduling material loading.')
    # Any time types are loaded we should ensure we have material and price data for all types
    load_materials.delay(reload=True)
    load_prices.delay()


@shared_task()
def load_materials(reload=False):
    """
    Loads data from the invTypeMaterials SDE table provided by zzeve.
        Materials will only be loaded if either they have not been before, or
        there has been a change to the md5 checksum indicating updated data.
    :param reload: If set to true, checksum comparison will be bypassed.
    :return:
    """
    logger.debug('Starting material loading task.')
    last_sum = None

    # Get current sum
    current_sum = requests.get('http://sde.zzeve.com/installed.md5').text[0:-1]  # Remove the newline character

    # First check for previous checksum.
    if MaterialCheckSum.objects.exists() and not reload:
        last_sum = MaterialCheckSum.objects.get(pk=1)
        if last_sum.checksum == current_sum:
            logger.debug('No updates detected, aborting load_materials.')
            return

    # Clear current materials.
    Material.objects.all().delete()

    # Get existing types
    groups = (18, 423, 427)
    types = EveType.objects.filter(
            Q(eve_group_id__eve_category_id=25) |
            Q(eve_group_id__in=groups)
        ).values_list('id', flat=True)
    mats = requests.get("http://sde.zzeve.com/invTypeMaterials.json").json()
    mats = list(filter(lambda t: t['typeID'] in types, mats))   # Filter out unneeded materials from the list

    mat_objs = list()
    for mat in mats:
        mat_objs.append(
            Material(
                evetype_id=mat['typeID'],
                material_evetype_id=mat['materialTypeID'],
                quantity=mat['quantity']
            )
        )

    Material.objects.bulk_create(mat_objs)

    logger.info('Material data successfully loaded.')

    # Update the checksum record.
    if MaterialCheckSum.objects.exists():
        if not last_sum:
            last_sum = MaterialCheckSum.objects.get(pk=1)
    else:
        last_sum = MaterialCheckSum(pk=1)
    last_sum.checksum = current_sum
    last_sum.save()


@shared_task()
def process_scan(scan_data: str, user_id: int):
    """
    Runs the provided scan data through the parser, and creates the required resource objects.
    :param scan_data: The raw scan data from the view.
    :param user_id: The user that initiated the scan.
    :return:
    """
    logger.debug('Processing moon scan.')
    try:
        data = ScanParser(scan_data).parse()

        resources = list()

        for moon in data:
            moon, created = EveMoon.objects.get_or_create_esi(id=int(moon))
            if not created:
                Resource.objects.filter(moon=moon).delete()

        for res_l in data.values():
            for res in res_l:
                resources.append(Resource(**res))

        Resource.objects.bulk_create(resources)
        logger.debug("Successfully processed moon scan!")
    except Exception as e:
        logger.error(f'Failed processing moon scan! (Data sent to user_id {user_id} via notification)')
        notify(
            User.objects.get(id=user_id),
            gt('Failed to Process Moon Scan'),
            message=gt('There was an error processing the following moon scan:\n'
                       '%(scan)s'
                       '\n\n'
                       'Error Encountered: %(error)s\n') % {'scan': scan_data, 'error': e},
            level='danger'
        )


@shared_task()
def load_prices():
    """
    Updates EveMarketPrice records.
    :return:
    """
    EveMarketPrice.objects.update_from_esi()


@shared_task()
def import_extraction_data():
    """
    Imports extraction data, and schedules notification checks.
    :return:
    """
    client = esi.client
    tokens = _get_tokens(ESI_CHARACTER_SCOPES)
    for token in tokens:
        try:
            # Get character and corp objects to go with token
            char = EveCharacter.objects.get(character_id=token.character_id)
            try:
                corp = EveCorporationInfo.objects.get(corporation_id=char.corporation_id)
            except EveCorporationInfo.DoesNotExist:
                corp = EveCorporationInfo.objects.create_corporation(corp_id=char.corporation_id)

            # Get Extraction events.
            events = client.Industry.get_corporation_corporation_id_mining_extractions(
                corporation_id=corp.corporation_id,
                token=token.valid_access_token()
            ).results()

            for event in events:
                # Get Structure Info
                moon, _ = EveMoon.objects.get_or_create_esi(id=event['moon_id'])
                try:
                    refinery = Refinery.objects.get(structure_id=event['structure_id'])
                except Refinery.DoesNotExist:
                    ref = client.Universe.get_universe_structures_structure_id(
                        structure_id=event['structure_id'],
                        token=token.valid_access_token()
                    ).results()
                    refinery = Refinery(
                        structure_id=event['structure_id'],
                        name=ref['name'],
                        corp=corp,
                        evetype_id=ref['type_id']
                    )
                    refinery.save()

                start_time = event['extraction_start_time']
                arrival_time = event['chunk_arrival_time']
                decay_time = event['natural_decay_time']
                try:
                    # Create the extraction event.
                    extraction = Extraction.objects.get_or_create(
                        start_time=start_time,
                        arrival_time=arrival_time,
                        decay_time=decay_time,
                        refinery=refinery,
                        moon=moon,
                        corp=corp
                    )
                except IntegrityError:
                    continue
                except Exception as e:
                    logger.error(f'Error encountered when saving extraction! Corp ID: {corp.corporation_id}'
                                 f' Refinery ID: {refinery.structure_id} Event Start: {start_time}')
                    logger.error(e)
            logger.info(f'Imported extraction data from {token.character_id}')
        except Exception as e:
            logger.error(f'Error importing extraction data from {token.character_id}')
            logger.error(e)

        check_notifications.delay(token.character_id)


@shared_task()
def check_notifications(character_id: int):
    """
    Checks and processes notifications related to moon mining.
        Note: This task does not add extraction events!
    :param character_id: The character_id to use to get a token.
    :return:
    """
    logger.debug(f'Checking notifications for {character_id}')
    # Define token and client, ensuring the token is valid.
    client = esi.client
    token = Token.get_token(character_id, ESI_CHARACTER_SCOPES)
    char = EveCharacter.objects.get(character_id=token.character_id)
    char = TrackingCharacter.objects.get(character=char)
    last_noti = char.latest_notification_id

    # Get notifications
    notifications = client.Character.get_characters_character_id_notifications(
        character_id=char.character.character_id,
        token=token.valid_access_token()
    ).results()
    # Set the last notification id for the character
    char.latest_notification_id = notifications[0]['notification_id']
    char.save()

    # Filter out notifications that we dont care about
    notifications = list(
        filter(
            lambda n: 'Moonmining' in n['type'] and int(n['notification_id']) > last_noti,
            notifications
        )
    )

    # Start processing notifications
    for noti in notifications:
        if 'Cancelled' not in noti['type']:
            # First parse the text from yaml format.
            data = yaml.safe_load(noti['text'])

            # Check that the moon has resources associated with it.
            # (If a scan was never added, it might not)
            moon = EveMoon.objects.get(id=data['moonID'])
            res = moon.resources.all().values_list('ore_id', flat=True)
            missing_res = list()

            # Make a list of resources missing from the moon.
            # This is used in case the data is either incorrect or incomplete.
            for ore in data['oreVolumeByType']:
                if ore not in res:
                    missing_res.append(ore)

            # If there is one or more missing resources, OR if there is a resource in the database
            # that shouldn't be there. We will assume that these notifications are always authoritative.
            if len(missing_res) > len(res) or len(missing_res) == len(data['oreVolumeByType']):
                # Calculate ore percentages, and add resource objects for the moon.
                total_ore = 0
                for k, v in data['oreVolumeByType'].items():
                    total_ore += v
                # Create resource objects
                new_res = list()
                for k, v in data['oreVolumeByType'].items():
                    pct = v / total_ore
                    new_res.append(
                        Resource(moon=moon, ore_id=k, quantity=pct)
                    )

                # Delete old moon resources and create new ones.
                moon.resources.all().delete()
                Resource.objects.bulk_create(new_res)

        elif 'Cancelled' in noti['type']:
            # Determine which extraction event was cancelled and mark it as such.
            # First Parse the timestamp
            noti_time = datetime.datetime.strptime(noti['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            noti_time = pytz.timezone("UTC").localize(noti_time, is_dst=None)

            # Parse the notification data from yaml
            data = yaml.load(noti['text'])

            # Get the refinery and list of extractions
            try:
                refinery = Refinery.objects.get(structure_id=data['structureID'])
            except Refinery.DoesNotExist:
                logger.info(f'Got extraction cancellation notification for refinery not in database. '
                            f'NID {noti["notification_id"]}')
                continue

            exts = refinery.extractions.filter(start_time__lt=noti_time, arrival_time__gt=noti_time)\
                .order_by('-start_time')

            # Cancel the extraction(s).
            if len(exts) == 1:
                exts[0].cancelled = True
                exts[0].save()
            elif len(exts) > 1:
                for ext in exts:
                    if ext.cancelled is not True:
                        ext.cancelled = True
                        ext.save()
            else:
                logger.info(f'Got extraction cancellation notification for event not in database. '
                            f'NID {noti["notification_id"]}')
