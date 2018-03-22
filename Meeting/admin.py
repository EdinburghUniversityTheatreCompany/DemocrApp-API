from django.contrib import admin
from .models import *


admin.site.site_header = 'DemocrApp Administration'
admin.site.site_title = 'DemocrApp'
admin.site.index_title = 'DemocrApp Administration'

class AuthTokenAdmin(admin.ModelAdmin):
    fields = ['has_proxy', 'token_set']


class OptionInline(admin.StackedInline):
    model = Option
    extra = 3


class VoteAdmin(admin.ModelAdmin):
    inlines = [OptionInline]


class MeetingAdmin(admin.ModelAdmin):
    fields = ['time', 'name']


admin.site.register(Meeting, MeetingAdmin)
admin.site.register(AuthToken, AuthTokenAdmin)
admin.site.register(TokenSet)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Option)
admin.site.register(Tie)
