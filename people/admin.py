"""
The management pages for people and devices.

For now these are Django's own admin pages, used by the owner on a PC. The touch-friendly
admin view replaces them for everyday use in milestone 2.
"""

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .forms import PersonAdminForm
from .models import Device, User

admin.site.site_header = _("blabtodo management")
admin.site.site_title = _("blabtodo management")
admin.site.index_title = _("What would you like to set up?")

# Permission groups are not used: an adult can do everything, a child cannot.
admin.site.unregister(Group)


@admin.register(User)
class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = ["display_name", "role", "has_pin", "is_active"]
    list_filter = ["role", "is_active"]
    fields = ["display_name", "role", "new_pin", "colour", "photo", "is_active"]

    @admin.display(boolean=True, description=_("PIN set"))
    def has_pin(self, person):
        return person.has_pin

    def has_delete_permission(self, request, obj=None):
        # People are never deleted, only marked as no longer living here, so that the
        # archive keeps showing who did what.
        return False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "trusted_by", "created_at", "last_seen_at"]
    list_filter = ["is_active"]
    fields = ["name", "is_active", "trusted_by", "created_at", "last_seen_at"]
    readonly_fields = ["trusted_by", "created_at", "last_seen_at"]

    def has_add_permission(self, request):
        # A device is added by opening the app on it and entering an adult's PIN.
        return False
