from django.contrib import admin
from .models import Member, Tournament, Team


class TournamentAdmin(admin.ModelAdmin):
    exclude = ("layout",)

    def save_model(self, request, obj, form, change):
        if not obj.layout or "bracket" not in obj.layout:
            obj.layout = {"bracket": []}
        super().save_model(request, obj, form, change)


admin.site.register(Member)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Team)