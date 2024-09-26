
from django.urls import path
from .views import *

app_name = "performances"

urlpatterns = [
    path('performances/<int:team_id>/', SingleTeamPerformanceListView.as_view(), name='performance_list'),
    path('', TeamsPerformanceListView.as_view(), name='team_performances'),
    path('user-performance/<int:user_id>/', UserPerformanceListView.as_view(), name='user_performance_list'),
    path('ranking/', performanceRankingView.as_view(), name='performance_ranking'),
    path('personal/', personalPerformanceView.as_view(), name='personal_work'),

]