# Importing necessary modules from Django's shortcut functions
# render: Used to bridge the gap between Python data and HTML templates. It combines a template with a context dictionary and returns an HTTP response.
# redirect: Essential for the POST-Redirect-GET pattern. It sends a 302 response to specific URL, preventing form resubmission on refresh.
# get_object_or_404: A robust way to fetch a single object. If the object isn't found, it gracefully raises a 404 Http error instead of crashing with a 500 error.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import csv
from django.db.models import Avg, Sum, Count

# Importing the built-in User model
# Django's authentication system uses this Model to handle user accounts, passwords, and permissions.
from django.contrib.auth.models import User

# Importing token generator
# Why? We need a stateless way to verify email ownership. This generator creates a hash based on user internal state (like password, timestamp).
# If the state changes (e.g. password changed), the token becomes invalid. Perfect for one-time links.
from django.contrib.auth.tokens import default_token_generator

# Importing utilities for URL-safe base64 encoding and decoding
# Why? We need to pass the user's primary key (ID) in the URL for the activation link.
# Raw IDs can sometimes contain characters unsafe for URLs or give away too much info. Base64 encoding standardizes it.
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

# Importing utility to force bytes conversion
# Why? The base64 encoder expects bytes, not strings. This ensures compatibility across different Python versions/string types.
from django.utils.encoding import force_bytes

# Importing send_mail for sending emails
# Django's wrapper around SMTP. It manages the connection to the email server defined in settings.py.
from django.core.mail import send_mail

# Importing decorators for restricting view access
# login_required: A decorator that wraps a view function. It checks if request.user.is_authenticated. If not, redirects to settings.LOGIN_URL.
# user_passes_test: A more flexible decorator. It takes a callable (function) and only allows access if that function returns True.
from django.contrib.auth.decorators import login_required, user_passes_test

# Importing login function
# Used to programmatically create a session for a user. This is different from authenticating (checking credentials).
# It essentially "logs them in" by setting the session ID cookie.
from django.contrib.auth import login

# Importing the messages framework
# Why? To provide feedback after an action (e.g. "Account created").
# It stores messages in a cookie or session, which are retrieved and cleared on the next request. This persistency across redirects is key.
from django.contrib import messages
from django.contrib.auth.views import LoginView

# Importing reverse
# Why hardcoding URLs (/quiz/1/) is bad? If you change your URLconf, you break links.
# reverse() looks up the URL pattern by name ('take_quiz') and returns the correct path. Dry principle.
from django.urls import reverse

# Importing custom models
# These are the Data Access Objects (DAOs) for our application's data.
from .models import Quiz, Question, Result, UserAnswer
from .forms import UserProfileForm

# Importing datetime
# Essential for calculating durations, checking deadlines, and handling timestamps.
from datetime import datetime

class CustomLoginView(LoginView):
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password")
        return super().form_invalid(form)

def is_admin(user):
    """
    Helper function used by the @user_passes_test decorator.
    
    Why: We need a reusable logic to determine who is an 'admin'.
    Currently, we rely on the built-in 'is_superuser' flag.
    If we later want to change this (e.g., 'is_staff' or a specific group), we only change it here.
    """
    return user.is_superuser

@user_passes_test(is_admin)
def admin_create_user(request):
    """
    View for administrators to create a new user.
    
    Deep Dive:
    1. Security: @user_passes_test(is_admin) ensures that even if a normal user guesses this URL, 
       they will be redirected to login or 403 Forbidden.
    2. Workflow: 
       - Admin inputs email.
       - System creates an inactive 'shell' user account.
       - System generates a secure link.
       - System emails the link.
       - User clicks link -> sets password -> account active.
       This 'Invitation' flow is safer than emailing plain-text passwords.
    """
    if request.method == 'POST':
        # Data Extraction: Get the email submitted in the form.
        email = request.POST['email']
        # Logic: Create a basic username from the email (everything before the @).
        username = email.split('@')[0]
        
        # Validation: Ensure uniqueness. Django's User model requires unique usernames, 
        # but we also want to enforce unique emails for this app logic.
        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
            return redirect('admin_create_user')
            
        # Creation: atomic creation of the object in RAM and DB.
        user = User.objects.create(username=username, email=email)
        
        # Security Critical: set_unusable_password() sets the password hash to a string that can never match
        # a valid hash (usually starting with !). This prevents anyone (including the user) from logging in 
        # via password until they officially set one.
        user.set_unusable_password()
        user.save()
        
        # Token Generation: make_token uses the user's password hash and last login timestamp as part of the seed.
        # This means if the user changes their password/logs in elsewhere, this specific token becomes invalid.
        token = default_token_generator.make_token(user)
        
        # ID Encoding: Safely encode the primary key.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # URL Construction: build_absolute_uri is crucial. 'reverse' only gives the relative path (/activate/...),
        # but email links need the full domain (http://domain.com/activate/...) to work outside the current browser context.
        link = request.build_absolute_uri(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))
        
        # Email Dispatch: Sends the email synchronously. 
        # Note: In high-traffic production apps, this should be offloaded to a background task (like Celery)
        # to avoid blocking the request processing.
        send_mail(
            'Set your password for Quiz App',
            f'Click the link to set your password: {link}',
            'admin@quizapp.com',
            [email],
            fail_silently=False,
        )
        
        # User Feedback: Flash message stored in session/cookie for the next page load.
        messages.success(request, f'Invitation sent to {email}')
        return redirect('admin_create_user')
    
    # GET Request: Just render the empty form.
    return render(request, 'quiz_master/admin_create_user.html')

def activate_account(request, uidb64, token):
    """
    View to handle account activation and password setting.
    
    Deep Dive:
    This is the destination of the secret link. It must verify two things:
    1. The user ID in the link is valid.
    2. The token corresponds to that user and hasn't expired.
    """
    try:
        # Step 1: Decode the base64 user ID back to a normal string/integer.
        uid = urlsafe_base64_decode(uidb64).decode()
        # Step 2: Retrieve the user from the DB.
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # Security: If the ID is malformed or the user doesn't exist, we treat it quietly as an invalid link.
        user = None

    # Step 3: Token Verification. check_token rehashes the user's current state and compares it to the token.
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            # Steps when user submits the password form
            password = request.POST['password']
            
            # Action: Set the new password. This handles hasing (PBKDF2 by default).
            # It implies the account is now 'active' in a sense that it can be logged into.
            user.set_password(password)
            user.save()
            
            # Redundancy Note: The double call in the original code is unnecessary but safe.
            # user.set_password(password)
            # user.save()
            
            # UX Choice: We redirect to login instead of auto-login to force them to verify their credentials immediately.
            messages.success(request, 'Your account has been activated. Please log in.')
            return redirect('login')
        
        # GET Request: Render the form to type the new password.
        return render(request, 'quiz_master/set_password.html')
    else:
        # Security: Generic error page for invalid tokens prevents information leakage about which users exist.
        return render(request, 'quiz_master/activation_invalid.html')

@login_required
def dashboard(request):
    """
    View for the user dashboard.
    
    Reasoning:
    - Lists all available quizzes.
    - Lists past results to track progress.
    - @login_required protects this view from anonymous access.
    """
    # QuerySet: Lazy database lookups.
    # Quiz.objects.all() prepares a SELECT * FROM quiz table query.
    quizzes = Quiz.objects.all()
    
    # Filtering: SELECT * FROM result WHERE user_id = [current_user_id]
    results = Result.objects.filter(user=request.user)
    
    # Merging the two querysets into a context dictionary passed to the template engine.
    return render(request, 'quiz_master/dashboard.html', {'quizzes': quizzes, 'results': results})

@login_required
def take_quiz(request, quiz_id):
    """
    View for taking a quiz. 
    
    Deep Logic Breakdown:
    1. **Access Control**: Ensures user is logged in and hasn't taken the quiz before.
    2. **State Management**: Uses Django Sessions (server-side storage) to track quiz start time. 
       This prevents users from refreshing the page to reset the timer.
    """
    # Robust Lookup: Get the quiz or 404 for invalid IDs.
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Business Logic: Enforce 'One Attempt Per Quiz'.
    # We query the Result table to see if a record already exists for this user+quiz combo.
    if Result.objects.filter(user=request.user, quiz=quiz).exists():
        messages.warning(request, "You have already attempted this quiz.")
        return redirect('dashboard')

    # **Timer Implementation Explaination**:
    # We cannot trust the client (browser) to send the correct 'time taken'. Users can manipulate JS.
    # Therefore, we store the 'start_time' in the securely signed session cookie on the server.
    
    session_key = f'quiz_{quiz_id}_start_time'
    
    # Initialization: If this is the first page load, mark the time.
    if session_key not in request.session:
        request.session[session_key] = datetime.now().timestamp()
    
    # Calculation: Compute remaining time dynamically on every request (GET or POST).
    start_time = datetime.fromtimestamp(request.session[session_key])
    elapsed_time = (datetime.now() - start_time).total_seconds()
    time_limit_seconds = quiz.time_limit * 60
    
    # Constraint: Time left cannot be negative.
    time_left = int(max(0, time_limit_seconds - elapsed_time))

    if request.method == 'POST':
        # **Submission Phase**
        
        # Cleanup: Remove the session key so the user could potentially take the quiz again 
        # IF we didn't have the DB check above. It's good hygiene.
        if session_key in request.session:
            del request.session[session_key]

        score = 0
        total = quiz.questions.count()
        
        # Scoring Logic:
        # We iterate through the server's knowledge of questions (quiz.questions.all()) rather than 
        # trusting the keys in request.POST, which ensures we only grade valid questions.
        for question in quiz.questions.all():
            # Get user's answer. The HTML form inputs are named after the question IDs (str(question.id)).
            selected_option = request.POST.get(str(question.id))
            
            # Comparator: Check against truth.
            if selected_option == question.correct_option:
                score += 1
        
        # Persistence: Save the calculated result permanently to the DB.
        result = Result.objects.create(user=request.user, quiz=quiz, score=score, total_questions=total)

        # Save specific answers for review
        for question in quiz.questions.all():
            selected_option = request.POST.get(str(question.id))
            if selected_option:
                is_correct = (selected_option == question.correct_option)
                UserAnswer.objects.create(
                    result=result,
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct
                )
        
        # Feedback and Redirect.
        messages.success(request, f'You scored {score}/{total}')
        return redirect('dashboard')
        
    # GET Request: Render the quiz interface. 
    # We pass 'time_left' so the frontend JavaScript can display a countdown.
    return render(request, 'quiz_master/take_quiz.html', {'quiz': quiz, 'time_left': time_left})

@user_passes_test(is_admin)
def admin_results(request):
    """
    View for admin reporting with Analytics and Export.
    """
    results = Result.objects.all().order_by('-date_taken')
    
    # Export Functionality
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="quiz_results.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['User', 'Quiz', 'Score', 'Total Questions', 'Date'])
        
        for result in results:
            writer.writerow([
                result.user.username,
                result.quiz.title,
                result.score,
                result.total_questions,
                result.date_taken.isoformat()
            ])
        
        return response

    # Analytics
    total_attempts = results.count()
    overall_avg_score = results.aggregate(Avg('score'))['score__avg'] or 0
    
    context = {
        'results': results,
        'total_attempts': total_attempts,
        'overall_avg_score': round(overall_avg_score, 2)
    }
    
    return render(request, 'quiz_master/admin_results.html', context)

@login_required
def view_result_detail(request, result_id):
    """
    View for users to review their quiz attempts.
    """
    result = get_object_or_404(Result, id=result_id)
    
    # Security: Ensure the user can only view their own results (unless admin)
    if result.user != request.user and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this result.")
        return redirect('dashboard')
        
    return render(request, 'quiz_master/result_detail.html', {'result': result})

@user_passes_test(is_admin)
def admin_leaderboard(request):
    """
    View for global leaderboard.
    Orders users by their total score across all quizzes.
    """
    # Annotate users with total score and number of quizzes taken.
    # We filter out users who check 'is_superuser' if we want only students, 
    # but maybe admins take quizzes too? Let's leave them in or filter out if needed.
    # Exclude defaults to None for Sum, so we might get None for total_score.
    
    users = User.objects.annotate(
        total_score=Sum('result__score'),
        quizzes_taken=Count('result')
    ).exclude(quizzes_taken=0).order_by('-total_score')
    
    
    return render(request, 'quiz_master/leaderboard.html', {'leaderboard_users': users})

@login_required
def edit_profile(request):
    """
    View for users to edit their profile (First name, Last name, Email).
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('edit_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'quiz_master/edit_profile.html', {'form': form})
