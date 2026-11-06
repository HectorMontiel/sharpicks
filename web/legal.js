// v584 — términos y privacidad en el idioma elegido en la app. Sin JavaScript se ve el español.
(function () {
  let lang = 'es';
  try { if (localStorage.getItem('sp_idioma') === 'en') lang = 'en'; } catch (e) { /* sin almacenamiento */ }
  function poner(l) {
    document.documentElement.lang = l;
    document.querySelectorAll('[data-lang]').forEach((x) => { x.hidden = x.dataset.lang !== l; });
  }
  poner(lang);
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-legal-idioma]');
    if (!b) return;
    e.preventDefault();
    try { localStorage.setItem('sp_idioma', b.dataset.legalIdioma); } catch (e2) { /* sin almacenamiento */ }
    poner(b.dataset.legalIdioma);
  });
}());
