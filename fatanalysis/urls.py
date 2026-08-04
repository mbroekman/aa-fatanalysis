from django.urls import path
from . import views

app_name = 'fatanalysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('overview/30/', views.overview_30, name='overview_30'),
    path('overview/90/', views.overview_90, name='overview_90'),
    path('player/<str:character_name>/<int:period_type>/', views.player_detail, name='player_detail'),
    path('import/', views.import_csv, name='import_csv'),
    path('periods/', views.period_list, name='period_list'),
    path('period/<int:period_id>/', views.period_detail, name='period_detail'),
    path('period/<int:period_id>/delete/', views.period_delete, name='period_delete'),
]
