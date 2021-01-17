from django.template.defaulttags import register
from django.utils import timezone
from datetime import datetime


@register.filter()
def get_refinery_name(moon):
    exts = moon.extractions.all()
    if len(exts) is 0:
        return ''
    refinery = list(exts)[-1].refinery
    return refinery.name


@register.filter()
def get_next_extraction(moon):
    exts = list(moon.extractions.all())
    if len(exts) is 0:
        return ''
    ext_arrival = exts[-1].arrival_time
    now = timezone.now()
    if ext_arrival > now:
        return datetime.strftime(exts[-1].arrival_time, '%Y-%m-%d %H:%M')
    return ''
