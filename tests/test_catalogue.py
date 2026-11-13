"""The starter catalogue of tasks and rooms, and names in several languages."""

import pytest
from django.utils import translation

from tasks import catalogue
from tasks.forms import NamesField, NamesWidget
from tasks.models import pick_name


def test_every_key_is_used_once():
    for entries in (catalogue.TASKS, catalogue.ROOMS):
        keys = [entry.key for entry in entries]
        assert len(keys) == len(set(keys))


def test_every_task_points_at_a_room_that_exists():
    for entry in catalogue.TASKS:
        assert entry.room is None or entry.room in catalogue.ROOMS_BY_KEY, entry.key


def test_every_entry_has_a_picture_and_a_sensible_effort():
    for entry in catalogue.TASKS + catalogue.ROOMS:
        assert entry.emoji
        assert entry.effort in (1, 2, 3)


@pytest.mark.parametrize("entry", catalogue.TASKS + catalogue.ROOMS, ids=lambda entry: entry.key)
def test_every_entry_has_a_czech_name_of_its_own(entry):
    names = entry.names()

    assert set(names) == {"cs", "en"}
    assert names["cs"] and names["en"]
    assert names["cs"] != names["en"], "the Czech name is missing"


def test_names_are_the_same_whatever_language_is_active_when_they_are_read():
    entry = catalogue.TASKS_BY_KEY["water-plants"]

    with translation.override("en"):
        assert entry.names() == {"cs": "Zalít květiny", "en": "Water the plants"}


def test_the_drop_down_is_sorted_by_name_in_the_current_language():
    labels = [label.split("  ", 1)[1] for _key, label in catalogue.choices(catalogue.ROOMS)]

    assert labels == sorted(labels, key=str.casefold)
    assert "Kuchyně" in labels


def test_a_name_falls_back_to_the_default_language_and_then_to_any():
    assert pick_name({"cs": "Zalít", "en": "Water"}, "en") == "Water"
    assert pick_name({"cs": "Zalít"}, "en") == "Zalít"
    assert pick_name({"en": "Water"}, "cs") == "Water"
    assert pick_name({}, "cs") == ""


def test_names_typed_in_several_boxes_become_one_record():
    field = NamesField()

    assert field.clean(["  Zalít květiny ", "Water the plants"]) == {
        "cs": "Zalít květiny",
        "en": "Water the plants",
    }
    assert field.clean(["Zalít květiny", ""]) == {"cs": "Zalít květiny"}
    assert field.clean(["", ""]) == {}


def test_a_stored_name_fills_the_boxes_again():
    assert NamesWidget().decompress({"en": "Water"}) == ["", "Water"]
    assert NamesWidget().decompress(None) == ["", ""]
