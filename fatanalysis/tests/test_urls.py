from allianceauth import views as aa_views
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("fatanalysis/", include("fatanalysis.urls")),
    path("account/login/", lambda r: HttpResponse("login"), name="login"),
    path("account/logout/", lambda r: HttpResponse("logout"), name="logout"),
    path("notifications/", include("allianceauth.notifications.urls")),
    path("authentication/", include("allianceauth.authentication.urls")),
    path("groupmanagement/", include("allianceauth.groupmanagement.urls")),
    path("theme/", aa_views.ThemeRedirectView.as_view(), name="theme"),
    path("night/", aa_views.NightModeRedirectView.as_view(), name="nightmode"),
    path("minimize-sidebar/", aa_views.MinimizeSidebarRedirectView.as_view(), name="minimize_sidebar"),
]
