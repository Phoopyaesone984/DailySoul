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

# views.py (add or replace api_get_piles)
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.templatetags.static import static
from .models import LuckCard, DailyPileDraw, PileCardSelection
import random

MAX_DRAWS_PER_DAY = 3

def api_get_piles(request):
    # Only GET allowed
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    today = timezone.now().date()

    try:
        # Get or create today's draw record
        daily_draw, created = DailyPileDraw.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'draw_count': 0}
        )

        available_cards = list(LuckCard.objects.all())

        if len(available_cards) < 3:
            # Not enough cards to pick from — let the frontend know
            return JsonResponse({
                'piles': [],
                'remaining_draws': max(0, MAX_DRAWS_PER_DAY - daily_draw.draw_count),
                'draw_allowed': daily_draw.draw_count < MAX_DRAWS_PER_DAY,
                'message': 'Not enough cards available'
            }, status=200)

        # If user already reached maximum draws, return the existing saved selections if present
        if daily_draw.draw_count >= MAX_DRAWS_PER_DAY:
            selections = PileCardSelection.objects.filter(daily_draw=daily_draw).order_by('position')
            if selections.exists():
                piles_data = []
                for sel in selections:
                    card = sel.card
                    # safe image URL: absolute if possible, fallback to static
                    try:
                        image_url = request.build_absolute_uri(card.image.url) if card.image else request.build_absolute_uri(static('images/default-card.jpg'))
                    except Exception:
                        image_url = card.image.url if card.image else static('images/default-card.jpg')

                    piles_data.append({
                        'id': sel.position,
                        'image_url': image_url,
                        'message': card.message or ''
                    })

                return JsonResponse({
                    'piles': piles_data,
                    'remaining_draws': 0,
                    'draw_allowed': False,
                    'message': 'Maximum draws reached for today'
                }, status=200)
            else:
                # Edge case: draw_count says used but no saved selections
                # Return a random (non-saved) sample to allow frontend to display images
                sample = random.sample(available_cards, 3)
                piles_data = []
                for idx, card in enumerate(sample, start=1):
                    try:
                        image_url = request.build_absolute_uri(card.image.url) if card.image else request.build_absolute_uri(static('images/default-card.jpg'))
                    except Exception:
                        image_url = card.image.url if card.image else static('images/default-card.jpg')

                    piles_data.append({
                        'id': idx,
                        'image_url': image_url,
                        'message': card.message or ''
                    })

                return JsonResponse({
                    'piles': piles_data,
                    'remaining_draws': 0,
                    'draw_allowed': False,
                    'message': 'Maximum draws reached for today (no saved selections found)'
                }, status=200)

        # At this point user is allowed to draw (draw_count < MAX)
        with transaction.atomic():
            selected_cards = random.sample(available_cards, 3)

            # Clear previous saved selections for this daily_draw and create new ones
            PileCardSelection.objects.filter(daily_draw=daily_draw).delete()
            created_selections = []
            for i, card in enumerate(selected_cards, start=1):
                sel = PileCardSelection.objects.create(
                    daily_draw=daily_draw,
                    card=card,
                    position=i
                )
                created_selections.append(sel)

            # Increment draw count and save
            daily_draw.draw_count += 1
            daily_draw.save()

        # Build response payload
        piles_data = []
        for i, sel in enumerate(created_selections, start=1):
            card = sel.card
            try:
                image_url = request.build_absolute_uri(card.image.url) if card.image else request.build_absolute_uri(static('images/default-card.jpg'))
            except Exception:
                image_url = card.image.url if card.image else static('images/default-card.jpg')

            piles_data.append({
                'id': i,
                'image_url': image_url,
                'message': card.message or ''
            })

        remaining = max(0, MAX_DRAWS_PER_DAY - daily_draw.draw_count)
        return JsonResponse({
            'piles': piles_data,
            'remaining_draws': remaining,
            'draw_allowed': remaining > 0
        }, status=200)

    except Exception as exc:
        # Safe error response for debugging (in production you might want to log and return a generic message)
        return JsonResponse({'error': str(exc)}, status=500)

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count
from collections import OrderedDict
from .models import JournalEntry


def journal(request):
    # Get today's entries
    today = timezone.now().date()
    todays_entries = JournalEntry.objects.filter(
        user=request.user,
        created_at__date=today
    ).order_by('-created_at')

    # Get all entries grouped by date
    all_entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')

    # Group entries by date
    entries_by_date = OrderedDict()
    for entry in all_entries:
        date_key = entry.created_at.date()
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)

    # Calculate streak (you might want to adjust this logic)
    streak = calculate_streak(request.user)

    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if entry_id:
            # Editing an existing entry
            entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
            entry.title = title
            entry.content = content
            entry.save()
            messages.success(request, 'Entry updated successfully!')
        else:
            # Creating a new entry
            JournalEntry.objects.create(
                user=request.user,
                title=title,
                content=content
            )
            messages.success(request, 'Entry saved successfully!')

        return redirect('journal')

    context = {
        'todays_entries': todays_entries,
        'entries_by_date': entries_by_date,
        'streak': streak,
        'current_date': timezone.now(),
    }

    return render(request, 'journal.html', context)


def calculate_streak(user):
    # This is a simple streak calculation - you might want to improve it
    entries = JournalEntry.objects.filter(user=user).order_by('-created_at')
    if not entries:
        return 0

    # Count consecutive days with at least one entry
    streak = 0
    current_date = timezone.now().date()

    while True:
        if entries.filter(created_at__date=current_date).exists():
            streak += 1
            current_date -= timezone.timedelta(days=1)
        else:
            break

    return streak