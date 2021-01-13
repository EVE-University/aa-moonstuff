from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as gt
from django.conf import settings

from allianceauth.authentication.decorators import permissions_required
from esi.decorators import token_required
from .tasks import process_scan
from .models import Resource

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


# Create your views here.
@login_required
@permission_required('moonstuff.access_moonstuff')
def dashboard(request):
    return render(request, 'moonstuff/base.html')


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
@permission_required('moonstuff.add_trackingcharacter')
def add_character(request):
    pass