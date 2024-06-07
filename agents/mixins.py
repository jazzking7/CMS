from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class AgentAndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lvl1:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)

class OrganisorAndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lvl2:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)
    
class SupervisorAndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lvl3:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)
    
class SuperAdminAndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_lvl4:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)

class NotSuperuserAndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_lvl4:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)
    
class NoLvl1AndLoginRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_lvl1:
            return redirect("leads:lead-list")
        return super().dispatch(request, *args, **kwargs)