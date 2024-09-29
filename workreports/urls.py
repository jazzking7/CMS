from django.urls import path
from .views import *

app_name = 'workreports'

urlpatterns = [
    path('add/', WorkReportCreateView.as_view(), name='report-create'),
    path('list/', WorkReportListView.as_view(), name='report-list'),
    path('workreport/<int:pk>/', WorkReportDetailView.as_view(), name='report-detail'),
    path('delete/<int:pk>', WorkReportDeleteView.as_view(), name='report-delete'),
    path('<int:pk>/update/', WorkReportUpdateView.as_view(), name='report-update'),
]