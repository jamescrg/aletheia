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

    const contactIdInput = document.getElementById("contact_id");
    const clearBtn = document.getElementById("combobox-clear");
    const resultsContainer = document.getElementById("search-results");

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
     * Select a contact from the results
     * Sets the hidden input value and displays the selected name
     */
    const selectContact = (contactId, contactName) => {
        // Set the hidden input value
        if (contactIdInput) {
            contactIdInput.value = contactId;
        }

        // Display the selected name in the input
        input.value = contactName;
        input.classList.add("selected");
        input.setAttribute("readonly", "readonly");

        // Show the clear button
        if (clearBtn) {
            clearBtn.classList.remove("hidden");
        }

        // Clear the search results
        if (resultsContainer) {
            resultsContainer.innerHTML = "";
        }

        // Reset focus index
        focusedIndex = -1;
    };

    /**
     * Clear the selection and allow re-searching
     */
    const clearSelection = () => {
        // Clear the hidden input
        if (contactIdInput) {
            contactIdInput.value = "";
        }

        // Clear and enable the search input
        input.value = "";
        input.classList.remove("selected");
        input.removeAttribute("readonly");
        input.focus();

        // Hide the clear button
        if (clearBtn) {
            clearBtn.classList.add("hidden");
        }

        // Clear results
        if (resultsContainer) {
            resultsContainer.innerHTML = "";
        }

        focusedIndex = -1;
    };

    // Handle clear button click
    if (clearBtn) {
        clearBtn.addEventListener("click", (e) => {
            e.preventDefault();
            clearSelection();
        });
    }

    // Handle clicking on a result
    if (resultsContainer) {
        resultsContainer.addEventListener("click", (e) => {
            const link = e.target.closest("a[data-contact-id]");
            if (link) {
                e.preventDefault();
                const contactId = link.dataset.contactId;
                const contactName = link.dataset.contactName;
                selectContact(contactId, contactName);
            }
        });
    }

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
            // Get the data attributes and select the contact
            const selectedItem = items[focusedIndex];
            const contactId = selectedItem.dataset.contactId;
            const contactName = selectedItem.dataset.contactName;
            selectContact(contactId, contactName);
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
