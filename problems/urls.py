from django.urls import path
from . import views

urlpatterns = [
    path('', views.problems_list, name='problems_list'),
    path('<slug:slug>/', views.problem_detail, name='problem_detail'),  
]
