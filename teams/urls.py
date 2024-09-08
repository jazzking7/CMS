from django.urls import path
from .views import (TeamDeleteView, TeamMemberCreateView, 
                    TeamManagementRootView, TeamCreateView, TeamUpdateView, UserCreateView,
                    TeamMemberDeleteView, UserDetailView)

app_name = 'teams'

urlpatterns = [
    path('', TeamManagementRootView.as_view(), name='team-root'),
    path('team/add/', TeamCreateView.as_view(), name='team-create'),
    path('team/<int:pk>/delete/', TeamDeleteView.as_view(), name='team-delete'),
    path('team/<int:pk>/update/', TeamUpdateView.as_view(), name='team-update'),
    path('teams/<int:pk>/add_member/', TeamMemberCreateView.as_view(), name='team-add-member'),
    path('teammember/<int:user_id>/<int:team_id>/delete/', TeamMemberDeleteView.as_view(), name='team-member-delete'),
    path('teammember/user_create/', UserCreateView.as_view(), name="team-user-create"),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]