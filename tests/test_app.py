import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import date, timedelta

from app import app, task_due


def test_health_endpoint():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_new_task_is_due():
    assert task_due({"last_completed": None, "interval_days": 7}) is True


def test_recent_task_is_not_due():
    assert task_due({"last_completed": date.today().isoformat(), "interval_days": 7}) is False


def test_old_task_is_due():
    old_date = (date.today() - timedelta(days=8)).isoformat()
    assert task_due({"last_completed": old_date, "interval_days": 7}) is True
