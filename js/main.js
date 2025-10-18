// main.js — scroll to top + mobilni meni
document.addEventListener('DOMContentLoaded', () => {
  const scrollBtn = document.getElementById('scrollTop');
  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');

  if (scrollBtn) {
    window.addEventListener('scroll', () => {
      scrollBtn.classList.toggle('show', window.scrollY > 300);
    });
    scrollBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  if (navToggle && nav) {
    navToggle.addEventListener('click', () => {
      nav.classList.toggle('open');
    });
  }
});