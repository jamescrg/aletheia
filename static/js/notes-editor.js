// Tiptap ESM imports from esm.sh CDN
import { Editor } from "https://esm.sh/@tiptap/core@2";
import Document from "https://esm.sh/@tiptap/extension-document@2";
import Paragraph from "https://esm.sh/@tiptap/extension-paragraph@2";
import Text from "https://esm.sh/@tiptap/extension-text@2";
import Bold from "https://esm.sh/@tiptap/extension-bold@2";
import Italic from "https://esm.sh/@tiptap/extension-italic@2";
import Strike from "https://esm.sh/@tiptap/extension-strike@2";
import Heading from "https://esm.sh/@tiptap/extension-heading@2";
import BulletList from "https://esm.sh/@tiptap/extension-bullet-list@2";
import OrderedList from "https://esm.sh/@tiptap/extension-ordered-list@2";
import ListItem from "https://esm.sh/@tiptap/extension-list-item@2";
import Blockquote from "https://esm.sh/@tiptap/extension-blockquote@2";
import HardBreak from "https://esm.sh/@tiptap/extension-hard-break@2";
import History from "https://esm.sh/@tiptap/extension-history@2";
import Dropcursor from "https://esm.sh/@tiptap/extension-dropcursor@2";
import Gapcursor from "https://esm.sh/@tiptap/extension-gapcursor@2";

let editor = null;
let autosaveTimer = null;
let lastSavedContent = "";
let currentRefType = "document";

// Initialize editor
function initEditor() {
  const container = document.getElementById("note-editor");
  if (!container || !window.NOTE_DATA) return;

  // Parse initial content - convert markdown references to HTML
  let initialContent = window.NOTE_DATA.content || "";
  initialContent = markdownToHtml(initialContent);

  editor = new Editor({
    element: container,
    extensions: [
      Document,
      Paragraph,
      Text,
      Bold,
      Italic,
      Strike,
      Heading.configure({ levels: [1, 2, 3] }),
      BulletList,
      OrderedList,
      ListItem,
      Blockquote,
      HardBreak,
      History,
      Dropcursor,
      Gapcursor,
    ],
    content: initialContent,
    autofocus: true,
    onUpdate: function () {
      scheduleAutosave();
    },
  });

  lastSavedContent = getMarkdownContent();
  setupToolbar();
  setupKeyboardShortcuts();
  setupReferencePicker();
}

// Convert simple markdown to HTML for editor
function markdownToHtml(md) {
  if (!md) return "<p></p>";

  // Convert reference syntax to spans
  md = md.replace(
    /\[\[doc:(\d+)\|([^\]]+)\]\]/g,
    '<span class="note-ref" data-type="document" data-id="$1">$2</span>'
  );
  md = md.replace(
    /\[\[hl:(\d+)\|([^\]]+)\]\]/g,
    '<span class="note-ref" data-type="highlight" data-id="$1">$2</span>'
  );

  // Simple markdown conversion
  let html = md
    // Headers
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold and italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/~~(.+?)~~/g, "<s>$1</s>")
    // Blockquotes
    .replace(/^> (.+)$/gm, "<blockquote><p>$1</p></blockquote>")
    // Lists (simplified)
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/^(\d+)\. (.+)$/gm, "<li>$2</li>");

  // Wrap loose text in paragraphs
  const lines = html.split("\n");
  const wrapped = lines
    .map(function (line) {
      line = line.trim();
      if (!line) return "";
      if (line.match(/^<(h[1-3]|li|blockquote|ul|ol)/)) return line;
      if (!line.startsWith("<")) return "<p>" + line + "</p>";
      return line;
    })
    .filter(function (line) {
      return line;
    })
    .join("");

  return wrapped || "<p></p>";
}

// Convert editor HTML to markdown
function htmlToMarkdown(html) {
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;

  function processNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return "";

    const tag = node.tagName.toLowerCase();
    const children = Array.from(node.childNodes).map(processNode).join("");

    switch (tag) {
      case "h1":
        return "# " + children + "\n\n";
      case "h2":
        return "## " + children + "\n\n";
      case "h3":
        return "### " + children + "\n\n";
      case "p":
        return children + "\n\n";
      case "strong":
        return "**" + children + "**";
      case "em":
        return "*" + children + "*";
      case "s":
        return "~~" + children + "~~";
      case "blockquote":
        return (
          children
            .trim()
            .split("\n")
            .map(function (line) {
              return "> " + line;
            })
            .join("\n") + "\n\n"
        );
      case "ul":
        return children;
      case "ol":
        return children;
      case "li":
        const parent = node.parentElement;
        if (parent && parent.tagName.toLowerCase() === "ol") {
          const index = Array.from(parent.children).indexOf(node) + 1;
          return index + ". " + children.trim() + "\n";
        }
        return "- " + children.trim() + "\n";
      case "br":
        return "\n";
      case "span":
        if (node.classList.contains("note-ref")) {
          const refType = node.dataset.type;
          const refId = node.dataset.id;
          const label = children;
          if (refType === "document") {
            return "[[doc:" + refId + "|" + label + "]]";
          } else if (refType === "highlight") {
            return "[[hl:" + refId + "|" + label + "]]";
          }
        }
        return children;
      default:
        return children;
    }
  }

  let markdown = processNode(tempDiv);
  // Clean up multiple newlines
  markdown = markdown.replace(/\n{3,}/g, "\n\n").trim();
  return markdown;
}

function getMarkdownContent() {
  if (!editor) return "";
  const html = editor.getHTML();
  return htmlToMarkdown(html);
}

// Autosave with debounce
function scheduleAutosave() {
  if (autosaveTimer) clearTimeout(autosaveTimer);
  updateSaveStatus("Unsaved changes...");
  autosaveTimer = setTimeout(performAutosave, 2000);
}

function performAutosave() {
  const content = getMarkdownContent();
  if (content === lastSavedContent) {
    updateSaveStatus("Saved");
    return;
  }

  updateSaveStatus("Saving...");

  const formData = new FormData();
  formData.append("content", content);

  fetch(window.NOTE_DATA.autosaveUrl, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
    body: formData,
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      if (data.saved) {
        lastSavedContent = content;
        updateSaveStatus("Saved");
      }
    })
    .catch(function () {
      updateSaveStatus("Save failed");
    });
}

function updateSaveStatus(message) {
  const el = document.getElementById("save-status");
  if (el) el.textContent = message;
}

function getCSRFToken() {
  const el = document.querySelector("[name=csrfmiddlewaretoken]");
  return el ? el.value : "";
}

// Toolbar setup
function setupToolbar() {
  const btnBold = document.getElementById("btn-bold");
  const btnItalic = document.getElementById("btn-italic");
  const btnStrike = document.getElementById("btn-strike");
  const btnH1 = document.getElementById("btn-heading-1");
  const btnH2 = document.getElementById("btn-heading-2");
  const btnH3 = document.getElementById("btn-heading-3");
  const btnBullet = document.getElementById("btn-bullet-list");
  const btnOrdered = document.getElementById("btn-ordered-list");
  const btnQuote = document.getElementById("btn-blockquote");

  if (btnBold) {
    btnBold.addEventListener("click", function () {
      editor.chain().focus().toggleBold().run();
    });
  }
  if (btnItalic) {
    btnItalic.addEventListener("click", function () {
      editor.chain().focus().toggleItalic().run();
    });
  }
  if (btnStrike) {
    btnStrike.addEventListener("click", function () {
      editor.chain().focus().toggleStrike().run();
    });
  }
  if (btnH1) {
    btnH1.addEventListener("click", function () {
      editor.chain().focus().toggleHeading({ level: 1 }).run();
    });
  }
  if (btnH2) {
    btnH2.addEventListener("click", function () {
      editor.chain().focus().toggleHeading({ level: 2 }).run();
    });
  }
  if (btnH3) {
    btnH3.addEventListener("click", function () {
      editor.chain().focus().toggleHeading({ level: 3 }).run();
    });
  }
  if (btnBullet) {
    btnBullet.addEventListener("click", function () {
      editor.chain().focus().toggleBulletList().run();
    });
  }
  if (btnOrdered) {
    btnOrdered.addEventListener("click", function () {
      editor.chain().focus().toggleOrderedList().run();
    });
  }
  if (btnQuote) {
    btnQuote.addEventListener("click", function () {
      editor.chain().focus().toggleBlockquote().run();
    });
  }

  // Reference insertion buttons
  document.querySelectorAll("[data-ref-type]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      openReferencePicker(btn.dataset.refType);
    });
  });
}

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      if (autosaveTimer) clearTimeout(autosaveTimer);
      performAutosave();
    }
  });
}

// Reference picker
function setupReferencePicker() {
  const overlay = document.getElementById("reference-picker-overlay");
  const closeBtn = document.getElementById("picker-close");
  const searchInput = document.getElementById("reference-search");
  const tabs = document.querySelectorAll(".picker-tab");

  if (closeBtn) {
    closeBtn.addEventListener("click", closeReferencePicker);
  }

  if (overlay) {
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeReferencePicker();
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      currentRefType = tab.dataset.type;
      tabs.forEach(function (t) {
        t.classList.remove("active");
      });
      tab.classList.add("active");
      if (searchInput.value) {
        searchReferences(searchInput.value);
      }
    });
  });

  if (searchInput) {
    let searchTimer;
    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () {
        searchReferences(searchInput.value);
      }, 300);
    });
  }

  // Handle result clicks
  document
    .getElementById("reference-results")
    .addEventListener("click", function (e) {
      const item = e.target.closest(".reference-item");
      if (item) {
        insertReference(item.dataset.type, item.dataset.id, item.dataset.label);
      }
    });
}

function openReferencePicker(refType) {
  currentRefType = refType || "document";
  const overlay = document.getElementById("reference-picker-overlay");
  const searchInput = document.getElementById("reference-search");
  const tabs = document.querySelectorAll(".picker-tab");
  const results = document.getElementById("reference-results");

  tabs.forEach(function (t) {
    t.classList.toggle("active", t.dataset.type === currentRefType);
  });

  results.innerHTML = '<div class="reference-empty">Type to search...</div>';
  overlay.classList.add("active");
  searchInput.value = "";
  searchInput.focus();
}

function closeReferencePicker() {
  const overlay = document.getElementById("reference-picker-overlay");
  overlay.classList.remove("active");
  editor.commands.focus();
}

function searchReferences(query) {
  if (!query.trim()) {
    document.getElementById("reference-results").innerHTML =
      '<div class="reference-empty">Type to search...</div>';
    return;
  }

  const url =
    window.NOTE_DATA.searchUrl +
    "?q=" +
    encodeURIComponent(query) +
    "&type=" +
    currentRefType;

  fetch(url, {
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  })
    .then(function (response) {
      return response.text();
    })
    .then(function (html) {
      document.getElementById("reference-results").innerHTML = html;
    });
}

function insertReference(type, id, label) {
  const refHtml =
    '<span class="note-ref" data-type="' +
    type +
    '" data-id="' +
    id +
    '">' +
    label +
    "</span> ";

  editor.chain().focus().insertContent(refHtml).run();

  closeReferencePicker();
}

// Initialize on load
document.addEventListener("DOMContentLoaded", initEditor);
