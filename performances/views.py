import os
import datetime
from django import contrib
from django.contrib import messages
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic, View
from agents.mixins import SupervisorAndLoginRequiredMixin, NotSuperuserAndLoginRequiredMixin, NoLvl1AndLoginRequiredMixin
from leads.models import Lead, CaseField, UserRelation, User, Team
from .forms import * #()
from django.db.models import Count, Sum, Q
from django.db import models
from django.core.exceptions import FieldDoesNotExist
import json
from django.db import IntegrityError


# Used by major update
from django.core.exceptions import ObjectDoesNotExist

from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta

class SingleTeamPerformanceListView(LoginRequiredMixin, generic.ListView):
    template_name = "performances/performance_list.html"
    context_object_name = 'performances'

    def get_queryset(self):
        # Retrieve team ID from the URL
        team_id = self.kwargs.get('team_id')
        team = Team.objects.get(id=team_id)
        leads = Lead.objects.filter(
            Q(agent__in=team.teammember_set.values_list('member', flat=True)) | 
            Q(manager__in=team.teammember_set.values_list('member', flat=True)) | 
            Q(agent=team.team_leader) | 
            Q(manager=team.team_leader)
        )
        # Apply time range filtering
        time_range = self.request.GET.get('time_range', 'all')
        if time_range != 'all':
            leads = self.filter_by_time_range(leads, time_range)
        return leads

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
        
        return queryset  # No filtering if 'all'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get('team_id')
        team = Team.objects.get(id=team_id)
        leads = self.get_queryset()

        # Initialize team member data
        team_members = list(team.teammember_set.values_list('member', flat=True)) + [team.team_leader.id]
        team_members_data = {member.member.id: {
                'user_id': member.member.id,
                'username': member.member.username,
                'num_leads': 0,
                'total_commission': 0,
                'num_completed_leads': 0,
                'completed_lead_commission': 0,
            }
            for member in team.teammember_set.all()
        }
        team_leader = team.team_leader
        team_members_data[team_leader.id] = {
            'user_id': team_leader.id,
            'username': team_leader.username,
            'num_leads': 0,
            'total_commission': 0,
            'num_completed_leads': 0,
            'completed_lead_commission': 0,
        }

        # Populate member data based on filtered leads
        for lead in leads:
            if lead.status == "取消":
                continue 
            if lead.agent and lead.agent.id in team_members:
                commission = int(lead.quote) * int(lead.commission) / 100
                team_members_data[lead.agent.id]['num_leads'] += 1
                team_members_data[lead.agent.id]['total_commission'] += commission
                if lead.status == '已完成':
                    team_members_data[lead.agent.id]['num_completed_leads'] += 1
                    team_members_data[lead.agent.id]['completed_lead_commission'] += commission

            if lead.manager and lead.manager.id in team_members:
                co_commission = int(lead.quote) * int(lead.co_commission) / 100
                team_members_data[lead.manager.id]['num_leads'] += 1
                team_members_data[lead.manager.id]['total_commission'] += co_commission
                if lead.status == '已完成':
                    team_members_data[lead.manager.id]['num_completed_leads'] += 1
                    team_members_data[lead.manager.id]['completed_lead_commission'] += co_commission
            
            if lead.agent and lead.manager and lead.agent == lead.manager and lead.agent.id in team_members:
                team_members_data[lead.agent.id]['num_leads'] -= 1
                if lead.status == '已完成':
                    team_members_data[lead.agent.id]['num_completed_leads'] -= 1


        performances = [
            {
                'member_stats': [
                member['username'],
                member['num_leads'],
                member['total_commission'],
                member['num_completed_leads'],
                member['completed_lead_commission'],
                ],
                'member_id': member['user_id']
            }
            for member in team_members_data.values()
        ]

        context['performances'] = performances
        context['curr_id'] = self.kwargs.get('team_id')
        context['curr_team'] = team
        return context

class TeamsPerformanceListView(LoginRequiredMixin, generic.ListView):
    template_name = "performances/teams_performances.html"
    context_object_name = 'teams_performances'

    def get_queryset(self):
        user = self.request.user
        queryset = Team.objects.none()

        # Fetch appropriate queryset based on user level
        if user.is_lvl4:
            queryset = Team.objects.all()
        elif user.is_lvl3:
            queryset = Team.objects.filter(team_leader__user_name__supervisor=user)
        elif user.is_lvl2 or user.is_lvl1:
            sr = UserRelation.objects.get(user=user)
            queryset = Team.objects.filter(team_leader__user_name__supervisor=sr.supervisor)

        return queryset
    
    def filter_by_time_range(self, queryset, time_range):
        """Filters queryset by the time range provided"""
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
        
        return queryset  # No filtering if 'all'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teams = self.get_queryset()
        time_range = self.request.GET.get('time_range', 'all')

        # Initialize team data
        team_data = {}
        for team in teams:

            leads = Lead.objects.filter(
                Q(agent__in=team.teammember_set.values_list('member', flat=True)) | 
                Q(manager__in=team.teammember_set.values_list('member', flat=True)) | 
                Q(agent=team.team_leader) | 
                Q(manager=team.team_leader)
            )

            if time_range != 'all':
                leads = self.filter_by_time_range(leads, time_range)

            completed_leads = leads.filter(status='已完成')

            team_members = list(team.teammember_set.values_list('member', flat=True))  # List of member IDs
            total_commission = 0
            for lead in completed_leads:

                if lead.agent and lead.agent.pk in team_members or lead.agent == team.team_leader:
                    total_commission += int(lead.quote) * int(lead.commission) / 100

                if lead.manager and lead.manager.pk in team_members or lead.manager == team.team_leader:
                    total_commission += int(lead.quote) * int(lead.co_commission) / 100

            team_data[team] = {
                'team_id': team.pk,
                'team_name': team.name,
                'team_leader': team.team_leader.username,
                'num_teammembers': team.teammember_set.count() + 1,
                'num_leads': leads.count(),
                'num_completed_leads': completed_leads.count(),
                'total_commission': total_commission,
            }

        # Convert team data to a list for display
        performances = [
            {
                'team_stats': [
                    team_info['team_name'],
                    team_info['team_leader'],
                    team_info['num_teammembers'],
                    team_info['num_leads'],
                    team_info['num_completed_leads'],
                    team_info['total_commission'],
                ],
                'team_id': team_info['team_id']
            }
            for team_info in team_data.values()
        ]

        context['teams_performances'] = performances
        return context

class UserPerformanceListView(LoginRequiredMixin, generic.ListView):
    template_name = "performances/user_performance_list.html"
    context_object_name = 'leads'

    def get_queryset(self):
        # Retrieve user ID from the URL
        user_id = self.kwargs.get('user_id')
        user = User.objects.get(id=user_id)

        leads = Lead.objects.filter(
            Q(agent=user) | Q(manager=user)
        )

        # Apply time range filtering
        time_range = self.request.GET.get('time_range', 'all')
        if time_range != 'all':
            leads = self.filter_by_time_range(leads, time_range)

        return leads

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
        
        return queryset  # No filtering if 'all'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        leads = self.get_queryset()
        curr_user = User.objects.get(id=user_id)

        # Performance summary
        num_leads = leads.count()
        total_commission = 0
        num_completed_leads = 0
        completed_lead_commission = 0

        lead_fields = []
        case_field_names = []
        datetime_fields_info = []

        lead = self.get_queryset().first()
        if lead:
            lead_fields = [field.name for field in lead._meta.get_fields()]
            if "extrafields" in lead_fields:
                lead_fields.remove("extrafields")
            if "followups" in lead_fields:
                lead_fields.remove('followups')
            if "id" in lead_fields:
                lead_fields.remove('id')
            if "organisation" in lead_fields:
                lead_fields.remove('organisation')
            if "description" in lead_fields:
                lead_fields.remove('description')

            case_fields = CaseField.objects.filter(user=lead.organisation)
            case_field_names = [field.name for field in case_fields]

            combined_fields = lead_fields # + case_field_names

            # Check field types and save index and type if it's DateTimeField or DateField
            for i, field_name in enumerate(combined_fields):
                try:
                    if field_name in lead_fields:
                        # Check lead fields
                        field = lead._meta.get_field(field_name)
                        if isinstance(field, models.DateTimeField):
                            datetime_fields_info.append({'index': i, 'type': 'datetime'})
                        elif isinstance(field, models.DateField):
                            datetime_fields_info.append({'index': i, 'type': 'date'})
                    else:
                        # Handle case fields if needed
                        # Assuming you might have some way to access field type
                        case_field = CaseField.objects.get(user=lead.organisation, name=field_name)
                        if case_field.field_type == 'date':
                            datetime_fields_info.append({'index': i, 'type': 'date'})
                        elif case_field.field_type == 'datetime':
                            datetime_fields_info.append({'index': i, 'type': 'datetime'})
                except FieldDoesNotExist:
                    pass


            context.update({
                "lead_fields": combined_fields,
                "datetime_fields_info": json.dumps(datetime_fields_info) 
            })


        for lead in leads:
            if lead.status == "取消":
                continue
            
            commission = int(lead.quote) * int(lead.commission) / 100 if lead.agent == curr_user else 0
            co_commission = int(lead.quote) * int(lead.co_commission) / 100 if lead.manager == curr_user else 0

            total_commission += (commission + co_commission)

            if lead.status == '已完成':
                num_completed_leads += 1
                completed_lead_commission += (commission + co_commission)

        performance_summary = {
            'num_leads': num_leads,
            'total_commission': total_commission,
            'num_completed_leads': num_completed_leads,
            'completed_lead_commission': completed_lead_commission,
        }

        # Pass the performance summary and leads to context
        context['performance_summary'] = performance_summary
        context['leads'] = leads
        context['curr_id'] = user_id
        context['curr_name'] = curr_user.username
        
        return context

class performanceRankingView(LoginRequiredMixin, generic.ListView):
    template_name = "performances/performance_ranking.html"
    context_object_name = 'performances'

    def get_queryset(self):
        user = self.request.user
        queryset = None
        if user.is_lvl4:
            queryset = Lead.objects.all()
        elif user.is_lvl3:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        elif user.is_lvl2:
            sr = UserRelation.objects.get(user=user)
            up = sr.supervisor.userprofile
            queryset = Lead.objects.filter(organisation=up)
        elif user.is_lvl1:
            sr = UserRelation.objects.get(user=user)
            up = sr.supervisor.userprofile
            queryset = Lead.objects.filter(organisation=up)

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = self.get_queryset()
        user = self.request.user

        up = None
        if user.is_lvl3:
            up = user.userprofile
        elif user.is_lvl2:
            sr = UserRelation.objects.get(user=user)
            up = sr.supervisor.userprofile
        elif user.is_lvl1:
            sr = UserRelation.objects.get(user=user)
            up = sr.supervisor.userprofile

        all_agents = []
        if user.is_lvl4:
            all_agents = User.objects.all()
        elif user.is_lvl3:
            all_agents = User.objects.filter(
                Q(is_lvl3=True, userprofile=up) |
                Q(Q(is_lvl1=True) | Q(is_lvl2=True), user_name__supervisor__userprofile=up)
            )
        elif user.is_lvl2:
            all_agents = User.objects.filter(
                Q(is_lvl3=True, userprofile=up) |
                Q(Q(is_lvl1=True) | Q(is_lvl2=True), user_name__supervisor__userprofile=up)
            )
        elif user.is_lvl1:
            all_agents = User.objects.filter(
                Q(is_lvl3=True, userprofile=up) |
                Q(Q(is_lvl1=True) | Q(is_lvl2=True), user_name__supervisor__userprofile=up)
            )

        agent_data = {}
        for agent in all_agents:
            agent_data[agent] = {
                'user_id': agent.pk,
                'username': agent.username,
                'num_leads': 0,
                'total_commission': 0,
                'num_completed_leads': 0,
                'completed_lead_commission': 0,
            }

        for lead in leads:
            if lead.status == "取消":
                continue 

            if lead.agent:
                agent_info = agent_data[lead.agent]
                agent_info['num_leads'] += 1
                commission = int((lead.quote) * (int(lead.commission) / 100))
                agent_info['total_commission'] += commission
                if lead.status=='已完成':
                    agent_info['completed_lead_commission'] += commission
                    agent_info['num_completed_leads'] += 1
            if lead.manager:
                agent_info = agent_data[lead.manager]
                agent_info['num_leads'] += 1
                co_commission = int((lead.quote) * (int(lead.co_commission) / 100))
                agent_info['total_commission'] += co_commission
                if lead.status=='已完成':
                    agent_info['completed_lead_commission'] += co_commission
                    agent_info['num_completed_leads'] += 1


            if lead.agent and lead.manager and lead.agent == lead.manager:
                agent_data[lead.manager]['num_leads'] -= 1
                if lead.status == '已完成':
                    agent_data[lead.manager]['num_completed_leads'] -= 1

        performances = sorted(
            [
                {
                    'user_stats': [
                        agent_info['username'],
                        agent_info['num_leads'],
                        agent_info['total_commission'],
                        agent_info['num_completed_leads'],
                        agent_info['completed_lead_commission'],
                    ],
                    'user_id': agent_info["user_id"]
                }
                for agent_info in agent_data.values()
            ],
            key=lambda x: x['user_stats'][4],  # Sort by completed_lead_commission
            reverse=True  # Sort in descending order
        )
        context['performances'] = performances
        return context
    
class personalPerformanceView(LoginRequiredMixin, generic.ListView):
    template_name = "performances/personal_stats.html"
    context_object_name = 'performances'

    def get_queryset(self):
        user = self.request.user

        leads = Lead.objects.filter(
            Q(agent=user) | Q(manager=user)
        )

        # Apply time range filtering
        time_range = self.request.GET.get('time_range', 'all')
        if time_range != 'all':
            leads = self.filter_by_time_range(leads, time_range)

        return leads
            
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.user.pk
        leads = self.get_queryset()
        curr_user = self.request.user

        # Performance summary
        num_leads = leads.count()
        total_commission = 0
        num_completed_leads = 0
        completed_lead_commission = 0

        lead_fields = []
        case_field_names = []
        datetime_fields_info = []

        lead = self.get_queryset().first()
        if lead:
            lead_fields = [field.name for field in lead._meta.get_fields()]
            if "extrafields" in lead_fields:
                lead_fields.remove("extrafields")
            if "followups" in lead_fields:
                lead_fields.remove('followups')
            if "id" in lead_fields:
                lead_fields.remove('id')
            if "organisation" in lead_fields:
                lead_fields.remove('organisation')
            if "description" in lead_fields:
                lead_fields.remove('description')

            case_fields = CaseField.objects.filter(user=lead.organisation)
            case_field_names = [field.name for field in case_fields]

            combined_fields = lead_fields  + case_field_names

            # Check field types and save index and type if it's DateTimeField or DateField
            for i, field_name in enumerate(combined_fields):
                try:
                    if field_name in lead_fields:
                        # Check lead fields
                        field = lead._meta.get_field(field_name)
                        if isinstance(field, models.DateTimeField):
                            datetime_fields_info.append({'index': i, 'type': 'datetime'})
                        elif isinstance(field, models.DateField):
                            datetime_fields_info.append({'index': i, 'type': 'date'})
                    else:
                        # Handle case fields if needed
                        # Assuming you might have some way to access field type
                        case_field = CaseField.objects.get(user=lead.organisation, name=field_name)
                        if case_field.field_type == 'date':
                            datetime_fields_info.append({'index': i, 'type': 'date'})
                        elif case_field.field_type == 'datetime':
                            datetime_fields_info.append({'index': i, 'type': 'datetime'})
                except FieldDoesNotExist:
                    pass


            context.update({
                "lead_fields": combined_fields,
                "datetime_fields_info": json.dumps(datetime_fields_info) 
            })


        for lead in leads:
            if lead.status == "取消":
                continue
            
            commission = int(lead.quote) * int(lead.commission) / 100 if lead.agent == curr_user else 0
            co_commission = int(lead.quote) * int(lead.co_commission) / 100 if lead.manager == curr_user else 0

            total_commission += (commission + co_commission)

            if lead.status == '已完成':
                num_completed_leads += 1
                completed_lead_commission += (commission + co_commission)

        performance_summary = {
            'num_leads': num_leads,
            'total_commission': total_commission,
            'num_completed_leads': num_completed_leads,
            'completed_lead_commission': completed_lead_commission,
        }

        # Pass the performance summary and leads to context
        context['performance_summary'] = performance_summary
        context['leads'] = leads
        context['curr_id'] = user_id
        context['curr_name'] = curr_user.username
        
        return context