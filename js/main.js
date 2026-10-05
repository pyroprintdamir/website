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

// ---------- GDPR / obavijest o kolačićima (Google Analytics consent) ----------
(function(){
  var CONSENT_KEY = 'pd_cookie_consent';

  function setAnalyticsConsent(granted){
    if (typeof gtag === 'function') {
      gtag('consent', 'update', {
        'analytics_storage': granted ? 'granted' : 'denied'
      });
    }
  }

  function showBanner(){
    var old = document.querySelector('.cookie-consent-banner');
    if (old) old.remove();

    var banner = document.createElement('div');
    banner.className = 'cookie-consent-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Obavijest o kolačićima');
    banner.innerHTML =
      '<p>Uz vaš pristanak koristimo Google Analytics kolačiće za anonimnu statistiku posjeta, kako bismo poboljšali sadržaj. Podaci se ne koriste za oglašavanje. <a href="/politika-privatnosti">Politika privatnosti</a></p>' +
      '<div class="cookie-consent-actions">' +
        '<button type="button" class="cookie-consent-decline">Odbijam</button>' +
        '<button type="button" class="cookie-consent-accept">Prihvaćam</button>' +
      '</div>';
    document.body.appendChild(banner);

    banner.querySelector('.cookie-consent-accept').addEventListener('click', function(){
      try { localStorage.setItem(CONSENT_KEY, 'granted'); } catch(e) {}
      setAnalyticsConsent(true);
      banner.remove();
    });
    banner.querySelector('.cookie-consent-decline').addEventListener('click', function(){
      try { localStorage.setItem(CONSENT_KEY, 'denied'); } catch(e) {}
      setAnalyticsConsent(false);
      banner.remove();
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    var stored = null;
    try { stored = localStorage.getItem(CONSENT_KEY); } catch(e) {}

    if (stored === 'granted') { setAnalyticsConsent(true); }
    else if (stored !== 'denied') { showBanner(); }
  });

  // Poveznica "Postavke kolačića" u podnožju: omogućuje promjenu ili povlačenje pristanka
  document.addEventListener('click', function(e){
    var link = e.target.closest ? e.target.closest('.cookie-settings-link') : null;
    if (link) {
      e.preventDefault();
      showBanner();
    }
  });
})();

// ---------- Google karta: učitava se tek nakon klika (bez automatskog slanja podataka Googleu) ----------
document.addEventListener('click', function(e){
  var btn = e.target.closest ? e.target.closest('.map-consent-load') : null;
  if (!btn) return;
  var box = btn.closest('.map-consent');
  if (!box) return;
  var iframe = document.createElement('iframe');
  iframe.src = box.getAttribute('data-map-src');
  iframe.title = box.getAttribute('data-map-title') || 'Google karta';
  iframe.width = '100%';
  iframe.height = '300';
  iframe.style.cssText = 'border:0;display:block;';
  iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
  box.innerHTML = '';
  box.classList.add('map-loaded');
  box.appendChild(iframe);
});

// ---------- Kontakt forma: slanje preko vlastitog Cloudflare Workera (bez trećeg obrađivača) ----------
document.addEventListener('submit', async function(e){
  var form = e.target;
  if (!form.classList || !form.classList.contains('contact-form')) return;
  e.preventDefault();

  var status = form.querySelector('.form-status');
  var btn = form.querySelector('button[type="submit"]');
  function say(msg, ok){
    if (!status) return;
    status.textContent = msg;
    status.className = 'form-status ' + (ok ? 'ok' : 'err');
  }
  function resetCaptcha(){ try { if (window.turnstile) window.turnstile.reset(); } catch(err) {} }

  btn.disabled = true;
  say('Šaljem…', true);
  try {
    var res = await fetch(form.action, { method: 'POST', body: new FormData(form) });
    var data = {};
    try { data = await res.json(); } catch(err) {}
    if (res.ok && data.ok) {
      form.reset();
      resetCaptcha();
      say('Hvala! Upit je poslan, javit ćemo vam se uskoro.', true);
    } else if (data.error === 'captcha') {
      resetCaptcha();
      say('Provjera zaštite od spama nije uspjela. Pričekajte trenutak i pokušajte ponovno.', false);
    } else if (data.error === 'validation') {
      say('Provjerite jesu li ime, e-mail i poruka ispravno upisani.', false);
    } else {
      say('Slanje nije uspjelo. Pokušajte ponovno ili nam pišite na pyroprint.damir@gmail.com.', false);
    }
  } catch(err) {
    say('Slanje nije uspjelo. Pokušajte ponovno ili nam pišite na pyroprint.damir@gmail.com.', false);
  }
  btn.disabled = false;
});
