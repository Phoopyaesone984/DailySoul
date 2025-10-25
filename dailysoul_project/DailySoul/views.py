from .models import Affirmation, LuckCard, DailyAffirmation,DeathNoteEntry,JournalEntry
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from .forms import RegisterForm
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from .models import LuckCard, DailyPileDraw, PileCardSelection
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from collections import OrderedDict




def home(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                # Save user
                user = form.save(commit=False)
                # normalize email
                user.email = form.cleaned_data.get('email').strip().lower()
                user.save()
                messages.success(request, "Account created successfully! You can now log in.")
                return redirect('login')
            except IntegrityError:
                # This should be rare due to form validation, but handle DB constraint race
                messages.error(request, "Email already exists")
                return render(request, 'register.html', {'form': form})
        else:
            # form invalid — show errors inline
            return render(request, 'register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# 🌼 Login

def login_view(request):
    """
    Login view using Django's AuthenticationForm.
    We set widget attrs in the view so the template doesn't need widget-tweaks.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        # Always attach styling attributes so the template renders nicely
        form.fields['username'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Username or email',
            'autocomplete': 'username'
        })
        form.fields['password'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username} 🌿")
            return redirect('dashboard')
        else:
            # Let template show form errors; also add a friendly message
            messages.error(request, "Login failed — please check your credentials.")
    else:
        form = AuthenticationForm()
        # Attach same widget attrs for GET
        form.fields['username'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Username or email',
            'autocomplete': 'username'
        })
        form.fields['password'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })

    return render(request, 'login.html', {'form': form})

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


@login_required
def journal(request):
    # Get all entries grouped by date
    all_entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')

    # Group entries by date
    entries_by_date = OrderedDict()
    for entry in all_entries:
        date_key = entry.created_at.date()
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)

    # Sort dates in descending order
    entries_by_date = OrderedDict(sorted(entries_by_date.items(), key=lambda x: x[0], reverse=True))

    # Simple streak calculation
    streak = calculate_streak_simple(request.user)

    if request.method == 'POST':
        # Check if it's a delete request
        if 'delete_id' in request.POST:
            entry_id = request.POST.get('delete_id')
            entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
            entry.delete()
            messages.success(request, 'Journal entry deleted successfully!')
            return redirect('journal')

        # Handle regular form submission (create/update)
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
        'entries_by_date': entries_by_date,
        'streak': streak,
        'current_date': timezone.now(),
    }

    return render(request, 'journal.html', context)


def calculate_streak_simple(user):
    """Simple streak calculation using UTC"""
    entries = JournalEntry.objects.filter(user=user).order_by('-created_at')
    if not entries:
        return 0

    streak = 0
    current_date = timezone.now().date()

    # Check consecutive days with entries
    for i in range(len(entries)):
        entry_date = entries[i].created_at.date()
        days_diff = (current_date - entry_date).days

        if days_diff == i:
            streak += 1
        else:
            break

    return streak


@login_required
def death_note(request):
    # Handle POST request first (form submission)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        mood = request.POST.get('mood', '').strip()

        print(f"DEBUG: Form submitted - User: {request.user}, Content: {content}")  # Debug

        if content:
            try:
                DeathNoteEntry.objects.create(
                    user=request.user,
                    content=content,
                    mood=mood if mood else None
                )
                messages.success(request, 'Negative thought captured in Death Note!')
                print(f"DEBUG: Successfully created entry for user {request.user}")  # Debug
            except Exception as e:
                messages.error(request, f'Error saving thought: {str(e)}')
                print(f"DEBUG: Error creating entry: {e}")  # Debug
        else:
            messages.error(request, 'Please write something before submitting.')

        return redirect('death_note')

    delete_id = request.GET.get('delete')
    if delete_id:
        try:
            entry = DeathNoteEntry.objects.get(id=delete_id, user=request.user)
            entry.delete()
            messages.success(request, 'Thought released successfully!')
            print(f"DEBUG: Successfully deleted entry {delete_id}")  # Debug
            return redirect('death_note')
        except DeathNoteEntry.DoesNotExist:
            messages.error(request, 'Thought not found.')
        except Exception as e:
            messages.error(request, f'Error deleting thought: {str(e)}')

    # Get all notes for the current user
    notes = DeathNoteEntry.objects.filter(user=request.user).order_by('-created_at')
    print(f"DEBUG: Found {notes.count()} notes for user {request.user}")  # Debug

    context = {
        'notes': notes
    }
    return render(request, 'death_note.html', context)# views.py


@login_required
def deathnote(request):
    # Handle POST request first (form submission)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()


        if content:
            try:
                DeathNoteEntry.objects.create(
                    user=request.user,
                    content=content,

                )
                messages.success(request, 'Negative thought captured in Death Note!')

            except Exception as e:
                messages.error(request, f'Error saving thought: {str(e)}')
        else:
            messages.error(request, 'Please write something before submitting.')

        return redirect('death_note')

    # Handle GET request (viewing page or deleting)
    delete_id = request.GET.get('delete')
    if delete_id:
        try:
            entry = DeathNoteEntry.objects.get(id=delete_id, user=request.user)
            entry.delete()
            messages.success(request, 'Thought released successfully!')
            return redirect('death_note')
        except DeathNoteEntry.DoesNotExist:
            messages.error(request, 'Thought not found.')

    # Get all notes for the current user
    notes = DeathNoteEntry.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'notes': notes
    }
    return render(request, 'death_note.html', context)

from django.shortcuts import render

from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt


# ... your existing views ...

def bubble_pop_game(request):
    """Bubble Pop Game view"""
    return render(request, 'bubble_pop.html')


@csrf_exempt
def save_bubble_score(request):
    """Save bubble pop game score"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            score = data.get('score', 0)
            bubbles_popped = data.get('bubbles_popped', 0)

            # Here you can save to database if you want
            # For example, if you have a GameScore model:
            # GameScore.objects.create(user=request.user, game='bubble_pop', score=score)

            return JsonResponse({
                'status': 'success',
                'score': score,
                'bubbles_popped': bubbles_popped,
                'message': 'Score recorded!'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def get_bubble_high_scores(request):

    high_scores = [
        {'player': 'Player1', 'score': 1500},
        {'player': 'Player2', 'score': 1200},
        {'player': 'Player3', 'score': 900},
        {'player': 'Player4', 'score': 800},
        {'player': 'Player5', 'score': 750},
    ]
    return JsonResponse({'high_scores': high_scores})


# games/views.py
from django.shortcuts import render
from django.views.decorators.http import require_GET

@require_GET
def color_therapy(request):
    """
    Simple color therapy page served from existing 'games' app.
    """
    return render(request, 'color_therapy.html')

from django.shortcuts import render

def memory_match_game(request):

    return render(request, 'memory_match.html')