/* ======================================================
   Pyroprint Damir - main.js (2025)
   Funkcionalnosti: Hamburger meni, Scroll to Top, Lightbox
====================================================== */

document.addEventListener("DOMContentLoaded", () => {

  /* ---------- HAMBURGER MENI ---------- */
  const navToggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".nav");

  navToggle.addEventListener("click", () => {
    nav.classList.toggle("open");
  });

  /* ---------- SCROLL TO TOP ---------- */
  const scrollBtn = document.getElementById("scrollTop");

  window.addEventListener("scroll", () => {
    if (window.scrollY > 200) {
      scrollBtn.classList.add("show");
    } else {
      scrollBtn.classList.remove("show");
    }
  });

  scrollBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ---------- LIGHTBOX ---------- */
  const lightbox = document.getElementById("lightbox");
  const lbImage = document.getElementById("lbImage");
  const lbCaption = document.getElementById("lbCaption");
  const lbClose = document.getElementById("lbClose");
  const lbPrev = document.getElementById("lbPrev");
  const lbNext = document.getElementById("lbNext");

  const galleryItems = document.querySelectorAll(".gallery-item");
  let currentIndex = 0;

  function openLightbox(index) {
    const item = galleryItems[index];
    lbImage.src = item.href;
    lbCaption.textContent = item.querySelector("img").alt || "";
    lightbox.classList.add("open");
    currentIndex = index;
  }

  function closeLightbox() {
    lightbox.classList.remove("open");
  }

  function showNext() {
    currentIndex = (currentIndex + 1) % galleryItems.length;
    openLightbox(currentIndex);
  }

  function showPrev() {
    currentIndex = (currentIndex - 1 + galleryItems.length) % galleryItems.length;
    openLightbox(currentIndex);
  }

  // Klik na slike galerije
  galleryItems.forEach((item, index) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      openLightbox(index);
    });
  });

  // Gumbi Lightbox
  lbClose.addEventListener("click", closeLightbox);
  lbNext.addEventListener("click", showNext);
  lbPrev.addEventListener("click", showPrev);

  // Klik izvan slike zatvara Lightbox
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });

  // Tipke tipkovnice
  document.addEventListener("keydown", (e) => {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowRight") showNext();
    if (e.key === "ArrowLeft") showPrev();
  });

});
