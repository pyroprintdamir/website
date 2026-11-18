(function () {
  var form = document.getElementById('raskid-form');
  if (!form) return;
  var k1 = document.getElementById('raskid-korak-1');
  var k2 = document.getElementById('raskid-korak-2');
  var pregled = document.getElementById('raskid-pregled');
  var status = document.getElementById('raskid-status');
  var gotovo = document.getElementById('raskid-gotovo');

  function val(n) { return (form.elements[n] && form.elements[n].value || '').trim(); }
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function say(msg, ok) { status.textContent = msg; status.className = 'form-status ' + (ok ? 'ok' : 'err'); }

  document.getElementById('raskid-dalje').addEventListener('click', function () {
    var kind = (form.querySelector('input[name="kind"]:checked') || {}).value;
    var emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(val('email'));
    if (!val('name') || !val('address') || !emailOk || !kind || !val('subject') || !val('ordered_on')) {
      form.reportValidity && form.reportValidity();
      var s1 = document.getElementById('raskid-status-1');
      s1.textContent = 'Ispunite sva obavezna polja i upišite ispravnu e-mail adresu.'; s1.className = 'form-status err';
      return;
    }
    pregled.innerHTML =
      '<p><strong>Ime i prezime:</strong> ' + esc(val('name')) + '<br>' +
      '<strong>Adresa:</strong> ' + esc(val('address')) + '<br>' +
      '<strong>E-mail:</strong> ' + esc(val('email')) + '<br>' +
      '<strong>Telefon:</strong> ' + esc(val('phone') || 'nije naveden') + '<br>' +
      '<strong>Raskidam:</strong> ' + (kind === 'roba' ? 'ugovor o prodaji robe' : 'ugovor o pružanju usluge') + '<br>' +
      '<strong>Roba/usluga:</strong> ' + esc(val('subject')) + '<br>' +
      '<strong>Naručeno/primljeno dana:</strong> ' + esc(val('ordered_on')) + '</p>';
    document.getElementById('raskid-status-1').textContent = '';
    k1.hidden = true; k2.hidden = false; say('', true);
    k2.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  document.getElementById('raskid-natrag').addEventListener('click', function () { k2.hidden = true; k1.hidden = false; });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var btn = document.getElementById('raskid-potvrdi');
    btn.disabled = true; say('Šaljem…', true);
    try {
      var res = await fetch(form.action, { method: 'POST', body: new FormData(form) });
      var data = {}; try { data = await res.json(); } catch (x) {}
      if (res.ok && data.ok) {
        form.hidden = true; gotovo.hidden = false;
        if (data.mailed === false) {
          gotovo.querySelector('p').innerHTML = 'Vaša izjava zaprimljena je <strong>' + esc(data.timestamp) + '</strong> (Europe/Zagreb). Potvrdu s njezinim sadržajem poslat ćemo vam e-poštom. Ako je ne dobijete u roku od jednog radnog dana, javite nam se na pyroprint.damir@gmail.com.</p><h4 class="text-dark">Sadržaj vaše izjave</h4><div class="text-dark">' + pregled.innerHTML + '</div><p class="text-gray">Sačuvajte ovu stranicu (npr. snimku zaslona) kao dokaz o podnošenju.';
        }
      } else if (data.error === 'captcha') {
        try { window.turnstile && window.turnstile.reset(); } catch (x) {}
        say('Provjera zaštite od spama nije uspjela. Pričekajte trenutak i pokušajte ponovno.', false);
      } else if (data.error === 'validation') {
        say('Provjerite podatke u izjavi pa pokušajte ponovno.', false);
      } else {
        say('Slanje nije uspjelo. Izjavu možete poslati e-poštom na pyroprint.damir@gmail.com ili poštom.', false);
      }
    } catch (err) {
      say('Slanje nije uspjelo. Izjavu možete poslati e-poštom na pyroprint.damir@gmail.com ili poštom.', false);
    }
    btn.disabled = false;
  });
})();
