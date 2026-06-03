(function () {
  var STORAGE_KEY = 'nav-layout';

  function current() {
    return localStorage.getItem(STORAGE_KEY) || 'vertical';
  }

  function apply(setting) {
    if (setting === 'horizontal') {
      document.documentElement.setAttribute('data-nav', 'horizontal');
    } else {
      document.documentElement.removeAttribute('data-nav');
    }
  }

  window.setNavLayout = function (setting) {
    localStorage.setItem(STORAGE_KEY, setting);
    apply(setting);
  };

  window.getNavLayoutSetting = current;

  // Reflect the stored setting onto the settings-page radios. Runs on load and
  // after every htmx swap, since the settings content arrives via a boosted
  // swap where an inline script would not reliably re-run.
  function syncRadios() {
    var input = document.querySelector(
      '.nav-options input[value="' + current() + '"]'
    );
    if (input) input.checked = true;
  }

  syncRadios();
  document.body.addEventListener('htmx:afterSwap', syncRadios);
})();
