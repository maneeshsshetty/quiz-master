# Importing necessary modules from Django's shortcut functions
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import csv
from django.db.models import Avg, Sum, Count

# Importing the built-in User model
from django.contrib.auth.models import User

# Importing token generator
from django.contrib.auth.tokens import default_token_generator

# Importing utilities for URL-safe base64 encoding and decoding
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

# Importing utility to force bytes conversion
from django.utils.encoding import force_bytes

# Importing send_mail for sending emails
from django.core.mail import send_mail

# Importing decorators for restricting view access
from django.contrib.auth.decorators import login_required, user_passes_test

# Importing login function
from django.contrib.auth import login

# Importing the messages framework
from django.contrib import messages
from django.contrib.auth.views import LoginView

# Importing reverse
from django.urls import reverse

# Importing custom models
from .models import Quiz, Question, Result, UserAnswer
from .forms import UserProfileForm, ProfileUpdateForm

# Importing datetime
from datetime import datetime

class CustomLoginView(LoginView):
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password")
        return super().form_invalid(form)

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_create_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = email.split('@')[0]
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
            return redirect('admin_create_user')
            
        user = User.objects.create(username=username, email=email)
        user.set_unusable_password()
        user.save()
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        link = request.build_absolute_uri(reverse('activate_account', kwargs={'uidb64': uid, 'token': token}))
        
        send_mail(
            'Set your password for Quiz App',
            f'Click the link to set your password: {link}',
            'admin@quizapp.com',
            [email],
            fail_silently=False,
        )
        
        messages.success(request, f'Invitation sent to {email}')
        return redirect('admin_create_user')
    
    return render(request, 'quiz_master/admin_create_user.html')

def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST['password']
            user.set_password(password)
            user.save()
            messages.success(request, 'Your account has been activated. Please log in.')
            return redirect('login')
        return render(request, 'quiz_master/set_password.html')
    else:
        return render(request, 'quiz_master/activation_invalid.html')

@login_required
def dashboard(request):
    quizzes = Quiz.objects.all()
    results = Result.objects.filter(user=request.user).order_by('-date_taken')
    
    # Stats Calculation
    stats = results.aggregate(
        total_quizzes=Count('id'),
        avg_score=Avg('score')
    )
    
    context = {
        'quizzes': quizzes, 
        'results': results,
        'user_stats': stats
    }
    return render(request, 'quiz_master/dashboard.html', context)

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if Result.objects.filter(user=request.user, quiz=quiz).exists():
        messages.warning(request, "You have already attempted this quiz.")
        return redirect('dashboard')

    session_key = f'quiz_{quiz_id}_start_time'
    
    if session_key not in request.session:
        request.session[session_key] = datetime.now().timestamp()
    
    start_time = datetime.fromtimestamp(request.session[session_key])
    elapsed_time = (datetime.now() - start_time).total_seconds()
    time_limit_seconds = quiz.time_limit * 60
    
    time_left = int(max(0, time_limit_seconds - elapsed_time))

    if request.method == 'POST':
        if session_key in request.session:
            del request.session[session_key]

        score = 0
        total = quiz.questions.count()
        
        for question in quiz.questions.all():
            selected_option = request.POST.get(str(question.id))
            if selected_option == question.correct_option:
                score += 1
        
        result = Result.objects.create(user=request.user, quiz=quiz, score=score, total_questions=total)

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
        
        messages.success(request, f'You scored {score}/{total}')
        return redirect('dashboard')
        
    return render(request, 'quiz_master/take_quiz.html', {'quiz': quiz, 'time_left': time_left})

@user_passes_test(is_admin)
def admin_results(request):
    results = Result.objects.all().order_by('-date_taken')
    
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
    result = get_object_or_404(Result, id=result_id)
    
    if result.user != request.user and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this result.")
        return redirect('dashboard')
        
    return render(request, 'quiz_master/result_detail.html', {'result': result})

@user_passes_test(is_admin)
def admin_leaderboard(request):
    users = User.objects.annotate(
        total_score=Sum('result__score'),
        quizzes_taken=Count('result')
    ).exclude(quizzes_taken=0).order_by('-total_score')
    
    return render(request, 'quiz_master/leaderboard.html', {'leaderboard_users': users})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserProfileForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('edit_profile')
    else:
        u_form = UserProfileForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'quiz_master/edit_profile.html', context)

@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all().annotate(
        quizzes_taken=Count('result'),
        avg_score=Avg('result__score')
    ).order_by('-date_joined')
    
    return render(request, 'quiz_master/admin_users.html', {'users': users})
