# Why customize the Admin?
# Django's auto-generated admin interface is great for basic CRUD. 
# But for real-world workflows (like bulk emailing users or editing related items), 
# we need to override the defaults.

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .utils import send_activation_email
from django.contrib import messages
from django.contrib import admin
from .models import Quiz, Question, Result

class QuestionInline(admin.TabularInline):
    """
    Inline Editing:
    Instead of navigating to 'Questions' -> 'Add Question' -> 'Select Quiz',
    this allows the admin to add/edit questions DIRECTLY on the 'Edit Quiz' page.
    """
    model = Question
    # extra=4: Shows 4 blank rows ready for input. 
    # Why 4? Because most multiple choice questions have 4 options, so it implies a pattern? 
    # Or just a reasonable default number of questions to add at once.
    extra = 4

class QuizAdmin(admin.ModelAdmin):
    """
    Configuration for Quiz List/Edit pages.
    """
    # Attaches the QuestionInline defined above to this parent model.
    # Result: The Quiz page shows the Quiz fields (Title, Time Limit) AND a table of Questions.
    inlines = [QuestionInline]

# Custom User Admin
# We want to add a button/action to the User list page.
class CustomUserAdmin(UserAdmin):
    """
    Extending UserAdmin to keep standard features (password hashing forms, permission checkboxes)
    while adding our custom 'actions'.
    """
    actions = ['send_activation_email_action']

    def send_activation_email_action(self, request, queryset):
        """
        Bulk Action:
        This runs when an admin selects multiple users and chooses "Send activation email" from the dropdown.
        
        request: The HTTP request.
        queryset: The list of User objects selected by the admin.
        """
        for user in queryset:
            # We reuse the logic from utils.py to ensure consistency.
            send_activation_email(user, request)
            
        # UI Feedback:
        # self.message_user displays a banner at the top of the admin page.
        self.message_user(request, f"Activation email sent to {queryset.count()} user(s).", messages.SUCCESS)
    
    # Human-readable name that appears in the dropdown menu.
    send_activation_email_action.short_description = "Send activation email"

# Monkey-Patching (Sort of):
# You can only have one Admin class registered per Model.
# We must first remove the default User registration...
admin.site.unregister(User)
# ...and replace it with our improved version.
admin.site.register(User, CustomUserAdmin)

# Standard Registration:
# Quiz uses our custom QuizAdmin class.
admin.site.register(Quiz, QuizAdmin)
# Question and Result use the default ModelAdmin (basic list/edit view).
admin.site.register(Question)
admin.site.register(Result)
