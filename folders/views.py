import random
from django.core.mail import send_mail
from django.views import generic
from django.shortcuts import reverse, get_object_or_404
from leads.models import (Agent, Manager, User, UserProfile, Folder, 
                          FolderDocument
                          )
from .forms import (FolderCreateForm, 
                    FolderContentCreateForm, FolderContentUpdateForm
                    )
from django.contrib.auth.mixins import LoginRequiredMixin
from agents.mixins import (SupervisorAndLoginRequiredMixin, SuperAdminAndLoginRequiredMixin, NoLvl1AndLoginRequiredMixin)

class RootFolderView(LoginRequiredMixin, generic.ListView):
    template_name = "folders/root_folders.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    
        root_folders = self.get_queryset()
        
        context['breadcrumbs'] = []
        context['folders'] = root_folders

        user = self.request.user
        curr_contents = []

        if user.is_lvl4:
            curr_contents = FolderDocument.objects.filter(folder__isnull=True)
        
        elif user.is_lvl3:
            # Level 3: all folders created by them and folders created by lvl2 under their management
            curr_contents = FolderDocument.objects.filter(
                organisation=user.userprofile,
                folder__isnull=True
            )
        
        elif user.is_lvl2:
            # Level 2: all folders created by them and folders created by lvl3 who supervise them
            curr_contents = FolderDocument.objects.filter(
                organisation=user.manager.organisation,
                folder__isnull=True,
            ) 
        
        elif user.is_lvl1:
            # Level 1: all folders created by lvl3 supervisors and lvl2 supervisors
            curr_contents = FolderDocument.objects.filter(
                organisation=user.agent.organisation,
                folder__isnull=True,
            )
    
        context['curr_contents'] = curr_contents

        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Folder.objects.filter(parent__isnull=True)

        if user.is_lvl4:
            # Level 4: all folders
            queryset = Folder.objects.filter(parent__isnull=True)
        
        elif user.is_lvl3:
            # Level 3: all folders created by them and folders created by lvl2 under their management
            queryset = Folder.objects.filter(
                organisation=user.userprofile,
                parent__isnull=True
            )
        
        elif user.is_lvl2:
            # Level 2: all folders created by them and folders created by lvl3 who supervise them
            queryset = Folder.objects.filter(
                organisation=user.manager.organisation,
                parent__isnull=True,
            ) 
        
        elif user.is_lvl1:
            # Level 1: all folders created by lvl3 supervisors and lvl2 supervisors
            queryset = Folder.objects.filter(
                organisation=user.agent.organisation,
                parent__isnull=True,
            )
        return queryset
    
class SubFolderView(LoginRequiredMixin, generic.ListView):
    template_name = "folders/sub_folder.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        current_folder = get_object_or_404(Folder, pk=self.kwargs['pk'])
        context['curr_folder'] = current_folder
    
        context['curr_folders'] = self.get_queryset()
        context['curr_contents'] = FolderDocument.objects.filter(folder=current_folder)

        return context

    def get_queryset(self):

        current_folder = get_object_or_404(Folder, pk=self.kwargs['pk'])

        queryset = Folder.objects.filter(parent=current_folder)

        return queryset
    
class FolderCreateView(NoLvl1AndLoginRequiredMixin, generic.CreateView):
    template_name = 'folders/folder_create.html'
    form_class = FolderCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_id'] = self.kwargs.get('parent_id')
        return context

    def form_valid(self, form):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            parent_folder = Folder.objects.get(id=parent_id)
            form.instance.parent = parent_folder
        else:
            form.instance.parent = None
        user = self.request.user
        if user.is_lvl2:
            form.instance.organisation = self.request.user.manager.organisation
        else:
            form.instance.organisation = self.request.user.userprofile
        return super().form_valid(form)

    def get_success_url(self):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            return reverse("folders:sub-folder", kwargs={"pk": parent_id})
        else:
            return reverse("folders:root-folders")

class FolderDeleteView(NoLvl1AndLoginRequiredMixin, generic.DeleteView):
    template_name = "folders/folder_delete.html"
    model = Folder

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_id'] = self.kwargs.get('parent_id')
        return context

    def get_success_url(self):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            return reverse('folders:sub-folder', kwargs={'pk': parent_id})
        else:
            return reverse('folders:root-folders')
        
class FolderUpdateView(NoLvl1AndLoginRequiredMixin, generic.UpdateView):
    template_name = "folders/folder_update.html"
    form_class = FolderCreateForm

    def get_object(self, queryset=None):
        # Retrieve the folder instance using the pk from the URL
        return get_object_or_404(Folder, pk=self.kwargs.get('pk'))

    def get_success_url(self):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            return reverse('folders:sub-folder', kwargs={'pk': parent_id})
        else:
            return reverse('folders:root-folders')

class FolderContentCreateView(NoLvl1AndLoginRequiredMixin, generic.CreateView):
    template_name = "folders/folder_content_create.html"
    model = FolderDocument
    form_class = FolderContentCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_id'] = self.kwargs.get('parent_id')
        return context

    def form_valid(self, form):
        parent_folder_id = self.kwargs.get('parent_id')
        if parent_folder_id:
            parent_folder = get_object_or_404(Folder, pk=parent_folder_id)
            form.instance.folder = parent_folder
        else:
            form.instance.folder = None
        user = self.request.user
        if user.is_lvl2:
            form.instance.organisation = self.request.user.manager.organisation
        else:
            form.instance.organisation = self.request.user.userprofile  
        return super().form_valid(form)

    def get_success_url(self):
        parent_folder_id = self.kwargs.get('parent_id')
        if parent_folder_id:
            return reverse("folders:sub-folder", kwargs={"pk": parent_folder_id})
        else:
            return reverse("folders:root-folders")

class FolderContentDeleteView(NoLvl1AndLoginRequiredMixin, generic.DeleteView):
    model = FolderDocument
    template_name = "folders/folder_content_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_id'] = self.kwargs.get('parent_id')
        return context
    
    def get_success_url(self):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            return reverse("folders:sub-folder", kwargs={"pk": parent_id})
        else:
            return reverse("folders:root-folders")

class FolderContentUpdateView(NoLvl1AndLoginRequiredMixin, generic.UpdateView):
    model = FolderDocument
    form_class = FolderContentUpdateForm
    template_name = "folders/folder_content_update.html"

    def get_success_url(self):
        parent_id = self.kwargs.get('parent_id')
        if parent_id:
            return reverse('folders:sub-folder', kwargs={'pk': parent_id})
        else:
            return reverse('folders:root-folders')