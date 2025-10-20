from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('affirmations/', views.affirmations_page, name='affirmations'),
    path('draw_affirmation/', views.draw_affirmation, name='draw_affirmation'),
    path('api/get-piles/', views.api_get_piles, name='api_get_piles'),
    path('journal/', views.journal, name='journal'),
    path('deathnote/', views.deathnote, name='death_note'),
    path('mini_games/', views.mini_games, name='mini_games'),
    path('games/bubble-pop/', views.bubble_pop_game, name='bubble_pop'),
    path('games/bubble-pop/save-score/', views.save_bubble_score, name='save_bubble_score'),
    path('games/bubble-pop/high-scores/', views.get_bubble_high_scores, name='get_bubble_high_scores'),
]
