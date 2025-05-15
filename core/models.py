from django.db import models

class Person(models.Model):
    def folder_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return f'persons/{instance.id}/{filename}'
    
    
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, unique=True)
    image1 = models.ImageField(upload_to=folder_path, null=True, blank=True)
    image2 = models.ImageField(upload_to=folder_path, null=True, blank=True)
    image3 = models.ImageField(upload_to=folder_path, null=True, blank=True)


    def __str__(self):
        return f"{self.name} ({self.number})"

class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"{self.title} on {self.date}"

class Attendance(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('person', 'event')
