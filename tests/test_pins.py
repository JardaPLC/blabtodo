"""PINs: their format, and the pause after repeated wrong tries."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from people.models import User
from people.pins import check_adult_pin, pause_after, seconds_paused, validate_pin
from tests.conftest import ADULT_PIN, make_person


@pytest.mark.parametrize("pin", ["1234", "00000", "12345678"])
def test_well_formed_pins_are_accepted(pin):
    validate_pin(pin)


@pytest.mark.parametrize("pin", ["", "123", "123456789", "12a4", "12 34", "١٢٣٤", "-1234"])
def test_malformed_pins_are_refused(pin):
    with pytest.raises(ValidationError):
        validate_pin(pin)


@pytest.mark.parametrize(
    ("failures", "seconds"),
    [(0, 0), (1, 0), (4, 0), (5, 60), (6, 120), (7, 240), (10, 1920), (11, 3600), (40, 3600)],
)
def test_the_pause_starts_at_the_fifth_wrong_try_and_doubles_up_to_an_hour(failures, seconds):
    assert pause_after(failures) == timedelta(seconds=seconds)


@pytest.mark.django_db
def test_the_right_pin_finds_its_adult(adult):
    result = check_adult_pin(ADULT_PIN)

    assert result.adult == adult
    assert result.seconds_paused == 0


@pytest.mark.django_db
def test_a_child_or_someone_who_moved_out_cannot_allow_anything(adult):
    child = make_person("Emma", User.Role.CHILD, "1111")
    moved_out = make_person("Uncle", User.Role.ADULT, "2222")
    moved_out.is_active = False
    moved_out.save()

    assert child.check_pin("1111")
    assert check_adult_pin("1111").adult is None
    assert check_adult_pin("2222").adult is None


@pytest.mark.django_db
def test_four_wrong_tries_cost_nothing_and_the_fifth_starts_a_pause(adult):
    now = timezone.now()

    for _try in range(4):
        assert check_adult_pin("0000", now=now).seconds_paused == 0
    assert seconds_paused(now) == 0

    assert check_adult_pin("0000", now=now).seconds_paused == 60
    assert seconds_paused(now) == 60


@pytest.mark.django_db
def test_during_a_pause_even_the_right_pin_is_not_looked_at(adult):
    now = timezone.now()
    for _try in range(5):
        check_adult_pin("0000", now=now)

    result = check_adult_pin(ADULT_PIN, now=now + timedelta(seconds=30))

    assert result.adult is None
    assert result.seconds_paused == 30


@pytest.mark.django_db
def test_after_the_pause_the_right_pin_works_and_clears_the_count(adult):
    now = timezone.now()
    for _try in range(5):
        check_adult_pin("0000", now=now)
    later = now + timedelta(seconds=61)

    assert check_adult_pin(ADULT_PIN, now=later).adult == adult
    # The count is cleared: four more wrong tries are free again.
    for _try in range(4):
        assert check_adult_pin("0000", now=later).seconds_paused == 0


@pytest.mark.django_db
def test_each_further_wrong_try_doubles_the_pause(adult):
    now = timezone.now()
    for _try in range(5):
        check_adult_pin("0000", now=now)

    after_first_pause = now + timedelta(seconds=61)

    assert check_adult_pin("0000", now=after_first_pause).seconds_paused == 120
