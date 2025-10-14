from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Affirmation, LuckCard, DailyAffirmation
import random
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone


# 🌿 Home Page
def home(request):
    return render(request, 'home.html')


# 🌸 Register
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'register.html')


# 🌼 Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username} 🌿")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


# 🍃 Logout
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out 🌸")
    return redirect('login')


# 🌻 Affirmations Page
def affirmations_page(request):
    return render(request, 'affirmations.html')


# 💫 API: Draw a single random affirmation
def draw_affirmation(request):
    affirmations = list(Affirmation.objects.all())
    if not affirmations:
        return JsonResponse({'affirmation': "No affirmations yet.", 'image': '', 'category': ''})

    card = random.choice(affirmations)
    return JsonResponse({
        'affirmation': card.text,
        'image': card.image.url if card.image else '',
        'category': card.category
    })


# 🌟 Dashboard: Random Luck Card + 5 Daily Affirmations
def dashboard(request):
    # Check user is logged in
    if not request.user.is_authenticated:
        return redirect('login')

    # Pick 1 random luck card
    luck_card = random.choice(list(LuckCard.objects.all())) if LuckCard.objects.exists() else None

    # Pick 5 random affirmations
    all_affirmations = list(Affirmation.objects.all())
    affirmations = random.sample(all_affirmations, min(5, len(all_affirmations))) if all_affirmations else []

    # Optionally record today’s daily affirmations for the user
    today = timezone.now().date()
    daily_record, created = DailyAffirmation.objects.get_or_create(user=request.user, date=today)
    if created:
        daily_record.affirmations.set(affirmations)

    return render(request, 'dashboard.html', {
        'luck_card': luck_card,
        'affirmations': affirmations
    })

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import LuckCard
import random

@login_required
@require_GET
def draw_luck_api(request):
    """
    Return one random LuckCard from the pool (admin-managed).
    This does NOT persist anything per-user — it's just a fresh draw.
    """
    qs = LuckCard.objects.all()
    if not qs.exists():
        return JsonResponse({'error': 'No luck cards available.'}, status=404)

    card = random.choice(list(qs))
    return JsonResponse({
        'message': card.message,
        'icon': card.icon or '',
    })
