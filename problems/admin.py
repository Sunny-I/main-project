from django.contrib import admin

from django.contrib import admin
from .models import Problem

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'submissions', 'created_at')
    search_fields = ('title', 'tags')
    prepopulated_fields = {'slug': ('title',)}
