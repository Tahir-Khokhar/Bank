// app.js - UI enhancements for the Bank Management System

(function () {
  'use strict';

  // Subtle animation when alerts appear.
  const alerts = document.querySelectorAll('.alert');
  for (let i = 0; i < alerts.length; i += 1) {
    alerts[i].style.animation = 'fadeInUp 260ms ease-out';
  }
  const style = document.createElement('style');
  style.innerHTML = '@keyframes fadeInUp { from { opacity: 0; transform: translateY(6px);} to {opacity: 1; transform: translateY(0);} }';
  document.head.appendChild(style);

  // Mobile sidebar toggle.
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('appSidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
  }
  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      if (backdrop) backdrop.classList.toggle('show');
    });
  }
  if (backdrop) backdrop.addEventListener('click', closeSidebar);

  // Auto-dismiss success alerts after a delay.
  window.setTimeout(function () {
    document.querySelectorAll('.alert-success').forEach(function (el) {
      el.classList.remove('show');
    });
  }, 5000);
})();
