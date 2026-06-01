(function () {
  var STORAGE_KEY = 'theme';
  var media = window.matchMedia('(prefers-color-scheme: dark)');

  function resolve(setting) {
    if (setting === 'auto') {
      return media.matches ? 'dark' : 'light';
    }
    return setting;
  }

  function apply(setting) {
    document.documentElement.setAttribute('data-theme', resolve(setting));
  }

  function current() {
    return localStorage.getItem(STORAGE_KEY) || 'auto';
  }

  window.setTheme = function (setting) {
    localStorage.setItem(STORAGE_KEY, setting);
    apply(setting);
  };

  window.getThemeSetting = current;

  media.addEventListener('change', function () {
    if (current() === 'auto') {
      apply('auto');
    }
  });
})();
