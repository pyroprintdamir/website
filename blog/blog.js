// Puna funkcija za inicijalizaciju bloga
function initBlog(blogs) {
    // Sortiraj po datumu (najnoviji prvi)
    blogs.sort((a, b) => new Date(b.date) - new Date(a.date));

    const main = document.getElementById('blog-main');
    const menu = document.getElementById('blog-menu');

    // ----------------------------------------------------
    // FUNKCIJE
    // ----------------------------------------------------

    function setBlogSEO(blog) {
        document.title = `${blog.title} | Pyroprint Damir Blog`;

        let metaDescription = document.querySelector('meta[name="description"]');
        if (!metaDescription) {
            metaDescription = document.createElement('meta');
            metaDescription.setAttribute('name', 'description');
            document.head.appendChild(metaDescription);
        }
        metaDescription.setAttribute('content', blog.description || 'Sve o laserskom graviranju, pirografiji i personaliziranim poklonima.');

        let metaKeywords = document.querySelector('meta[name="keywords"]');
        if (!metaKeywords) {
            metaKeywords = document.createElement('meta');
            metaKeywords.setAttribute('name', 'keywords');
            document.head.appendChild(metaKeywords);
        }
        metaKeywords.setAttribute('content', blog.keywords || 'graviranje, pokloni, pirografija, blog');
    }

    async function displayBlog(blog, updateUrl = true) {
        try {
            const res = await fetch(blog.file);
            if (!res.ok) {
                 throw new Error(`Greška: ${res.status} ${res.statusText} pri učitavanju ${blog.file}`);
            }
            const html = await res.text();
            
            setBlogSEO(blog);
            main.innerHTML = `<h1>${blog.title}${blogs[0].title === blog.title ? ' 🆕' : ''}</h1>${html}`;

            window.scrollTo(0, 0); 

            // Ažuriranje URL-a pomoću SLUG-a
            if (updateUrl) {
                history.pushState({ slug: blog.slug }, '', `?post=${blog.slug}`);
            }

            // Aktivna klasa u meniju
            document.querySelectorAll('.menu-item').forEach(item => {
                item.classList.toggle('active', item.dataset.slug === blog.slug);
            });
            
            // Re-bindiranje internih linkova
            main.querySelectorAll('a[href^="index.html?post="]').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetSlug = link.href.split('?post=')[1];
                    const targetBlog = blogs.find(b => b.slug === targetSlug);
                    if (targetBlog) {
                        displayBlog(targetBlog, true);
                    }
                });
            });

        } catch (err) {
            console.error('Greška pri učitavanju blog sadržaja:', err);
            main.innerHTML = `<p style="color:red;padding: 20px;">**GREŠKA PRI UČITAVANJU BLOGA:** ${err.message || err}. Provjerite da li blog file (${blog.file}) postoji na serveru (404 Greška).</p>`;
        }
    }

    // ----------------------------------------------------
    // INICIJALIZACIJA
    // ----------------------------------------------------

    // 1. Logika za učitavanje na osnovu URL parametra (koristi SLUG)
    const urlParams = new URLSearchParams(window.location.search);
    const postSlug = urlParams.get('post');
    let initialBlog = blogs[0];

    if (postSlug) {
        const foundBlog = blogs.find(b => b.slug === postSlug);
        if (foundBlog) {
            initialBlog = foundBlog;
        }
    }

    // 2. Kreiraj MENU PRVO
    menu.innerHTML = blogs
        .map(blog => `<div class="menu-item" data-slug="${blog.slug}">${blog.title}${blogs[0].title === blog.title ? ' 🆕' : ''}</div>`)
        .join('');

    // 3. Prikaži početni ili traženi blog
    displayBlog(initialBlog, false);


    // 4. Klik event za sve stavke menija
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            const slug = item.dataset.slug;
            const blogToDisplay = blogs.find(b => b.slug === slug);
            if (blogToDisplay) {
                displayBlog(blogToDisplay, true);
            }
        });
    });

    // 5. Podrška za back/forward dugmad preglednika
    window.addEventListener('popstate', (e) => {
        const urlParams = new URLSearchParams(window.location.search);
        const popSlug = urlParams.get('post');
        const blogToDisplay = blogs.find(b => b.slug === popSlug);
        if (blogToDisplay) {
             displayBlog(blogToDisplay, false);
        } else {
             displayBlog(blogs[0], false);
        }
    });
}

// Učitavanje blog.json datoteke (dodatni catch za greške pri učitavanju JSON-a)
fetch('blogs.json')
  .then(response => {
      if (!response.ok) {
          throw new Error('Ne mogu učitati blogs.json! Provjerite putanju i integritet datoteke.');
      }
      return response.json();
  })
  .then(initBlog)
  .catch(err => {
      console.error('Kritična greška pri inicijalizaciji bloga:', err);
      // Prikaz greške na stranici ako JSON ne radi
      document.getElementById('blog-main').innerHTML = `<p style="color:red;padding: 20px;">KRITIČNA GREŠKA: Nije moguće učitati blogove. (${err.message}). Provjerite da li je datoteka **blogs.json** na ispravnoj putanji i da je format ispravan.</p>`;
  });
