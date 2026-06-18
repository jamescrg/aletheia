import json

import pytest

from apps.checklists.models import Checklist, ChecklistItem


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
def test_board_card_selection(client, task):
    client.post("/tasks/view-mode/board/")

    # Unselected: select button present, card not marked selected.
    body = client.get("/").content.decode()
    assert f"/tasks/toggle-select/{task.id}/" in body
    assert "importance-4 selected" not in body

    # Toggle selection -> card carries the selected class + checked icon.
    assert client.post(f"/tasks/toggle-select/{task.id}/").status_code == 204
    body = client.get("/").content.decode()
    assert "importance-4 selected" in body
    assert "icon-square-check" in body


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


@pytest.mark.django_db
def test_board_move_to_complete_blocked_by_open_checklist(client, task):
    checklist = Checklist.objects.create(task=task)
    ChecklistItem.objects.create(
        checklist=checklist, description="Unfinished step", item_type="item"
    )
    client.post("/tasks/view-mode/board/")

    resp = client.post(
        "/tasks/board/move/",
        data=json.dumps(
            {"task_id": task.id, "status_slug": "complete", "ordered_ids": [task.id]}
        ),
        content_type="application/json",
    )

    # Move is rejected with a reason for the toast, and status is unchanged.
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "checklist" in body["message"].lower()
    task.refresh_from_db()
    assert task.status == "Pending"
    assert task.date_completed is None
