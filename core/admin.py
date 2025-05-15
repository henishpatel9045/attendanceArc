from django.contrib import admin
from .models import Person, Event, Attendance

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'number')
    fields = ('name', 'number', 'image1', 'image2', 'image3')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('person', 'event', 'timestamp')
