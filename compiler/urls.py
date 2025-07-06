from django.urls import path
from . import views

app_name = 'compiler'
urlpatterns = [
    path('run/',views.run_code, name = 'run_code'),
    path('submit/',views.submit_code, name = 'submit_code'),
    path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'), 

]