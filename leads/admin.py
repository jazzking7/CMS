from django.contrib import admin

from .models import (User, Lead, Agent, UserProfile, FollowUp,
                      CaseField, CaseValue, Manager,
                      Folder, 
                      FolderDocument
                      )



class LeadAdmin(admin.ModelAdmin):
    # fields = (
    #     'first_name',
    #     'last_name',
    # )
    # list_filter = ['category']
    list_display = ['first_name', 'last_name', 'email']
    list_display_links = ['first_name']
    list_editable = ['last_name']
    search_fields = ['first_name', 'last_name', 'email']


admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Agent)
admin.site.register(FollowUp)
admin.site.register(CaseField)
admin.site.register(CaseValue)
admin.site.register(Manager)
admin.site.register(Folder)
admin.site.register(FolderDocument)
