from django import contrib
from django.contrib import messages
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic, View
from agents.mixins import SupervisorAndLoginRequiredMixin, NotSuperuserAndLoginRequiredMixin, NoLvl1AndLoginRequiredMixin
from leads.models import WorkReport, UserRelation, Team, TeamMember
from .forms import *
from django.db.models import Q
from django.db import models
from django.core.exceptions import FieldDoesNotExist
import datetime
from django.db import IntegrityError
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta

# Used by major update
from django.core.exceptions import ObjectDoesNotExist

class WorkReportCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = WorkReportForm
    template_name = 'workreports/workreport_create.html'  # Your template for the form

    def form_valid(self, form):
        user = self.request.user

        form.instance.creator = user

        # For lvl1 and lvl2, set organisation to be their supervisor's userprofile
        if user.is_lvl1 or user.is_lvl2:
            try:
                supervisor_relation = UserRelation.objects.get(user=user)
                form.instance.organisation = supervisor_relation.supervisor.userprofile
            except UserRelation.DoesNotExist:
                form.add_error(None, "Supervisor not found.")
                return self.form_invalid(form)

        # For lvl3 and lvl4, set organisation to be their own userprofile
        elif user.is_lvl3 or user.is_lvl4:
            form.instance.organisation = user.userprofile

        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to a specific page after successful form submission
        return reverse('workreports:report-list')
    
class WorkReportListView(LoginRequiredMixin, generic.ListView):
    template_name = 'workreports/workreport_list.html'  # Your template for the list
    context_object_name = 'workreports'

    def get_queryset(self):
        user = self.request.user
        queryset = None
        if user.is_lvl1:
            # Step 1: Get all teams the user is a member of
            team_memberships = TeamMember.objects.filter(member=user).values_list('team', flat=True)

            # Step 2: Get all team members and team leaders from those teams
            team_users = User.objects.filter(
                Q(id__in=TeamMember.objects.filter(team__in=team_memberships).values_list('member', flat=True)) |
                Q(id__in=Team.objects.filter(id__in=team_memberships).values_list('team_leader', flat=True))
            ).distinct()

            team_users_set = set(team_users)  # Convert queryset to a set
            team_users_set.add(user) 

            # Step 4: Fetch all work reports created by the combined group
            queryset = WorkReport.objects.filter(creator__in=team_users_set).distinct()

        elif user.is_lvl2:
            # Step 1: Get all teams the user leads
            teams_led = Team.objects.filter(team_leader=user).values_list('id', flat=True)

            # Step 2: Get all team members and include the user
            team_users = User.objects.filter(
                Q(id__in=TeamMember.objects.filter(team__in=teams_led).values_list('member', flat=True)) |
                Q(id=user.id)
            ).distinct()

            # Step 3: Fetch all work reports created by the combined group
            queryset = WorkReport.objects.filter(creator__in=team_users).distinct()

        elif user.is_lvl3:
            queryset = WorkReport.objects.filter(organisation=user.userprofile)
        elif user.is_lvl4:
            queryset = WorkReport.objects.all()

     # Apply time range filtering
        time_range = self.request.GET.get('time_range', 'all')
        if time_range != 'all':
            queryset = self.filter_by_time_range(queryset, time_range)

        return queryset

    def filter_by_time_range(self, queryset, time_range):
        if time_range == 'years':
            year = int(self.request.GET.get('year', datetime.now().year))
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            return queryset.filter(date_added__range=(start_date, end_date))
        
        elif time_range == 'quarters':
            year = int(self.request.GET.get('quarter_year', datetime.now().year))
            quarter = self.request.GET.get('quarter')
            quarter_start_end = {
                'Q1': (1, 3),
                'Q2': (4, 6),
                'Q3': (7, 9),
                'Q4': (10, 12)
            }
            start_month, end_month = quarter_start_end[quarter]
            start_date = datetime(year, start_month, 1)
            end_date = datetime(year, end_month, 1).replace(day=1) + timedelta(days=31) - timedelta(days=1)
            return queryset.filter(date_added__range=(start_date, end_date))
        
        elif time_range == 'months':
            year = int(self.request.GET.get('month_year', datetime.now().year))
            month = int(self.request.GET.get('month', datetime.now().month))
            start_date = datetime(year, month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            return queryset.filter(date_added__range=(start_date, end_date))
        
        elif time_range == 'custom':
            start_datetime = parse_datetime(self.request.GET.get('start_datetime'))
            end_datetime = parse_datetime(self.request.GET.get('end_datetime'))

            if start_datetime and end_datetime and end_datetime >= start_datetime:
                return queryset.filter(date_added__range=(start_datetime, end_datetime))

            return queryset
        
        return queryset
    
class WorkReportDetailView(LoginRequiredMixin, generic.DetailView):
    model = WorkReport
    template_name = 'workreports/workreport_detail.html'  # Your template for the detail view
    context_object_name = 'work_report'  # Name of the object in the context

    def get_queryset(self):
        return WorkReport.objects.all()  # You can add any additional filtering if necessary
    
class WorkReportDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = WorkReport
    template_name = 'workreports/workreport_confirm_delete.html'
    context_object_name = 'report'

    def get_queryset(self):
        # Optional: Add any custom queryset filtering if necessary
        return super().get_queryset()
    
    def get_success_url(self):
        # Redirect to the report list page after successful deletion
        return reverse('workreports:report-list')
    
class WorkReportUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = WorkReport
    form_class = WorkReportUpdateForm
    template_name = 'workreports/workreport_update.html'  # Your template for the form
    context_object_name = 'report'

    def get_success_url(self):
        return reverse('workreports:report-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        return super().form_valid(form)