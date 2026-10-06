from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    # Login saves last_login too, including for older users without a profile.
    Profile.objects.using(using).get_or_create(user=instance)
