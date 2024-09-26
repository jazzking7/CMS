
from django.urls import path
from .views import (
    LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, LeadDeleteView, LeadJsonView, 
    FollowUpCreateView, FollowUpUpdateView, FollowUpDeleteView, CreateFieldView, CaseFieldListView, CreateFieldDeleteView,
)

app_name = "leads"

urlpatterns = [
    path('', LeadListView.as_view(), name='lead-list'),
    path('json/', LeadJsonView.as_view(), name='lead-list-json'),
    path('<int:pk>/', LeadDetailView.as_view(), name='lead-detail'),
    path('<int:pk>/update/', LeadUpdateView.as_view(), name='lead-update'),
    path('<int:pk>/delete/', LeadDeleteView.as_view(), name='lead-delete'),
    path('<int:pk>/followups/create/', FollowUpCreateView.as_view(), name='lead-followup-create'),
    path('followups/<int:pk>/', FollowUpUpdateView.as_view(), name='lead-followup-update'),
    path('followups/<int:pk>/delete/', FollowUpDeleteView.as_view(), name='lead-followup-delete'),
    path('create/', LeadCreateView.as_view(), name='lead-create'),
    path('create_field/', CreateFieldView.as_view(), name='create-field'),
    path('casefields/', CaseFieldListView.as_view(), name='casefield-list'),
    path('casefields/<int:pk>/delete', CreateFieldDeleteView.as_view(), name='casefield-delete'),
]