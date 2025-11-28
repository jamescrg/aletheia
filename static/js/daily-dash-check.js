// Daily dash check - ensures users view the agenda dash at least once per day
// Handles browser tabs left open overnight by checking on visibility change
(function() {
  const DASH_URL = '/dash/';
  const STORAGE_KEY = 'dailyDashCheckDate';

  function getTodayString() {
    return new Date().toISOString().split('T')[0];
  }

  function checkDailyDash() {
    const lastCheckDate = localStorage.getItem(STORAGE_KEY);
    const today = getTodayString();

    // If we're already on the dash page, update the check date
    if (window.location.pathname === DASH_URL) {
      localStorage.setItem(STORAGE_KEY, today);
      return;
    }

    // If we haven't checked in today, redirect to dash
    if (lastCheckDate !== today) {
      window.location.href = DASH_URL;
    }
  }

  // Check when the page becomes visible (handles tab switching and waking from sleep)
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
      checkDailyDash();
    }
  });

  // Also check on initial page load
  document.addEventListener('DOMContentLoaded', function() {
    // Small delay to let the page settle and avoid race with server redirect
    setTimeout(checkDailyDash, 100);
  });
})();
