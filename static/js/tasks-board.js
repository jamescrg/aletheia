// SortableJS integration for the tasks Kanban board.
// Drag a card between columns to change its status; reorder within a column to
// set priority. Order + status are persisted via POST /tasks/board/move/.
// Shift-click selects cards; dragging any selected card moves the whole
// selection to the dropped column at once (POST /tasks/board/bulk-move/).
(function () {
  function getCSRFToken() {
    var body = document.querySelector("body");
    var hxHeaders = body && body.getAttribute("hx-headers");
    if (hxHeaders) {
      try {
        return JSON.parse(hxHeaders)["X-CSRFToken"] || "";
      } catch (e) {
        /* ignore */
      }
    }
    return "";
  }

  function updateColumnCounts(board) {
    board.querySelectorAll(".kanban-column").forEach(function (column) {
      var count = column.querySelectorAll(".kanban-card").length;
      var badge = column.querySelector(".kanban-column-count");
      if (badge) badge.textContent = count;
    });
  }

  // Fill the viewport: the board runs from its top edge to the bottom of the
  // window (less a small gutter), so columns are full-height and scroll
  // internally. Measured rather than hard-coded so it survives the dev banner,
  // toolbar height changes, and the collapsible sidebar.
  function sizeBoard() {
    var board = document.getElementById("tasks-board");
    if (!board) return;
    var top = board.getBoundingClientRect().top;
    board.style.height = Math.max(240, window.innerHeight - top - 24) + "px";
  }

  // Toggle a card's selection in the session (shift-click). The card's
  // .selected class is toggled optimistically by the caller for instant
  // feedback, so here we only persist and then refresh the toolbar (bulk
  // actions + count) — not the whole board, which would re-render every card
  // and re-init every Sortable on each click.
  function syncSelect(taskId) {
    fetch("/tasks/toggle-select/" + taskId + "/", {
      method: "POST",
      headers: { "X-CSRFToken": getCSRFToken() },
    }).finally(function () {
      htmx.ajax("GET", "/tasks/toolbar/", {
        target: "#tasks-toolbar",
        swap: "outerHTML",
      });
    });
  }

  // Move every selected card to a column in one go (bulk drag). The selection
  // already lives in the session; we just send the destination status.
  function persistBulkMove(statusSlug) {
    fetch("/tasks/board/bulk-move/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ status_slug: statusSlug }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data && data.skipped && data.message && typeof Toast !== "undefined") {
          Toast.warning(data.message);
        }
      })
      .finally(function () {
        // Reconcile order + clear the selection from the server's truth.
        htmx.trigger(document.body, "tasksListChanged");
      });
  }

  function persistMove(board, item, to) {
    var statusSlug = to.dataset.statusSlug;
    var orderedIds = Array.from(to.querySelectorAll(".kanban-card")).map(function (c) {
      return c.dataset.taskId;
    });

    // Optimistic UI: reflect the new column's state immediately.
    item.classList.toggle("complete", statusSlug === "complete");
    if (statusSlug === "complete") item.classList.remove("past-due");
    updateColumnCounts(board);

    fetch("/tasks/board/move/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({
        task_id: item.dataset.taskId,
        status_slug: statusSlug,
        ordered_ids: orderedIds,
      }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!data || !data.ok) {
          // Toast is a top-level const in toasts.js — a global binding, not a
          // window property — so reach it by name, not via window.Toast.
          if (data && data.message && typeof Toast !== "undefined") {
            Toast.warning(data.message);
          }
          // Re-render the board from the server's truth to undo the drop.
          htmx.trigger(document.body, "tasksListChanged");
        }
      })
      .catch(function () {
        htmx.trigger(document.body, "tasksListChanged");
      });
  }

  function selectedCards(board) {
    return board.querySelectorAll(".kanban-card.selected");
  }

  function initTaskBoard() {
    var board = document.getElementById("tasks-board");
    if (!board) return;

    // The whole card is the drag handle (Jira-style). A plain click opens the
    // editor; a shift-click toggles selection; a drag (past fallbackTolerance)
    // moves the card and is followed by a suppressed click so the drop doesn't
    // also open the editor.
    if (!board.dataset.clickInit) {
      board.dataset.clickInit = "1";
      board.addEventListener("click", function (e) {
        if (board._suppressClick) return;
        var card = e.target.closest(".kanban-card");
        // Shift-click toggles selection instead of opening the editor.
        if (e.shiftKey) {
          if (card) {
            e.preventDefault();
            // Optimistic: highlight immediately, then persist + refresh the
            // toolbar in the background so selection feels instant.
            card.classList.toggle("selected");
            syncSelect(card.dataset.taskId);
          }
          return;
        }
        // Let the checklist/notes buttons + the column "+" self-handle.
        if (e.target.closest("a, button")) return;
        if (!card) return;
        var url = card.dataset.editUrl;
        if (url) htmx.ajax("GET", url, { target: "#htmx-modal-container" });
      });
    }

    board.querySelectorAll(".kanban-column-cards").forEach(function (list) {
      if (list.dataset.sortableInit) return;
      list.dataset.sortableInit = "1";
      Sortable.create(list, {
        group: "tasks",
        animation: 150,
        ghostClass: "sortable-ghost",
        dragClass: "sortable-drag",
        draggable: ".kanban-card",
        // Don't start a drag from the interactive controls (priority dropdown,
        // checklist/notes buttons); let their click (and htmx request) through.
        filter: ".kanban-card-btn, .kanban-card-priority",
        preventOnFilter: false,
        // Sortable's own drag impl with a small pixel threshold so a click
        // (under 5px of movement) never registers as a drag.
        forceFallback: true,
        fallbackTolerance: 5,
        // Show the grabbing cursor only once a drag is actually under way,
        // not on hover. When dragging one of several selected cards, dress the
        // drag as a moving stack: dim the other selected cards in place and put
        // a stacked shadow + count badge on the floating clone.
        onStart: function (evt) {
          document.body.classList.add("kanban-dragging");
          var selected = selectedCards(board);
          if (!(evt.item.classList.contains("selected") && selected.length > 1)) {
            return;
          }
          document.body.classList.add("kanban-bulk-dragging");
          selected.forEach(function (c) {
            if (c !== evt.item) c.classList.add("bulk-drag-source");
          });
          var addBadge = function () {
            var clone = document.querySelector(".kanban-card.sortable-fallback");
            if (!clone || clone.querySelector(".bulk-drag-count")) return;
            var badge = document.createElement("span");
            badge.className = "bulk-drag-count";
            badge.textContent = selected.length;
            clone.appendChild(badge);
          };
          addBadge();
          // The fallback clone may not exist yet on the first tick.
          if (!document.querySelector(".kanban-card.sortable-fallback")) {
            requestAnimationFrame(addBadge);
          }
        },
        onEnd: function (evt) {
          var wasBulk = document.body.classList.contains("kanban-bulk-dragging");
          document.body.classList.remove("kanban-dragging", "kanban-bulk-dragging");
          board.querySelectorAll(".bulk-drag-source").forEach(function (c) {
            c.classList.remove("bulk-drag-source");
          });
          board._suppressClick = true;
          setTimeout(function () {
            board._suppressClick = false;
          }, 100);
          // Dragging any selected card with a multi-selection active moves the
          // whole selection to the dropped column; otherwise it's a single move.
          if (wasBulk) {
            persistBulkMove(evt.to.dataset.statusSlug);
          } else {
            persistMove(board, evt.item, evt.to);
          }
        },
      });
    });

    sizeBoard();
  }

  document.addEventListener("DOMContentLoaded", initTaskBoard);
  window.addEventListener("resize", sizeBoard);
  // Re-init after any swap that brings the board into the DOM. Two paths reach
  // here: the #tasks div reloading itself (list⇄board toggle, filter changes)
  // where target.id === "tasks"; and the hx-boosted sidebar nav, which swaps the
  // whole page into #main-content — there target is the container, so we look for
  // the board *inside* the swapped subtree. Without this second case the board
  // renders on first navigation but never gets its SortableJS handlers, so cards
  // won't drag until a full page refresh. initTaskBoard() is idempotent.
  document.body.addEventListener("htmx:afterSwap", function (event) {
    var t = event.target;
    if (!t) return;
    if (t.id === "tasks" || (t.querySelector && t.querySelector("#tasks-board"))) {
      initTaskBoard();
    }
  });
})();
