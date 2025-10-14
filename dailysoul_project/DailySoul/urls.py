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
    path('api/draw-luck/', views.draw_luck_api, name='api_draw_luck'),
]
