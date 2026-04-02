document.addEventListener("click", function (e) {
  var item = e.target.closest(".scheme-dropdown-item");

  if (!item) return;

  var trigger = item
    .closest(".scheme-dropdown")
    .querySelector(".scheme-dropdown-trigger");
  item
    .closest(".scheme-dropdown-menu")
    .querySelectorAll(".scheme-dropdown-item")
    .forEach(function (s) {
      s.classList.remove("active");
    });
  item.classList.add("active");

  if (item.dataset.scheme) {
    var scheme = item.dataset.scheme;
    document.getElementById("id_color_scheme").value = scheme;

    trigger.querySelector(".swatch-dot").className =
      "swatch-dot swatch-" + scheme;
    trigger.querySelector(".scheme-dropdown-label").textContent =
      item.textContent.trim();

    document.documentElement.setAttribute("data-theme", scheme);
  }

  // Dark mode
  if (item.dataset.appearance) {
    var mode = item.dataset.appearance;
    document.getElementById("id_dark_mode").value = mode;

    var icons = { system: "monitor", light: "sun", dark: "moon" };
    var triggerIcon = trigger.querySelector(".mode-icon");

    triggerIcon.className = "icon-" + icons[mode] + " mode-icon";
    trigger.querySelector(".mode-dropdown-label").textContent =
      item.textContent.trim();

    if (mode === "system") {
      var isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute(
        "data-mode",
        isDark ? "dark" : "light",
      );

      document.documentElement.setAttribute("data-mode-source", "system");
    } else {
      document.documentElement.setAttribute("data-mode", mode);
      document.documentElement.removeAttribute("data-mode-source");
    }
  }
});
