import os
import datetime
from django import contrib
from django.contrib import messages
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic, View
from agents.mixins import OrganisorAndLoginRequiredMixin, AgentAndLoginRequiredMixin,SupervisorAndLoginRequiredMixin, NotSuperuserAndLoginRequiredMixin
from .models import Lead, FollowUp, CaseField, CaseValue, Agent
from .forms import (
    LeadModelForm, 
    AssignAgentForm, 
    FollowUpModelForm,
    LeadUpdateForm,
    FollowUpUpdateModelForm
)
import logging
logger = logging.getLogger(__name__)

class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)

class LeadListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()
        # initial queryset of leads for the entire organisation
        if user.is_lvl4:
            queryset = Lead.objects.all()
        elif user.is_lvl3:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, 
                #agent__isnull=False
            )
        elif user.is_lvl2:
            queryset = Lead.objects.filter(
                organisation=user.manager.organisation, 
                #agent__isnull=False
            )
            queryset = queryset.filter(manager__user=user)
        elif user.is_lvl1:
            queryset = Lead.objects.filter(
                organisation=user.agent.organisation, 
                #agent__isnull=False
            )
            queryset = queryset.filter(agent__user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        lead_fields = []
        case_field_names = []
        leads_data = []
        # Get the first lead from the queryset to extract field names
        lead = self.get_queryset().first()
        if lead:
            lead_fields = [field.name for field in lead._meta.get_fields()]
            if "extrafields" in lead_fields:
                lead_fields.remove("extrafields")
            if "followups" in lead_fields:
                lead_fields.remove('followups')
            if "id" in lead_fields:
                lead_fields.remove('id')
            case_fields = CaseField.objects.filter(user=lead.organisation)
            case_field_names = [field.name for field in case_fields]

            for lead in self.get_queryset():
                lead_data = {field: getattr(lead, field) for field in lead_fields}
                for case_field in case_fields:
                    try:
                        case_value = CaseValue.objects.get(lead=lead, field=case_field)
                        if case_field.field_type == 'text':
                            lead_data[case_field.name] = case_value.value_text
                        elif case_field.field_type == 'number':
                            lead_data[case_field.name] = case_value.value_number
                        elif case_field.field_type == 'date':
                            lead_data[case_field.name] = case_value.value_date
                    except CaseValue.DoesNotExist:
                        lead_data[case_field.name] = None
                lead_data['pk'] = lead.id
                leads_data.append(lead_data)
        context.update({
            "basic_fields": lead_fields,
            "lead_fields": lead_fields + case_field_names,
            "lead_list": leads_data
        })

        return context

class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        if user.is_lvl4:
            queryset = Lead.objects.all()
        elif user.is_lvl3:
            queryset = Lead.objects.filter(
                organisation=user.userprofile, 
                #agent__isnull=False
            )
        elif user.is_lvl2:
            queryset = Lead.objects.filter(
                organisation=user.manager.organisation, 
                #agent__isnull=False
            )
            queryset = queryset.filter(manager__user=user)
        elif user.is_lvl1:
            queryset = Lead.objects.filter(
                organisation=user.agent.organisation, 
                #agent__isnull=False
            )
            queryset = queryset.filter(agent__user=user)
        return queryset

class LeadCreateView(AgentAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        lead = form.save(commit=False)
        lead.agent = self.request.user.agent
        lead.organisation = self.request.user.agent.organisation
        lead.save()
        # send_mail(
        #     subject="A lead has been created",
        #     message="Go to the site to see the new lead",
        #     from_email="test@test.com",
        #     recipient_list=["test2@test.com"]
        # )
        messages.success(self.request, "You have successfully created a lead")
        return super(LeadCreateView, self).form_valid(form)

class LeadUpdateView(NotSuperuserAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_update.html"
    form_class = LeadUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['instance'] = self.object
        return kwargs

    def get_queryset(self):
        user = self.request.user
        up = None
        if user.is_lvl3:
            up = user.userprofile
        elif user.is_lvl2:
            up = user.manager.organisation
        elif user.is_lvl1:
            up = user.agent.organisation

        return Lead.objects.filter(organisation=up)

    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        form.save()
        messages.info(self.request, "You have successfully updated this lead")
        return super(LeadUpdateView, self).form_valid(form)

class LeadDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_success_url(self):
        return reverse("leads:lead-list")

    def get_queryset(self):
        user = self.request.user
        up = None
        if user.is_lvl2:
            up = user.manager.organisation

        # initial queryset of leads for the entire organisation
        return Lead.objects.filter(organisation=up)

class FollowUpCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "leads/followup_create.html"
    form_class = FollowUpModelForm

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super(FollowUpCreateView, self).get_context_data(**kwargs)
        context.update({
            "lead": Lead.objects.get(pk=self.kwargs["pk"])
        })
        return context

    def form_valid(self, form):
        lead = Lead.objects.get(pk=self.kwargs["pk"])
        followup = form.save(commit=False)
        followup.lead = lead
        followup.save()
        return super(FollowUpCreateView, self).form_valid(form)

class FollowUpUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/followup_update.html"
    form_class = FollowUpUpdateModelForm

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_lvl4:
            queryset = FollowUp.objects.all()
        elif user.is_lvl3:
            queryset = FollowUp.objects.filter(lead__organisation=user.userprofile)
        elif user.is_lvl2:
            queryset = FollowUp.objects.filter(lead__organisation=user.manager.organisation)
            queryset = queryset.filter(lead__manager__user=user)
        elif user.is_lvl1:
            queryset = FollowUp.objects.filter(lead__organisation=user.agent.organisation)
            queryset = queryset.filter(lead__agent__user=user)
        return queryset

    def get_success_url(self):
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().lead.id})

class FollowUpDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "leads/followup_delete.html"

    def get_success_url(self):
        followup = FollowUp.objects.get(id=self.kwargs["pk"])
        return reverse("leads:lead-detail", kwargs={"pk": followup.lead.pk})

    def get_queryset(self):
        user = self.request.user
        # initial queryset of leads for the entire organisation
        if user.is_lvl4:
            queryset = FollowUp.objects.all()
        elif user.is_lvl3:
            queryset = FollowUp.objects.filter(lead__organisation=user.userprofile)
        elif user.is_lvl2:
            queryset = FollowUp.objects.filter(lead__organisation=user.manager.organisation)
            queryset = queryset.filter(lead__manager__user=user)
        elif user.is_lvl1:
            queryset = FollowUp.objects.filter(lead__organisation=user.agent.organisation)
            queryset = queryset.filter(lead__agent__user=user)
        return queryset
    
    def form_valid(self, form):
        followup = self.get_object()
        file_path = followup.file.path if followup.file else None
        
        # Delete the followup object
        response = super().form_valid(form)
        
        # If there is a file associated, remove it from the filesystem
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        return response


class CaseFieldListView(SupervisorAndLoginRequiredMixin, generic.ListView):
    template_name = "leads/casefield_list.html"
    context_object_name = 'casefields'

    def get_queryset(self):
        user = self.request.user
        userprofile = user.userprofile
        return CaseField.objects.filter(user=userprofile)
    
class CreateFieldDeleteView(SupervisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/casefield_delete.html"

    def get_success_url(self):
        return reverse('leads:casefield-list')

    def get_queryset(self):
        user = self.request.user
        up = None
        if user.is_lvl3:
            up = user.userprofile
        return CaseField.objects.filter(user=up)

class CreateFieldView(SupervisorAndLoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        field_type = request.POST.get('fieldType')
        field_name = request.POST.get('fieldName')
        CaseField.objects.create(user=self.request.user.userprofile, name=field_name, field_type=field_type)
        return redirect('leads:casefield-list')
    
class PerformanceListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/performance_list.html"
    context_object_name = 'performances'

    def get_queryset(self):
        user = self.request.user
        if user.is_lvl4:
            queryset = Lead.objects.all()
        elif user.is_lvl3:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        elif user.is_lvl2:
            queryset = Lead.objects.filter(organisation=user.manager.organisation)
        elif user.is_lvl1:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = self.get_queryset()
        user = self.request.user

        all_agents = []
        if user.is_lvl4:
            all_agents = Agent.objects.all()
        elif user.is_lvl3:
            all_agents = Agent.objects.filter(organisation=user.userprofile)
        elif user.is_lvl2:
            all_agents = Agent.objects.filter(organisation=user.manager.organisation)
        elif user.is_lvl1:
            all_agents = Agent.objects.filter(organisation=user.agent.organisation)

        agent_data = {}
        for agent in all_agents:
            agent_data[agent] = {
                'username': agent.user.username,
                'num_leads': 0,
                'total_commission': 0,
                'num_completed_leads': 0,
                'completed_lead_commission': 0,
            }

        for lead in leads:
            if lead.agent:
                agent_info = agent_data[lead.agent]
                agent_info['num_leads'] += 1
                commission = int(lead.quote) * (int(lead.commission) / 100)
                agent_info['total_commission'] += commission
                if lead.completed:
                    agent_info['num_completed_leads'] += 1
                    agent_info['completed_lead_commission'] += commission

        performances = [
            [
                agent_info['username'],
                agent_info['num_leads'],
                agent_info['total_commission'],
                agent_info['num_completed_leads'],
                agent_info['completed_lead_commission'],
            ]
            for agent_info in agent_data.values()
        ]

        context['performances'] = performances
        return context
    
class LeadJsonView(generic.View):

    def get(self, request, *args, **kwargs):
        
        qs = list(Lead.objects.all().values(
            "first_name", 
            "last_name", )
        )

        return JsonResponse({
            "qs": qs,
        })
    
class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs
        
    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)