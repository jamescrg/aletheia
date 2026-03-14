// SortableJS integration for checklist template item ordering

function initializeTemplateItemsSortable() {
    const list = document.getElementById('template-items-sortable');
    if (!list) return;

    Sortable.create(list, {
        handle: '.template-item-handle',
        animation: 150,
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',

        onEnd: function() {
            const items = list.querySelectorAll('li[data-item-id]');
            const itemIds = Array.from(items).map(li => li.dataset.itemId);
            const templateId = list.dataset.templateId;

            // Update visible numbers
            items.forEach(function(li, index) {
                const numberSpan = li.querySelector('.template-item-number');
                if (numberSpan) numberSpan.textContent = (index + 1) + '.';
            });

            const bodyElement = document.querySelector('body');
            const hxHeaders = bodyElement.getAttribute('hx-headers');
            let csrfToken = '';
            if (hxHeaders) {
                try {
                    csrfToken = JSON.parse(hxHeaders)['X-CSRFToken'] || '';
                } catch (e) { /* ignore */ }
            }

            fetch('/settings/checklists/' + templateId + '/items/reorder/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ item_ids: itemIds })
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeTemplateItemsSortable);
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.target.id === 'template-items' || event.target.id === 'htmx-modal-container') {
        initializeTemplateItemsSortable();
    }
});
