from django.urls import path
from . import views

app_name = 'compiler'  # This line is crucial

urlpatterns = [
    path('', views.problem_list, name='problem_list'),
    path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'),
    path('submit/<int:problem_id>/', views.submit_code, name='submit_code'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('submissions/', views.user_submissions, name='user_submissions'),
]