from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, ContentType

CustomUser = get_user_model()

@receiver(post_save, sender=CustomUser)
def set_permissions(sender, instance, created, **kwargs):
    if created:
        instance.is_staff = True
        instance.is_agent = True
        instance.save()
        # Only give view permission for CustomUser
        view_perm = Permission.objects.get(codename='view_customuser')
        # Get all permissions for other models in rentcars except CustomUser
        other_perms = Permission.objects.filter(
            content_type__app_label='rentcars'
        ).exclude(content_type=ContentType.objects.get_for_model(CustomUser))
        # Combine permissions
        perms = list(other_perms) + [view_perm]
        instance.user_permissions.set(perms)