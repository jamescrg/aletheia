/**
 * Keyboard navigation for search combobox
 *
 * This script adds keyboard support to the "Assign Contact" search modal:
 * - Arrow Down: highlight the next result in the list
 * - Arrow Up: highlight the previous result (or return to input)
 * - Enter: select the highlighted result
 * - Escape: clear highlighting and return focus to input
 */

const initCombobox = () => {
    // Find the search input element by its ID
    // If it doesn't exist on this page, exit early (do nothing)
    const input = document.getElementById("assign-search-input");
    if (!input) return;

    /**
     * Get all the clickable result links from the search results
     * This is a function (not a variable) because results change dynamically
     * as the user types and HTMX updates the list
     */
    const getResults = () => {
        const container = document.getElementById("search-results");
        // querySelectorAll returns all <a> tags inside <li> tags inside .assign-results
        return container ? container.querySelectorAll(".assign-results li a") : [];
    };

    // Track which result is currently highlighted
    // -1 means nothing is highlighted (focus is on the input)
    let focusedIndex = -1;

    /**
     * Update the visual highlighting on results
     * Adds "focused" class to the current item, removes it from all others
     */
    const updateFocus = (items) => {
        items.forEach((item, i) => {
            if (i === focusedIndex) {
                // Highlight this item
                item.classList.add("focused");
                // Scroll it into view if it's outside the visible area
                item.scrollIntoView({ block: "nearest" });
            } else {
                // Remove highlight from all other items
                item.classList.remove("focused");
            }
        });
    };

    /**
     * Listen for keyboard events on the search input
     * This is where the arrow key navigation happens
     */
    input.addEventListener("keydown", (e) => {
        // Get the current list of results (may have changed since last keypress)
        const items = getResults();

        // If there are no results, don't do anything special
        if (items.length === 0) return;

        if (e.key === "ArrowDown") {
            // Prevent the cursor from moving to the end of the input text
            e.preventDefault();
            // Move to next item, but don't go past the last one
            // Math.min picks the smaller of the two numbers
            focusedIndex = Math.min(focusedIndex + 1, items.length - 1);
            updateFocus(items);
        }
        else if (e.key === "ArrowUp") {
            // Prevent default cursor behavior
            e.preventDefault();
            // Move to previous item, but don't go below -1 (the input)
            // Math.max picks the larger of the two numbers
            focusedIndex = Math.max(focusedIndex - 1, -1);
            updateFocus(items);
            // If we've moved back to -1, make sure focus is on the input
            if (focusedIndex === -1) {
                input.focus();
            }
        }
        else if (e.key === "Enter" && focusedIndex >= 0) {
            // Only act on Enter if something is highlighted
            e.preventDefault();
            // Simulate a click on the highlighted item
            // This triggers the HTMX request to load the role selection modal
            items[focusedIndex].click();
        }
        else if (e.key === "Escape") {
            // Clear the highlighting and return to input
            focusedIndex = -1;
            updateFocus(items);
            input.focus();
        }
        // Any other key (like typing letters) is handled normally by the browser
    });

    /**
     * Reset the highlight when search results change
     * HTMX fires "htmx:afterSwap" after it updates content on the page
     */
    document.body.addEventListener("htmx:afterSwap", (e) => {
        // Only reset if the search-results container was updated
        if (e.detail.target.id === "search-results") {
            focusedIndex = -1;
        }
    });
};

// Run initCombobox when the page first loads
document.addEventListener("DOMContentLoaded", initCombobox);

// Also run it after HTMX loads new content (like when the modal opens)
// "htmx:afterSettle" fires after HTMX has finished updating the DOM
document.body.addEventListener("htmx:afterSettle", initCombobox);
