from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('upload/', views.upload_ppt_view, name='upload'),
    path('summary/<int:session_id>/', views.summary_view, name='summary'),
    path('quiz/<int:session_id>/', views.quiz_view, name='quiz'),
    path('quiz/<int:session_id>/api/', views.quiz_data_api, name='quiz_data_api'),
    path('quiz/<int:session_id>/results/', views.quiz_submit_view, name='quiz_results'),
    path('live-converter/', views.animation_view, name='animation'),
    path('history/', views.history_view, name='history'),
]
