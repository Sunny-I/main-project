from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Problem, TestCase, Submission, TestCaseResult

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ('order', 'input', 'expected_output', 'is_public')
    ordering = ['order']
    classes = ['collapse']

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'created_at', 'test_case_count', 'admin_actions')
    list_filter = ('difficulty', 'created_at')
    search_fields = ('title', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'difficulty')
        }),
        ('Problem Details', {
            'fields': (
                'sample_input', 
                'sample_output', 
                'constraints',
                'time_limit',
                'memory_limit'
            )
        }),
    )
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TestCaseInline]
    readonly_fields = ('created_at',)
    actions = ['recalculate_test_case_count']

    def test_case_count(self, obj):
        return obj.test_cases.count()
    test_case_count.short_description = '# Test Cases'

    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">View Submissions</a>',
            reverse('admin:compiler_submission_changelist') + f'?problem__id__exact={obj.id}'
        )
    admin_actions.short_description = 'Actions'
    admin_actions.allow_tags = True

    def recalculate_test_case_count(self, request, queryset):
        for problem in queryset:
            # This triggers the count property which is already efficient
            count = problem.test_case_count
        self.message_user(request, f"Test case counts verified for {queryset.count()} problems")
    recalculate_test_case_count.short_description = "Recalculate test case counts"

class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('problem', 'order', 'is_public', 'short_input', 'short_output')
    list_filter = ('is_public', 'problem__difficulty')
    search_fields = ('problem__title', 'input', 'expected_output')
    list_select_related = ('problem',)
    ordering = ['problem__title', 'order']
    fields = ('problem', 'order', 'input', 'expected_output', 'is_public')
    raw_id_fields = ('problem',)

    def short_input(self, obj):
        return obj.input[:50] + '...' if len(obj.input) > 50 else obj.input
    short_input.short_description = 'Input Preview'

    def short_output(self, obj):
        return obj.expected_output[:50] + '...' if len(obj.expected_output) > 50 else obj.expected_output
    short_output.short_description = 'Output Preview'

class TestCaseResultInline(admin.TabularInline):
    model = TestCaseResult
    extra = 0
    readonly_fields = ('test_case', 'status', 'runtime', 'memory', 'created_at')
    fields = ('test_case', 'status', 'runtime', 'memory', 'created_at')
    can_delete = False
    ordering = ['test_case__order']
    show_change_link = True

    def has_add_permission(self, request, obj):
        return False

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'language', 'status', 'runtime', 
                   'memory', 'passed_test_cases', 'submitted_at', 'task_status')
    list_filter = ('status', 'language', 'problem__difficulty', 'submitted_at')
    search_fields = ('user__username', 'problem__title', 'code')
    readonly_fields = ('submitted_at', 'task_id', 'is_finished', 'execution_details')
    fieldsets = (
        ('Submission Info', {
            'fields': (
                'user', 
                'problem',
                'submitted_at',
                'language',
                'status',
                'task_id'
            )
        }),
        ('Code', {
            'fields': ('code',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': (
                'runtime',
                'memory',
                'passed_test_cases',
                'total_test_cases',
                'is_finished'
            )
        }),
        ('Debug Info', {
            'fields': ('execution_details',),
            'classes': ('collapse',)
        }),
    )
    inlines = [TestCaseResultInline]
    actions = ['reprocess_submissions', 'cancel_pending_submissions']
    list_select_related = ('user', 'problem')
    raw_id_fields = ('user', 'problem')

    def task_status(self, obj):
        if not obj.task_id:
            return "No task"
        if obj.is_finished:
            return "Completed"
        return "Processing"
    task_status.short_description = 'Task Status'

    def execution_details(self, obj):
        if not obj.task_id:
            return "No execution details available"
        return f"Task ID: {obj.task_id}\nStatus: {'Completed' if obj.is_finished else 'Running'}"
    execution_details.short_description = 'Execution Information'

    def reprocess_submissions(self, request, queryset):
        # This would typically send submissions back to the queue
        # In a real implementation, you'd call your task processing function
        updated = queryset.update(status='P', is_finished=False)
        self.message_user(request, f"{updated} submissions marked for reprocessing")
    reprocess_submissions.short_description = "Reprocess selected submissions"

    def cancel_pending_submissions(self, request, queryset):
        # This would cancel pending tasks in the queue
        queryset = queryset.filter(is_finished=False)
        # In real implementation: revoke Celery tasks
        updated = queryset.update(status='CE', is_finished=True, task_id='')
        self.message_user(request, f"{updated} pending submissions canceled")
    cancel_pending_submissions.short_description = "Cancel pending submissions"

@admin.register(TestCaseResult)
class TestCaseResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission', 'test_case_order', 'status', 'runtime', 'memory', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('submission__user__username', 'submission__problem__title')
    readonly_fields = ('created_at', 'output_preview', 'error_preview')
    fieldsets = (
        ('Test Case Info', {
            'fields': (
                'submission',
                'test_case',
                'created_at'
            )
        }),
        ('Results', {
            'fields': (
                'status',
                'runtime',
                'memory'
            )
        }),
        ('Output', {
            'fields': ('output_preview',),
            'classes': ('collapse',)
        }),
        ('Error', {
            'fields': ('error_preview',),
            'classes': ('collapse',)
        }),
    )
    list_select_related = ('submission', 'submission__user', 'submission__problem', 'test_case')

    def test_case_order(self, obj):
        return obj.test_case.order
    test_case_order.short_description = 'TC Order'
    test_case_order.admin_order_field = 'test_case__order'

    def output_preview(self, obj):
        return obj.output[:500] + '...' if obj.output and len(obj.output) > 500 else obj.output
    output_preview.short_description = 'Output'

    def error_preview(self, obj):
        return obj.error_message[:500] + '...' if obj.error_message and len(obj.error_message) > 500 else obj.error_message
    error_preview.short_description = 'Error Message'

# Register models
admin.site.register(TestCase, TestCaseAdmin)