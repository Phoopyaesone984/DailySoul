from django.urls import path
from . import views


urlpatterns=[
    path('', views.home, name='home'),
    path('affirmations/',views.affirmations_page,name='affirmations'),
    path('draw/',views.draw_affirmation,name='draw_affirmation'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('register/',views.register_view,name='register'),
]

