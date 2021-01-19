from django.template.defaulttags import register
from django.utils import timezone
from datetime import datetime, timedelta


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


@register.filter()
def card_labels(resources):
    rare_values = set([r.rarity for r in resources])
    return sorted(list(rare_values), reverse=True)


@register.filter()
def chunk_time(extraction):
    """
    Returns the number of days that the extraction will take.
    :param extraction: Extraction model object.
    :return:
    """
    start = extraction.start_time
    end = extraction.arrival_time

    delta = end - start
    return delta.days


@register.filter()
def destruct_time(extraction):
    """
    Returns the self-destruct time for the extraction.
    :param extraction: Extraction model object.
    :return:
    """
    return extraction.arrival_time+timedelta(hours=3)


@register.filter()
def percent(quantity: float):
    """
    Converts decimal to percent.
    :param quantity: float
    :return:
    """
    return round(quantity * 100, 1)


@register.filter()
def order_quantity(resources):
    """
    Returns a list of resources ordered by quantity.
    :param resources: QS containing the resources.
    :return:
    """
    return sorted(list(resources), key=lambda r: r.quantity, reverse=True)
