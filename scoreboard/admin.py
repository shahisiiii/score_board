


# ============================================
# FILE: scoreboard/admin.py
# ============================================

from django.contrib import admin
from .models import Member, ScoreEntry, Score

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0

@admin.register(ScoreEntry)
class ScoreEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'created_by', 'created_at')
    list_filter = ('date', 'created_by')
    inlines = [ScoreInline]

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('member', 'score', 'entry')
    list_filter = ('entry__date',)
