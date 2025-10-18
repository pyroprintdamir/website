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
  const lightbox = document.createElement("div");
  lightbox.classList.add("lightbox");
  document.body.appendChild(lightbox);

  const lbImage = document.createElement("img");
  lbImage.classList.add("lb-image");
  lightbox.appendChild(lbImage);

  const lbCaption = document.createElement("div");
  lbCaption.classList.add("lb-caption");
  lightbox.appendChild(lbCaption);

  const lbClose = document.createElement("button");
  lbClose.classList.add("lb-close");
  lbClose.innerHTML = "&times;";
  lightbox.appendChild(lbClose);

  const lbPrev = document.createElement("button");
  lbPrev.classList.add("lb-prev");
  lbPrev.innerHTML = "&#10094;";
  lightbox.appendChild(lbPrev);

  const lbNext = document.createElement("button");
  lbNext.classList.add("lb-next");
  lbNext.innerHTML = "&#10095;";
  lightbox.appendChild(lbNext);

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

  galleryItems.forEach((item, index) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      openLightbox(index);
    });
  });

  lbClose.addEventListener("click", closeLightbox);
  lbNext.addEventListener("click", showNext);
  lbPrev.addEventListener("click", showPrev);

  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });

  /* ---------- ESC KEY ZA ZATVARANJE ---------- */
  document.addEventListener("keydown", (e) => {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowRight") showNext();
    if (e.key === "ArrowLeft") showPrev();
  });
});
