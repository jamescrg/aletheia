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
})();
