import random
from django.core.mail import send_mail
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.shortcuts import reverse, get_object_or_404, redirect
from django.contrib import messages
from leads.models import (User,  UserRelation, Team, TeamMember
                          )
from .forms import (TeamCreateForm, 
                    TeamUpdateForm, TeamMemberForm, UserCreateForm
                    )
from django.contrib.auth.mixins import LoginRequiredMixin
from agents.mixins import (SupervisorAndLoginRequiredMixin, SuperAdminAndLoginRequiredMixin, NoLvl1AndLoginRequiredMixin)

class TeamManagementRootView(NoLvl1AndLoginRequiredMixin, generic.ListView):
    template_name = "teams/teams_root.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the queryset of teams
        teams = self.get_queryset()
        
        # Initialize an empty dictionary to store teams and their members
        teams_with_members = {}

        # Fetch team members for each team
        for team in teams:
            # Fetch team members for the current team
            members = User.objects.filter(teammember__team=team)
            teams_with_members[team] = members
        
        # TEAM MEMBERS
        context['teams_with_members'] = teams_with_members
        # TEAMS
        context['teams'] = teams
        # Optionally: If you need `curr_contents` similar to the folder document approach, you can adjust here as needed

        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Team.objects.all()  # Default queryset if no conditions are met

        if user.is_lvl4:
            # Level 4: All teams
            queryset = Team.objects.all()
        
        elif user.is_lvl3:
            # Level 3: All teams from users managed by them
            user_relation = UserRelation.objects.filter(supervisor=user).values_list('user', flat=True)
            queryset = Team.objects.filter(team_leader__in=user_relation)
        
        elif user.is_lvl2:
            # Level 2: All teams created by them
            queryset = Team.objects.filter(team_leader=user)
        
        return queryset

class TeamCreateView(NoLvl1AndLoginRequiredMixin, generic.CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/teams_create.html'  # Replace with your actual template

    def get_form_kwargs(self):
        kwargs = super(TeamCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            # Set the team leader if the form is valid
            team = form.save(commit=False)
            if self.request.user.is_lvl2:
                team.team_leader = self.request.user
            elif not form.cleaned_data['team_leader']:
                team.team_leader = self.request.user
            team.save()
            return super(TeamCreateView, self).form_valid(form)
        except IntegrityError:
            # If there's an integrity error, add a message and redirect to the teams root
            messages.error(self.request, "Failed to create team due to a database integrity issue.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("teams:team-root")
    
class TeamDeleteView(NoLvl1AndLoginRequiredMixin, generic.DeleteView):
    model = Team
    template_name = 'teams/teams_delete.html'  # Template to confirm deletion
    
    def get_success_url(self):
        return reverse("teams:team-root")

    def get_queryset(self):
        # Ensure that the queryset contains only the team with the given ID
        queryset = super().get_queryset()
        return queryset.filter(id=self.kwargs.get('pk'))
    
class TeamUpdateView(NoLvl1AndLoginRequiredMixin, generic.UpdateView):
    form_class = TeamUpdateForm
    template_name = 'teams/teams_update.html'  # Replace with your actual template name

    def form_valid(self, form):
        try:
            return super(TeamUpdateView, self).form_valid(form)
        except IntegrityError:
            # If there's an integrity error, add a message and redirect to the teams root
            messages.error(self.request, "Failed to update team due to a database integrity issue.")
            return self.form_invalid(form)

    def get_success_url(self):
        # Redirect to the team's detail view or a list view after successful update
        return reverse('teams:team-root')
    def get_queryset(self):
            # Fetch the team object with the given ID (primary key)
            return Team.objects.filter(id=self.kwargs['pk'])

class TeamMemberCreateView(NoLvl1AndLoginRequiredMixin, generic.CreateView):
    model = TeamMember
    form_class = TeamMemberForm
    template_name = 'teams/teams_member_create.html'  # Replace with your actual template

    def get_form_kwargs(self):
        # Get the default form kwargs
        kwargs = super().get_form_kwargs()
        # Add the user to the form kwargs
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        team = get_object_or_404(Team, id=self.kwargs['pk'])
        team_member = form.save(commit=False)
        team_member.team = team

        try:
            # Try saving the team member to the team
            team_member.save()
            messages.success(self.request, "Team member added successfully!")
            return super(TeamMemberCreateView, self).form_valid(form)
        except IntegrityError:
            # Handle the case where the member is already in the team
            messages.error(self.request, "This user is already a member of the team.")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        # Redirect back to the form if invalid and display an error
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Redirect to the team's detail view or a list view after adding a member
        return reverse('teams:team-root')
    
class TeamMemberDeleteView(NoLvl1AndLoginRequiredMixin, generic.DeleteView):
    model = TeamMember
    template_name = 'teams/teams_member_delete.html' 
    
    def get_success_url(self):
        return reverse("teams:team-root")
    
    def get_object(self, queryset=None):
        user_id = self.kwargs.get('user_id')
        team_id = self.kwargs.get('team_id')
        # Fetch the TeamMember object that matches the given user_id and team_id
        return get_object_or_404(TeamMember, member_id=user_id, team_id=team_id)

    def get_queryset(self):
        # Get user_id and team_id from URL parameters
        user_id = self.kwargs.get('user_id')
        team_id = self.kwargs.get('team_id')
        
        # Fetch the TeamMember object that matches both user_id and team_id
        return TeamMember.objects.filter(member_id=user_id, team_id=team_id)
    
class UserCreateView(NoLvl1AndLoginRequiredMixin, generic.CreateView):
    template_name = "teams/user_create.html"
    form_class = UserCreateForm

    def get_success_url(self):
        return reverse("teams:team-root")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_updating'] = False
        return kwargs
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_lvl1 = True

        user.set_password(f"{random.randint(0, 1000000)}") # ???
        user.save()
        
        if self.request.user.is_lvl3 or self.request.user.is_lvl4:
            UserRelation.objects.create(user=user, supervisor=self.request.user)
        else:
            try:
                supervisor = UserRelation.objects.get(user=self.request.user).supervisor
                UserRelation.objects.create(user=user, supervisor=supervisor)
            except ObjectDoesNotExist:
                raise ValueError("The requesting user does not have a supervisor.")

        # send_mail(
        #     subject="You are invited to join",
        #     message="You were added as a user on DJCRM. Please come login to start working.",
        #     from_email="admin@test.com",
        #     recipient_list=[user.email]
        # )
        return super(UserCreateView, self).form_valid(form)
    
class UserDetailView(NoLvl1AndLoginRequiredMixin, generic.DetailView):
    model = User  # Replace with your actual User model if it's custom
    template_name = 'teams/user_detail.html'  # Path to your template
    context_object_name = 'user'  # The context variable name for the user

    def get_queryset(self):
        # Fetch only the user matching the provided ID (pk)
        return User.objects.filter(id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        # Get the default context data
        context = super(UserDetailView, self).get_context_data(**kwargs)
        return context