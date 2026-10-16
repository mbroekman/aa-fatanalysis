from django.urls import path

from . import views

app_name = "fatanalysis"

urlpatterns = [
    path("", views.index, name="index"),
    path("overview/<int:days>/", views.overview_legacy, name="overview_legacy"),
    path("player/<str:character_name>/", views.player_detail, name="player_detail"),
    path("player/<str:character_name>/<int:period_type>/", views.player_detail_legacy, name="player_detail_legacy"),
    path("sync/", views.sync_management, name="sync_management"),
    path("import/", views.sync_management, name="import_csv"),
    path("periods/", views.period_list, name="period_list"),
    path("period/<int:period_id>/", views.period_detail, name="period_detail"),
    path("period/<int:period_id>/delete/", views.period_delete, name="period_delete"),
]
