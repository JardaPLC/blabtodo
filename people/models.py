from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    A family member.

    The project has its own user model from the first migration, because Django makes it
    hard to switch later. Display names, roles, faces and PINs arrive in milestone 1.
    """
