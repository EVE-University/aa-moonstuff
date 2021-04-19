from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from typing import Iterable
from django.contrib import messages
from django.utils.translation import gettext as gt
from django.conf import settings

from esi.decorators import token_required
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from .tasks import process_scan, import_extraction_data
from .models import Resource, TrackingCharacter, Extraction, EveMoon
from .providers import ESI_CHARACTER_SCOPES

logger = get_extension_logger(__name__)

# Get refine setting
refine = .876
if hasattr(settings, 'MOON_REFINE_PERCENT'):
    if settings.MOON_REFINE_PERCENT > 1:
        refine = settings.MOON_REFINE_PERCENT / 100
    else:
        refine = settings.MOON_REFINE_PERCENT

# Get Default Extraction View setting
extraction_view = "Calendar"
if hasattr(settings, "DEFAULT_EXTRACTION_VIEW"):
    extraction_view = settings.DEFAULT_EXTRACTION_VIEW


def _get_resource_values(resources: Iterable[Resource]) -> dict:
    """
    Returns a dict containing the per-m3 values for a given list of resources.
    :param resources:
    :return:
    """
    ret = dict()

    for resource in resources:
        value = 0
        mats = resource.ore.materials.all()
        for mat in mats:
            ore_volume = resource.ore.volume
            amount = mat.quantity
            mat_value = mat.material_eve_type.market_price.average_price
            value += (((amount / 100) * refine) * mat_value) / ore_volume
        ret[resource.ore.id] = value

    return ret


def _get_moon_value_dict(moon_id: int) -> dict:
    """
    Returns a dict containing the per-m3 values of the moon's resources
    :param moon_id: The id of the moon.
    :return:
    """
    resources = Resource.objects\
        .prefetch_related('ore', 'ore__materials', 'ore__materials__material_eve_type__market_price')\
        .filter(moon__id=moon_id)

    ret = _get_resource_values(resources)

    return ret


def _get_extractions(limit=None):
    """
    Gets a dict of extractions from beginning of the current.
    :param limit: Number of days out to go. (Default: None - Will grab ALL extractions)
    :return:
    """
    if limit:
        qs = Extraction.objects.select_related('moon')\
            .filter(arrival_time__gte=datetime.utcnow().replace(day=1),
                    arrival_time__lte=datetime.utcnow()+timedelta(days=limit),
                    cancelled=False)\
            .prefetch_related('moon__resources', 'moon__resources__ore', 'refinery')\
            .order_by('arrival_time')
    else:
        qs = Extraction.objects.select_related('moon')\
            .filter(arrival_time__gte=datetime.utcnow().replace(day=1),
                    cancelled=False)\
            .prefetch_related('moon__resources', 'moon__resources__ore', 'refinery')\
            .order_by('arrival_time')

    return qs


def _build_event_dict(qs):
    ret = [
        {"title": q.refinery.name,
         "start": datetime.strftime(q.arrival_time, '%Y-%m-%dT%H:%M:%S%z'),
         "moon": q.moon.name,
         "rarity": [r.rarity for r in q.moon.resources.all()],
         "moon_id": q.moon.id}
        for q in qs
    ]

    return ret


# Create your views here.
@login_required
@permission_required('moonstuff.access_moonstuff')
def dashboard(request):
    """
    The main view for moonstuff.
    :param request: HTTPRequest object
    :return:
    """
    ctx = dict()

    # Get upcoming extraction events (calendar)
    extractions = _get_extractions()
    events = _build_event_dict(extractions)

    # Get moons
    moons = EveMoon.objects.filter(resources__isnull=False).distinct()\
        .prefetch_related('resources',
                          'resources__ore',
                          'resources__ore__materials',
                          'resources__ore__materials__material_eve_type__market_price',
                          'extractions',
                          'extractions__refinery',
                          'extractions__refinery__corp',
                          'eve_planet',
                          'eve_planet__eve_solar_system',
                          'eve_planet__eve_solar_system__eve_constellation__eve_region',
                          )

    resources = tuple(set(res for moon in moons for res in moon.resources.all()))
    ctx['events'] = events
    ctx['extractions'] = extractions
    ctx['moons'] = moons
    ctx['resources'] = _get_resource_values(resources)
    ctx['default_view'] = extraction_view
    return render(request, 'moonstuff/dashboard.html', ctx)


@login_required
@permission_required('moonstuff.add_resource')
def add_scan(request):
    """
    View for adding moon scan data.
    :param request: HTTPRequest object
    :return:
    """
    if request.method == 'POST':
        scan_data = request.POST['scan']

        process_scan.delay(scan_data, request.user.id)
        messages.success(request, gt('Your moon scan is being processed. Depending on size this may take some time.'))
        return redirect('moonstuff:dashboard')

    return render(request, 'moonstuff/add_scan.html')


@login_required
@token_required(scopes=ESI_CHARACTER_SCOPES)
@permission_required('moonstuff.add_trackingcharacter')
def add_character(request, token):
    """
    View for adding tracking character and corresponding token.
    :param request: HTTPRequest object
    :param token: django-esi Token object
    :return:
    """
    messages.success(request, 'Character added!')
    eve_char = EveCharacter.objects.get(character_id=token.character_id)
    char = TrackingCharacter(character=eve_char)
    char.save()

    # Schedule an import task to pull data from the new Tracking Character.
    import_extraction_data.delay()

    return redirect('moonstuff:dashboard')


@login_required
@permission_required('moonstuff.access_moonstuff')
def moon_info(request, moon_id=None):
    """
    View for viewing a moon's data.
    :param request: HTTPRequest object
    :param moon_id: integer
    :return:
    """
    ctx = {}
    if moon_id is None:
        messages.error(request, gt("Please provide the ID of a moon to view it's data."))
        return redirect('moonstuff:dashboard')

    # Get moon
    try:
        moon = EveMoon.objects.filter(id=moon_id, resources__isnull=False)\
            .prefetch_related('extractions',
                              'extractions__refinery',
                              'resources',
                              'resources__ore',
                              )[0]
        ctx['resources'] = _get_moon_value_dict(moon_id)
        ctx['moon'] = moon
    except EveMoon.DoesNotExist:
        messages.error(request, gt('A moon matching the provided ID could not be found.'))
        return redirect('moonstuff:dashboard')

    if request.is_ajax():
        return render(request, 'moonstuff/moon_info_ajax.html', ctx)
    return render(request, 'moonstuff/moon_info.html', ctx)
