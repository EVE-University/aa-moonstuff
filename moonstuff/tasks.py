import requests

from allianceauth.services.hooks import get_extension_logger
from celery import shared_task
from eveuniverse.tasks import update_or_create_eve_object
from eveuniverse.models import EveUniverseEntityModel
from django.db.models import Q

from .models import Material, MaterialCheckSum, EveType


logger = get_extension_logger(__name__)


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
    # Any time types are loaded we should ensure we have material data for all types
    load_materials.delay(reload=True)


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
    logger.debug(types)
    mats = requests.get("http://sde.zzeve.com/invTypeMaterials.json").json()
    mats = list(filter(lambda t: t['typeID'] in types, mats))   # Filter out unneeded materials from the list
    logger.debug(f"mats filtered {len(mats)}")

    matObjs = list()
    for mat in mats:
            matObjs.append(
                Material(
                    evetype_id=mat['typeID'],
                    material_evetype_id=mat['materialTypeID'],
                    quantity=mat['quantity']
                )
            )

    Material.objects.bulk_create(matObjs)

    logger.info('Material data successfully loaded.')

    # Update the checksum record.
    if MaterialCheckSum.objects.exists():
        if not last_sum:
            last_sum = MaterialCheckSum.objects.get(pk=1)
    else:
        last_sum = MaterialCheckSum(pk=1)
    last_sum.checksum = current_sum
    last_sum.save()
