/* ======================================================
   Pyroprint Damir - main.js (Optimizirano + Dark Mode)
   Funkcionalnosti: Hamburger meni (ARIA), Scroll to Top, Lightbox (Preload), Theme Switch (Dark Mode)
====================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;

    /* ---------- DARK MODE LOGIC ---------- */
    const themeToggle = document.getElementById("theme-toggle");

    // Funkcija za primjenu teme
    function applyTheme(isDark) {
        if (isDark) {
            body.classList.add("dark-mode");
            if (themeToggle) themeToggle.textContent = '☀️';
        } else {
            body.classList.remove("dark-mode");
            if (themeToggle) themeToggle.textContent = '🌓';
        }
    }

    // Učitavanje teme (prvo iz localStorage, zatim iz postavki sustava)
    function loadTheme() {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark') {
            applyTheme(true);
        } else if (storedTheme === 'light') {
            applyTheme(false);
        } else {
            // Ako nema u storage-u, koristi postavku sustava
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark);
        }
    }

    // Toggle funkcija
    function toggleTheme() {
        const isDark = body.classList.toggle("dark-mode");
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        applyTheme(isDark); // Ažurira ikonu
    }

    // Inicijalno učitaj temu
    loadTheme();

    // Event listener za gumb
    if (themeToggle) {
        themeToggle.addEventListener("click", toggleTheme);
    }

    /* ---------- HAMBURGER MENI (sa ARIA podrškom) ---------- */
    const navToggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".nav");
    
    if (navToggle) navToggle.setAttribute("aria-expanded", "false"); 

    if (navToggle) {
        navToggle.addEventListener("click", () => {
            if (nav) nav.classList.toggle("open");
            const isExpanded = nav.classList.contains("open");
            navToggle.setAttribute("aria-expanded", isExpanded);
        });
    }

    /* ---------- SCROLL TO TOP (Optimizirano) ---------- */
    const scrollBtn = document.getElementById("scrollTop");

    window.addEventListener("scroll", () => {
      if (scrollBtn) {
          scrollBtn.classList.toggle("show", window.scrollY > 200);
      }
    });

    if (scrollBtn) {
      scrollBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    /* ---------- LIGHTBOX (sa Preloadom i ARIA podrškom) ---------- */
    const lightbox = document.getElementById("lightbox");
    const lbImage = document.getElementById("lbImage");
    const lbCaption = document.getElementById("lbCaption");
    const lbClose = document.getElementById("lbClose");
    const lbPrev = document.getElementById("lbPrev");
    const lbNext = document.getElementById("lbNext");

    if (lbPrev) lbPrev.setAttribute("aria-label", "Prethodna slika");
    if (lbNext) lbNext.setAttribute("aria-label", "Sljedeća slika");

    const galleryItems = document.querySelectorAll(".gallery-item");
    let currentIndex = 0;

    function openLightbox(index) {
        const item = galleryItems[index];
        const itemImg = item.querySelector("img");
        
        // Pre-fetch/Preload slike
        const imageUrl = item.href;
        const altText = itemImg ? itemImg.alt : "";

        const imgElement = new Image();
        imgElement.onload = () => {
            lbImage.src = imageUrl;
            lbCaption.textContent = altText;
            if(lightbox) lightbox.classList.add("open");
            currentIndex = index;
            if (lbClose) lbClose.focus();
        };
        imgElement.src = imageUrl; 
    }

    function closeLightbox() {
        if(lightbox) lightbox.classList.remove("open");
        if (galleryItems[currentIndex]) galleryItems[currentIndex].focus();
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
        item.setAttribute('tabindex', '0');
    });

    // Gumbi Lightbox
    if (lbClose) lbClose.addEventListener("click", closeLightbox);
    if (lbNext) lbNext.addEventListener("click", showNext);
    if (lbPrev) lbPrev.addEventListener("click", showPrev);

    // Klik izvan slike zatvara Lightbox
    if (lightbox) {
        lightbox.addEventListener("click", (e) => {
            if (e.target === lightbox) closeLightbox();
        });

        // Zatvaranje na tipku ESC
        document.addEventListener('keydown', (e) => {
            if (lightbox.classList.contains('open') && e.key === 'Escape') closeLightbox();
            if (lightbox.classList.contains('open') && e.key === 'ArrowRight') showNext();
            if (lightbox.classList.contains('open') && e.key === 'ArrowLeft') showPrev();
        });
    }
});

/* ======================================================
   Blog hero galerija - auto-rotacija + swipe (blog/{slug}.html)
====================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const tracks = document.querySelectorAll('.blog-hero-gallery-track');
    if (!tracks.length) return;

    tracks.forEach((track) => {
        let paused = false;
        let resumeTimer = null;

        function pauseAwhile() {
            paused = true;
            clearTimeout(resumeTimer);
            resumeTimer = setTimeout(() => { paused = false; }, 4500);
        }

        track.addEventListener('mouseenter', () => { paused = true; });
        track.addEventListener('mouseleave', () => { paused = false; });
        track.addEventListener('touchstart', () => { paused = true; }, { passive: true });
        track.addEventListener('touchend', pauseAwhile, { passive: true });
        track.addEventListener('wheel', pauseAwhile, { passive: true });

        setInterval(() => {
            if (paused) return;
            const maxScroll = track.scrollWidth - track.clientWidth;
            if (maxScroll <= 4) return;
            const step = track.clientWidth * 0.55 || 260;
            const next = track.scrollLeft + step;
            if (next >= maxScroll - 5) {
                track.scrollTo({ left: 0, behavior: 'smooth' });
            } else {
                track.scrollTo({ left: next, behavior: 'smooth' });
            }
        }, 3200);
    });
});
