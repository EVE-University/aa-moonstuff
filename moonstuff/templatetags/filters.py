from django.template.defaulttags import register

@register.filter()
def moon_rarity(resources):
    values = [resource.rarity for resource in resources]
    return max(values) if len(values) > 0 else 0
