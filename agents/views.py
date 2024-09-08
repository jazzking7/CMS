import random
from django.core.mail import send_mail
from django.views import generic
from django.shortcuts import reverse, get_object_or_404
from leads.models import User, UserProfile, Lead, UserRelation
from .forms import (AgentModelForm, UpdateAgentForm, UserModelForm, UpdateUserForm)
from .mixins import (SupervisorAndLoginRequiredMixin, SuperAdminAndLoginRequiredMixin, NoLvl1AndLoginRequiredMixin)
from django.db.models import Q

class AgentListView(SupervisorAndLoginRequiredMixin, generic.ListView):
    template_name = "agents/agent_list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.request.user
        context['agents'] = User.objects.filter(
            Q(is_lvl1=True) & Q(user_name__supervisor=organisation)
        )
        print(context['agents'])
        context['managers'] = User.objects.filter(
            Q(is_lvl2=True) & Q(user_name__supervisor=organisation)
        )
        return context

    def get_queryset(self):
        # Returning agents by default, to comply with ListView's requirement
        organisation = self.request.user
        return User.objects.filter(
            Q(is_lvl1=True) & Q(user_name__supervisor=organisation)
        )


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
        
        UserRelation.objects.create(user=user, supervisor=self.request.user)

        # send_mail(
        #     subject="You are invited to join",
        #     message="You were added as a user on DJCRM. Please come login to start working.",
        #     from_email="admin@test.com",
        #     recipient_list=[user.email]
        # )
        return super(AgentCreateView, self).form_valid(form)


class AgentDetailView(NoLvl1AndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_object(self, queryset=None):
            # Fetch the user object based on the 'pk' passed in the URL
            user_id = self.kwargs.get('pk')
            return get_object_or_404(User, id=user_id)

    def get_context_data(self, **kwargs):
        # Fetch the default context data
        context = super().get_context_data(**kwargs)
        
        # Get the user from the context
        user = context['agent']
        
        # Add additional context data if needed
        # For example, you can add more related data about the user
        context['agent'] = user
        
        return context

    def get_queryset(self):
        current_user = self.request.user
        if self.request.user.is_lvl2 and self.request.user.is_lvl4:
            return User.objects.filter(is_lvl1=True)
        # Filter users whose supervisor is the current user
        return User.objects.filter(
            user_name__supervisor=current_user,
            is_lvl1=True  # Add this filter if you specifically want lvl1 users
        )

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
        return get_object_or_404(User, pk=self.kwargs['pk'], user_name__supervisor=user)

    def get_initial(self):
        agent = self.get_object()
        initial = {
            'first_name': agent.first_name,
            'last_name': agent.last_name,
            'user_level': 'lvl1'  # Initial level
        }
        return initial

    def form_valid(self, form):
        agent = self.get_object()

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        agent.first_name = first_name
        agent.last_name = last_name
        agent.is_lvl1 = user_level == 'lvl1'
        agent.is_lvl2 = user_level == 'lvl2'
        agent.save()

        return super().form_valid(form)
    
class AgentDeleteView(SupervisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        current_user = self.request.user
        
        # Filter users whose supervisor is the current user
        return User.objects.filter(
            user_name__supervisor=current_user,
            is_lvl1=True  # Add this filter if you specifically want lvl1 users
        )
    
    def delete(self, request, *args, **kwargs):
        # Get the manager instance
        agent = self.get_object()

        response = super().delete(request, *args, **kwargs)
        
        # Delete the associated user
        agent.delete()
        
        return response
    

class ManagerDetailView(SupervisorAndLoginRequiredMixin, generic.DetailView):
    template_name = "agents/manager_detail.html"
    context_object_name = "manager"

    def get_queryset(self):
        current_user = self.request.user
        
        # Filter users whose supervisor is the current user
        return User.objects.filter(
            user_name__supervisor=current_user,
            is_lvl2=True  # Add this filter if you specifically want lvl1 users
        )

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
        return get_object_or_404(User, pk=self.kwargs['pk'], user_name__supervisor=user)

    def get_initial(self):
        manager = self.get_object()
        initial = {
            'first_name': manager.first_name,
            'last_name': manager.last_name,
            'user_level': 'lvl2'  # Initial level
        }
        return initial

    def form_valid(self, form):
        manager = self.get_object()

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        manager.first_name = first_name
        manager.last_name = last_name
        manager.is_lvl1 = user_level == 'lvl1'
        manager.is_lvl2 = user_level == 'lvl2'
        manager.save()

        return super().form_valid(form)

class ManagerDeleteView(SupervisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "agents/manager_delete.html"
    context_object_name = "manager"

    def get_success_url(self):
        return reverse("agents:agent-list")

    def get_queryset(self):
        current_user = self.request.user
        
        return User.objects.filter(
            user_name__supervisor=current_user,
            is_lvl2=True  
        )
    
    def delete(self, request, *args, **kwargs):
        # Get the manager instance
        manager = self.get_object()
        
        # Perform the deletion of the manager
        response = super().delete(request, *args, **kwargs)
        
        # Delete the associated user
        manager.delete()
        
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
        
        if user_level == 'lvl1':
            UserRelation.objects.create(user=user, supervisor=self.request.user)
        elif user_level == 'lvl2':
            UserRelation.objects.create(user=user, supervisor=self.request.user)
        elif user_level == 'lvl3':
            UserProfile.objects.create(
                user=user
            )

        # send_mail(
        #     subject="You are invited to join",
        #     message="You were added as a user on DJCRM. Please come login to start working.",
        #     from_email="admin@test.com",
        #     recipient_list=[user.email]
        # )
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
            sr = UserRelation.objects.filter(user=user)
            curr_sup = sr.first().supervisor
        elif user.is_lvl2:
            lvl = 'lvl2'
            sr = UserRelation.objects.filter(user=user)
            curr_sup = sr.first().supervisor
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
        is4 = edit_user.is_lvl4

        # Extract form data
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        user_level = form.cleaned_data['user_level']

        # Update user information
        edit_user.first_name = first_name
        edit_user.last_name = last_name
        if not is4:
            edit_user.is_lvl1 = user_level == 'lvl1'
            edit_user.is_lvl2 = user_level == 'lvl2'
            edit_user.is_lvl3 = user_level == 'lvl3'
        edit_user.save()

        organisor_profile = None
        if 'organisor' in form.cleaned_data:
            organisor_profile = form.cleaned_data['organisor']
            print(organisor_profile)

        if user_level == 'lvl1' and was3:

            if was3:

                UserRelation.objects.filter(supervisor=edit_user).update(supervisor=self.request.user)
                UserRelation.objects.create(user=edit_user, supervisor=self.request.user)
                Lead.objects.filter(organisation=edit_user.userprofile).update(organisation=self.request.user.userprofile)
                UserProfile.objects.filter(user=edit_user).delete()

        elif user_level == 'lvl2' and was3:


            if was3:
                UserRelation.objects.filter(supervisor=edit_user).update(supervisor=self.request.user)
                UserRelation.objects.create(user=edit_user, supervisor=self.request.user)
                Lead.objects.filter(organisation=edit_user.userprofile).update(organisation=self.request.user.userprofile)
                UserProfile.objects.filter(user=edit_user).delete()
            
        
        elif user_level == 'lvl3' and (was1 or was2):

            UserRelation.objects.filter(user=edit_user).delete()
            UserProfile.objects.create(user=edit_user)

        if user_level == 'lvl1' and not was3:
            UserRelation.objects.filter(user=edit_user).update(supervisor=organisor_profile)


        if user_level == 'lvl2' and not was3:
            UserRelation.objects.filter(user=edit_user).update(supervisor=organisor_profile)

        return super().form_valid(form)