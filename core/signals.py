# myapp/signals.py
from .views import face_recognizer
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Person
import pickle

@receiver(post_delete, sender=Person)
def delete_image_file_on_delete(sender, instance: Person, **kwargs):
    if instance.image1:
        instance.image1.delete(save=False)
    if instance.image2:
        instance.image2.delete(save=False)
    if instance.image3:
        instance.image3.delete(save=False)

@receiver(pre_save, sender=Person)
def delete_old_image_on_change(sender, instance: Person, **kwargs):
    if not instance.pk:
        # If new object, nothing to delete yet
        return
    try:
        old = {Person}.objects.get(pk=instance.pk)
    except Person.DoesNotExist:
        return
    # Compare old file name to new one; if changed, delete old
    if old.image1 and old.image1 != instance.image1:
        old.image1.delete(save=False)
    if old.image2 and old.image2 != instance.image2:
        old.image2.delete(save=False)
    if old.image3 and old.image3 != instance.image3:
        old.image3.delete(save=False)
    # If the image is deleted, remove it from the embeddings
    if old.image1 != instance.image1 or old.image2 != instance.image2 or old.image3 != instance.image3:
        embs = face_recognizer.get_embeddings(person=instance)
        face_recognizer.embeddings[instance.id] = embs
        with open(face_recognizer.pickle_file_path, 'wb') as f:
            pickle.dump(face_recognizer.embeddings, f)

@receiver(post_save, sender=Person)
def photo_post_save_handler(sender, instance: Person, created, **kwargs):
    if created:
        embs = face_recognizer.get_embeddings(person=instance)
        if embs:
            face_recognizer.embeddings[instance.id] = embs
            # Save the embeddings to a pickle file
            with open(face_recognizer.pickle_file_path, 'wb') as f:
                pickle.dump(face_recognizer.embeddings, f)
        print(f"New photo created: {instance}")
