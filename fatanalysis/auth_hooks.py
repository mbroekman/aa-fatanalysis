from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook
from django.utils.translation import gettext_lazy as _

from . import urls

class FatAnalysisMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""
    def __init__(self):
        # Setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _('FAT Analysis'),
            'fas fa-chart-line fa-fw',
            'fatanalysis:index',
            navactive=['fatanalysis:']
        )

    def render(self, request):
        if request.user.has_perm('fatanalysis.basic_access'):
            return MenuItemHook.render(self, request)
        return ''

@hooks.register('menu_item_hook')
def register_menu():
    return FatAnalysisMenuItem()

@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'fatanalysis', r'^fatanalysis/')
