from django.contrib import admin
from .models import *


admin.site.register(Meeting)


class AuthTokenAdmin(admin.ModelAdmin):
    fields = ['has_proxy', 'token_set']


class OptionInline(admin.StackedInline):
    model = Option
    extra = 3


class VoteAdmin(admin.ModelAdmin):
    inlines = [OptionInline]


admin.site.register(AuthToken, AuthTokenAdmin)
admin.site.register(TokenSet)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Option)
admin.site.register(Tie)
