from django.urls import path
from .views import (
    AgentListView, AgentCreateView, AgentDetailView, 
    AgentUpdateView, AgentDeleteView, ManagerDetailView, ManagerUpdateView, ManagerDeleteView,
    UserListView, UserCreateView, UserDetailView, UserUpdateView, UserDeleteOptionView, UserDeleteView
)

app_name = 'agents'

urlpatterns = [
    path('', AgentListView.as_view(), name='agent-list'),
    path('<int:pk>/', AgentDetailView.as_view(), name='agent-detail'),
    path('<int:pk>/update/', AgentUpdateView.as_view(), name='agent-update'),
    path('<int:pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
    path('create/', AgentCreateView.as_view(), name='agent-create'),
    path('<int:pk>/manager/', ManagerDetailView.as_view(), name='manager-detail'),
    path('<int:pk>/manager/update/', ManagerUpdateView.as_view(), name='manager-update'),
    path('<int:pk>/manager/delete/', ManagerDeleteView.as_view(), name='manager-delete'),
    path('sup/', UserListView.as_view(), name='user-list'),
    path('sup/create', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/sup/detail', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/sup/update', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/sup/delete_user_option', UserDeleteOptionView.as_view(), name='user-delete-option'),
    path('<int:pk>/sup/delete_user', UserDeleteView.as_view(), name='user-delete'),
]