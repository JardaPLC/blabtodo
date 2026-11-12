"""The address the host uses to see whether the app is alive."""

import pytest


@pytest.mark.django_db
def test_health_reports_ok(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "test"}


def test_health_reports_a_database_failure(client, monkeypatch):
    monkeypatch.setattr("household.views._database_ok", lambda: False)

    response = client.get("/health/")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
