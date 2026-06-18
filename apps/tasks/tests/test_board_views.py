import json

import pytest


@pytest.mark.django_db
def test_board_view_renders(client, task):
    # Switch to board mode
    resp = client.post("/tasks/view-mode/board/")
    assert resp.status_code == 204
    assert resp.headers.get("HX-Trigger") == "tasksListChanged"

    # Index now renders the board with the task's column
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert 'id="tasks-board"' in body
    assert 'data-status-slug="pending"' in body
    assert f'data-task-id="{task.id}"' in body
    # All four columns present
    for slug in ("pending", "in-progress", "on-hold", "complete"):
        assert f'data-status-slug="{slug}"' in body


@pytest.mark.django_db
def test_board_move_changes_status_and_order(client, task):
    client.post("/tasks/view-mode/board/")
    resp = client.post(
        "/tasks/board/move/",
        data=json.dumps(
            {"task_id": task.id, "status_slug": "in-progress", "ordered_ids": [task.id]}
        ),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    task.refresh_from_db()
    assert task.status == "In progress"
    assert task.custom_order == 0


@pytest.mark.django_db
def test_board_move_to_complete_sets_completed_date(client, task):
    client.post("/tasks/view-mode/board/")
    client.post(
        "/tasks/board/move/",
        data=json.dumps(
            {"task_id": task.id, "status_slug": "complete", "ordered_ids": [task.id]}
        ),
        content_type="application/json",
    )
    task.refresh_from_db()
    assert task.status == "Complete"
    assert task.date_completed is not None


@pytest.mark.django_db
def test_view_mode_rejects_unknown(client):
    resp = client.post("/tasks/view-mode/bogus/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_quick_filter_keeps_board_view(client, task):
    client.post("/tasks/view-mode/board/")
    resp = client.post("/tasks/filter/quick/all")
    assert resp.status_code == 200
    assert 'id="tasks-board"' in resp.content.decode()
