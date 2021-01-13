from esi.clients import EsiClientProvider

from . import __version__

ESI_CHARACTER_SCOPES = (
    'esi-industry.read_corporation_mining.v1',
    'esi-universe.read_structures.v1',
    'esi-characters.read_notifications.v1',
    )

esi = EsiClientProvider(app_info_text="moonstuff v" + __version__)
