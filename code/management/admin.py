from django.contrib import admin

# Register your models here.
from .models import CCTV, Space, Neighbor, Sequence, Video

admin.site.register(CCTV)
admin.site.register(Space)
admin.site.register(Neighbor)
admin.site.register(Sequence)
admin.site.register(Video)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Manager

# Define an inline admin descriptor for Manager model
# which acts a bit like a singleton
class ManagerInline(admin.StackedInline):
    model = Manager
    can_delete = False
    verbose_name_plural = 'manager'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ManagerInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
