from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls


class MoonstuffMenu(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(self,
                              'Moon Tools',
                              'fas fa-moon',
                              'moonstuff:dashboard',
                              navactive=['moonstuff:'])

    def render(self, request):
        if request.user.has_perm('moonstuff.access_moonstuff'):
            return MenuItemHook.render(self, request)
        return ''


@hooks.register('menu_item_hook')
def register_menu():
    return MoonstuffMenu()


@hooks.register('url_hook')
def register_url():
    return UrlHook(urls, 'moonstuff', '^moons/')
