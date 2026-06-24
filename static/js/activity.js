

function updateRate(){
    /**
     * Update the rate on the time entry form.
     *
     * Changes the value of the "id_rate" input
     * Should be triggered when the "Matter" select input changes.
     *
     * Makes an AJAX request to fetch the rate for the selected matter.
     */
    var matterElement = document.getElementById("id_matter");
    var matterId = matterElement.options[matterElement.selectedIndex].value;

    if (matterId) {
        fetch(`/activity/time/set-rate/${matterId}`)
            .then(response => response.text())
            .then(rate => {
                document.getElementById("id_rate").value = rate;
            })
            .catch(error => {
                console.error('Error fetching rate:', error);
            });
    }

}


// Abbreviation codes cache
let abbreviationCodes = null;

/**
 * Initialize abbreviation preview functionality
 * Fetches abbreviation codes and sets up event listener on the actions textarea
 */
function initAbbreviationPreview() {
    const actionsTextarea = document.getElementById('id_actions');
    const previewContainer = document.getElementById('actions-preview');
    const previewBody = document.getElementById('actions-preview-body');
    const previewText = document.getElementById('actions-preview-text');
    const applyCheckbox = document.getElementById('id_apply_codes');

    if (!actionsTextarea || !previewContainer || !previewBody || !previewText) {
        return; // Elements not found, exit early
    }

    // Fetch abbreviation codes if not already cached
    if (!abbreviationCodes) {
        fetch('/activity/time/codes/json/')
            .then(response => response.json())
            .then(codes => {
                abbreviationCodes = codes;
                updatePreview(); // Update preview with initial value
            })
            .catch(error => {
                console.error('Error fetching abbreviation codes:', error);
            });
    }

    // Function to update the preview
    function updatePreview() {
        if (!abbreviationCodes) return;

        const originalText = actionsTextarea.value;

        let expandedText = originalText;
        for (const [code, expansion] of Object.entries(abbreviationCodes)) {
            expandedText = expandedText.replaceAll(code, expansion);
        }

        // The whole row (checkbox + preview) only appears when there's actually
        // something to expand.
        const hasCodes = originalText.trim() && expandedText !== originalText;
        if (!hasCodes) {
            previewContainer.style.display = 'none';
            return;
        }
        previewContainer.style.display = 'flex';

        // The expanded text shows only when expansion is enabled; the checkbox
        // stays visible either way so it can be toggled back on.
        if (applyCheckbox && !applyCheckbox.checked) {
            previewBody.style.display = 'none';
        } else {
            previewText.textContent = expandedText;
            previewBody.style.display = '';
        }
    }

    // Add event listener for input changes
    actionsTextarea.addEventListener('input', updatePreview);

    // Toggle the preview when the apply-codes checkbox changes
    if (applyCheckbox) {
        applyCheckbox.addEventListener('change', updatePreview);
    }

    // Update preview on initial load (for edit mode)
    updatePreview();
}

// Initialize preview when modal content is loaded
document.body.addEventListener('htmx:afterSettle', function(event) {
    // Check if the time entry form was loaded
    if (document.getElementById('time-entry-form')) {
        initAbbreviationPreview();
    }
});
