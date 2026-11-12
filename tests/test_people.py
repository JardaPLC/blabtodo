"""People. In milestone 0 only one thing matters: the project has its own user model."""

import pytest

from people.models import User


@pytest.mark.django_db
def test_project_uses_its_own_user_model(django_user_model):
    assert django_user_model is User

    user = User.objects.create_user(username="parent", password="a-long-passphrase")

    assert user.check_password("a-long-passphrase")
