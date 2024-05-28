import random
from django.core.mail import send_mail
from django.views import generic
from django.shortcuts import reverse, get_object_or_404
from leads.models import Agent, Manager, User, UserProfile, Lead
from .forms import (AgentModelForm, UpdateAgentForm, UserModelForm, UpdateUserForm)
from .mixins import SupervisorAndLoginRequiredMixin, SuperAdminAndLoginRequiredMixin

class AgentListView(SupervisorAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.request.user.userprofile
        context['agents'] = Agent.objects.filter(organisation=organisation)
        context['managers'] = Manager.objects.filter(organisation=organisation)
        return context

    def get_queryset(self):
        # Returning agents by default, to comply with ListView's requirement
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation=organisation)


class AgentCreateView(SupervisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "agents/agent_create.html"
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse("agents:agent-list")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_updating'] = False
        return kwargs
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user_level = form.cleaned_data.get('user_level')
        if user_level == 'lvl1':
            user.is_lvl1 = True
            user.is_lvl2 = False
        elif user_level == 'lvl2':
            user.is_lvl1 = False
            user.is_lvl2 = True
        user.set_password(f"{random.randint(0, 1000000)}")
        user.save()
        
        organisation = self.request.user.userprofile
        if user_level == 'lvl1':
            Agent.objects.create(
                user=user,
                organisation=organisation
            )
        elif user_level == 'lvl2':
            Manager.objects.create(
                user=user,
                organisation=organisation
            )

        send_mail(
            subject="You are invited to join",
            message="You were added as a user on DJCRM. Please come login to start working.",
            from_email="admin@test.com",
            recipient_list=[user.email]
        )
        return super(AgentCreateView, self).form_valid(form)


class AgentDetailView(SupervisorAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation=organisation)

class AgentUpdateView(SupervisorAndLoginRequiredMixin, generic.FormView):
    template_name = "agents/agent_update.html"
    form_class = UpdateAgentForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.get_object()
        return context

    def get_object(self):
        user = self.request.user
        return get_object_or_404(Agent, pk=self.kwargs['pk'], organisation=user.userprofile)

    def get_initial(self):
        agent = self.get_object()
        initial = {
            'first_name': agent.user.first_name,
            'last_name': agent.user.last_name,
            'user_level': 'lvl1'  # Initial level
        }
        return initial

    def form_valid(self, form):
        agent = self.get_object()
        user_level_before_update = agent.user.is_lvl1

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        agent.user.first_name = first_name
        agent.user.last_name = last_name
        agent.user.is_lvl1 = user_level == 'lvl1'
        agent.user.is_lvl2 = user_level == 'lvl2'
        agent.user.save()

        # Check if user_level has been updated to 'lvl2' and if user was previously lvl1
        if user_level == 'lvl2' and user_level_before_update:

            # Create a new manager with the existing user and organization
            Manager.objects.create(user=agent.user, organisation=self.request.user.userprofile)
            # Delete the current agent
            agent.delete()

        return super().form_valid(form)
    
class AgentDeleteView(SupervisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation=organisation)
    
    def delete(self, request, *args, **kwargs):
        # Get the manager instance
        agent = self.get_object()
        # Get the associated user
        user = agent.user
        
        # Perform the deletion of the manager
        response = super().delete(request, *args, **kwargs)
        
        # Delete the associated user
        user.delete()
        
        return response
    

class ManagerDetailView(SupervisorAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/manager_detail.html"
    context_object_name = "manager"

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Manager.objects.filter(organisation=organisation)

class ManagerUpdateView(SupervisorAndLoginRequiredMixin, generic.FormView):
    template_name = "agents/manager_update.html"
    form_class = UpdateAgentForm

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager'] = self.get_object()
        return context

    def get_object(self):
        user = self.request.user
        return get_object_or_404(Manager, pk=self.kwargs['pk'], organisation=user.userprofile)

    def get_initial(self):
        manager = self.get_object()
        initial = {
            'first_name': manager.user.first_name,
            'last_name': manager.user.last_name,
            'user_level': 'lvl2'  # Initial level
        }
        return initial

    def form_valid(self, form):
        manager = self.get_object()
        user_level_before_update = manager.user.is_lvl2

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        manager.user.first_name = first_name
        manager.user.last_name = last_name
        manager.user.is_lvl1 = user_level == 'lvl1'
        manager.user.is_lvl2 = user_level == 'lvl2'
        manager.user.save()

        # Check if user_level has been updated to 'lvl2' and if user was previously lvl1
        if user_level == 'lvl1' and user_level_before_update:

            # Create a new manager with the existing user and organization
            Agent.objects.create(user=manager.user, organisation=self.request.user.userprofile)
            # Delete the current manager
            manager.delete()

        return super().form_valid(form)

class ManagerDeleteView(SupervisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/manager_delete.html"
    context_object_name = "manager"

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Manager.objects.filter(organisation=organisation)
    
    def delete(self, request, *args, **kwargs):
        # Get the manager instance
        manager = self.get_object()
        # Get the associated user
        user = manager.user
        
        # Perform the deletion of the manager
        response = super().delete(request, *args, **kwargs)
        
        # Delete the associated user
        user.delete()
        
        return response
    

class UserListView(SuperAdminAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/user_list.html"
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all()


class UserCreateView(SuperAdminAndLoginRequiredMixin, generic.CreateView):
    template_name = "agents/user_create.html"
    form_class = UserModelForm

    def get_success_url(self):
        return reverse("agents:user-list")
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user_level = form.cleaned_data.get('user_level')
        if user_level == 'lvl1':
            user.is_lvl1 = True
        elif user_level == 'lvl2':
            user.is_lvl2 = True
        elif user_level == 'lvl3':
            user.is_lvl3 = True
        user.set_password(f"{random.randint(0, 1000000)}")
        user.save()
        
        # superuser has a super profile
        organisation = self.request.user.userprofile
        if user_level == 'lvl1':
            Agent.objects.create(
                user=user,
                organisation=organisation
            )
        elif user_level == 'lvl2':
            Manager.objects.create(
                user=user,
                organisation=organisation
            )
        elif user_level == 'lvl3':
            UserProfile.objects.create(
                user=user
            )

        send_mail(
            subject="You are invited to join",
            message="You were added as a user on DJCRM. Please come login to start working.",
            from_email="admin@test.com",
            recipient_list=[user.email]
        )
        return super(UserCreateView, self).form_valid(form)

class UserDetailView(SuperAdminAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/user_detail.html"
    context_object_name = "show_user"
    model = User

class UserUpdateView(SuperAdminAndLoginRequiredMixin, generic.FormView):
    template_name = "agents/user_update.html"
    form_class = UpdateUserForm

    def get_success_url(self):
        return reverse("agents:user-list")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.get_object()
        lvl = ''
        curr_sup = None
        if user.is_lvl1:
            lvl = 'lvl1'
            agent = Agent.objects.filter(user=user)
            if agent.exists():
                curr_sup = agent.first().organisation
        elif user.is_lvl2:
            lvl = 'lvl2'
            manager = Manager.objects.filter(user=user)
            if manager.exists():
                curr_sup = manager.first().organisation
        elif user.is_lvl3:
            lvl = 'lvl3'
        else:
            lvl = 'lvl4'
        kwargs['lvl'] = lvl
        kwargs['curr_sup'] = curr_sup
        return kwargs

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edit_user'] = self.get_object()
        return context

    def get_initial(self):
        user = self.get_object()
        lvl = ''
        if user.is_lvl1:
            lvl = 'lvl1'
        elif user.is_lvl2:
            lvl = 'lvl2'
        elif user.is_lvl3:
            lvl = 'lvl3'
        else:
            lvl = 'lvl4'
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_level': lvl
        }
        return initial

    def form_valid(self, form):
        edit_user = self.get_object()
        was1 = edit_user.is_lvl1
        was2 = edit_user.is_lvl2
        was3 = edit_user.is_lvl3

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        edit_user.first_name = first_name
        edit_user.last_name = last_name
        edit_user.is_lvl1 = user_level == 'lvl1'
        edit_user.is_lvl2 = user_level == 'lvl2'
        edit_user.is_lvl3 = user_level == 'lvl3'
        edit_user.save()

        organisor_profile = None
        if 'organisor' in form.cleaned_data:
            organisor_profile = form.cleaned_data['organisor']

        if user_level == 'lvl1' and (was2 or was3):

            if was2:
                Manager.objects.filter(user=edit_user).delete()
            elif was3:
                
                fo = UserProfile.objects.filter(user=edit_user).first()
                Agent.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                Manager.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                Lead.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                UserProfile.objects.filter(user=edit_user).delete()
            
            if organisor_profile is None:
                organisor_profile = self.request.user.userprofile
            Agent.objects.create(user=edit_user, organisation=organisor_profile)

        elif user_level == 'lvl2' and (was1 or was3):

            if was1:
                Agent.objects.filter(user=edit_user).delete()
            elif was3:
                fo = UserProfile.objects.filter(user=edit_user).first()
                Agent.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                Manager.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                Lead.objects.filter(organisation=fo).update(organisation=self.request.user.userprofile)
                UserProfile.objects.filter(user=edit_user).delete()
            
            if organisor_profile is None:
                organisor_profile = self.request.user.userprofile
            Manager.objects.create(user=edit_user, organisation=organisor_profile)
        
        elif user_level == 'lvl3' and (was1 or was2):
            if was1:
                Agent.objects.filter(user=edit_user).delete()
            elif was2:
                Manager.objects.filter(user=edit_user).delete()

            UserProfile.objects.create(user=edit_user)

        if user_level == 'lvl1':
            agent = Agent.objects.get(user=edit_user)
            agent.organisation = organisor_profile
            agent.save()

        if user_level == 'lvl2':
            manager = Manager.objects.get(user=edit_user)
            manager.organisation = organisor_profile
            manager.save()

        return super().form_valid(form)