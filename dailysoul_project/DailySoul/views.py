from django.shortcuts import render
from django.http import JsonResponse
from .models import Affirmation
import random


def home(request):
    return render(request, 'home.html')


def affirmations_page(request):
    return render(request, 'affirmations.html')


def draw_affirmation(request):
    """Return a random affirmation from database."""
    affirmations = list(Affirmation.objects.all())
    if not affirmations:
        return JsonResponse({'affirmation': "No affirmations yet.", 'image': '', 'category': ''})

    card = random.choice(affirmations)
    return JsonResponse({
        'affirmation': card.text,
        'image': card.image.url if card.image else '',
        'category': card.category
    })