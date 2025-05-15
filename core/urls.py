# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # other paths...
]

# core/urls.py
urlpatterns += [
    path('events/', views.events_list, name='events'),
    path('events/<int:pk>/start/', views.start_attendance, name='start_attendance'),
    path('api/events/<int:pk>/stream/', views.stream_frame, name='stream_frame'),
    path('attendance/', views.attendance_history, name='attendance_history'),
]
