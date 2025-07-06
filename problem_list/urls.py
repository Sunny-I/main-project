from django.urls import path,include
from django.conf import settings
from . import views

urlpatterns = [
        path('', views.problem_list, name = 'problems_list'),
        path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'), 
]