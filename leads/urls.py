from django.urls import path
from .views import (lead_list, lead_detail, lead_create, lead_update, lead_delete,
                    LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, LeadDeleteView,
                    AssignAgentView, CategoryListView, CategoryDetailView)

app_name = 'leads'

urlpatterns = [
    path('', LeadListView.as_view(), name='lead-list'),
    path('<int:pk>/', LeadDetailView.as_view(), name='lead-detail'), # specify the type otherwise pk can be anything
    path('create/', LeadCreateView.as_view(), name='lead-create'),
    path('<int:pk>/update/', LeadUpdateView.as_view(), name='lead-update'),
    path('<int:pk>/delete/', LeadDeleteView.as_view(), name='lead-delete'),
    path('<int:pk>/assign-agent/', AssignAgentView.as_view(), name='assign-agent'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]