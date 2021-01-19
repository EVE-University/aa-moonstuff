from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as gt
from django.conf import settings

from esi.decorators import token_required
from allianceauth.eveonline.models import EveCharacter

from .tasks import process_scan
from .models import Resource, TrackingCharacter, Extraction, EveMoon
from .providers import ESI_CHARACTER_SCOPES

# Get refine setting
refine = .876
if hasattr(settings, 'MOON_REFINE_PERCENT'):
    if settings.MOON_REFINE_PERCENT > 1:
        refine = settings.MOON_REFINE_PERCENT / 100
    else:
        refine = settings.MOON_REFINE_PERCENT


def _get_moon_value_dict(moon_id: int) -> dict:
    """
    Returns a dict containing the per-m3 values of the moon's resources
    :param moon_id: The id of the moon.
    :return:
    """
    resources = Resource.objects\
        .prefetch_related('ore', 'ore__materials', 'ore__materials__material_evetype__market_price')\
        .filter(moon__id=moon_id)

    ret = dict()

    for resource in resources:
        value = 0
        mats = resource.ore.materials.all()
        for mat in mats:
            ore_volume = resource.ore.volume
            amount = mat.quantity
            mat_value = mat.material_evetype.market_price.average_price
            value += (((amount / 100) * refine) * mat_value) / ore_volume
        ret[resource.ore.id] = value

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
                    arrival_time__lte=datetime.utcnow()+timedelta(days=limit))\
            .prefetch_related('moon__resources', 'moon__resources__ore', 'refinery')
    else:
        qs = Extraction.objects.select_related('moon')\
            .filter(arrival_time__gte=datetime.utcnow().replace(day=1))\
            .prefetch_related('moon__resources', 'moon__resources__ore', 'refinery')

    return qs


def _build_event_dict(qs):
    ret = [
        {"title": q.refinery.name,
         "start": datetime.strftime(q.arrival_time, '%Y-%m-%dT%H:%M:%S%z'),
         "moon": q.moon.name,
         "rarity": [r.rarity for r in q.moon.resources.all()]}
        for q in qs
    ]

    return ret


# Create your views here.
@login_required
@permission_required('moonstuff.access_moonstuff')
def dashboard(request):
    ctx = dict()

    # Get upcoming extraction events (calendar)
    extractions = _get_extractions()
    events = _build_event_dict(extractions)

    # Get moons
    moons = EveMoon.objects.filter(resources__isnull=False).distinct()\
        .prefetch_related('resources', 'resources__ore', 'extractions', 'extractions__refinery')

    ctx['events'] = events
    ctx['extractions'] = extractions
    ctx['moons'] = moons
    return render(request, 'moonstuff/dashboard.html', ctx)


@login_required
@permission_required('moonstuff.add_resource')
def add_scan(request):
    """
    View for adding moon scan data.
    :param request:
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
    messages.success(request, 'Character added!')
    eve_char = EveCharacter.objects.get(character_id=token.character_id)
    char = TrackingCharacter(character=eve_char)
    char.save()
    return redirect('moonstuff:dashboard')
