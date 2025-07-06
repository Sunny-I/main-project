from . import views
from django.urls import path,include


urlpatterns = [
    path('my_submissons/', views.my_submissions, name= 'my_submissions'),
    path('<int:submission_id>/', views.submission_detail, name='submission_detail'),
]