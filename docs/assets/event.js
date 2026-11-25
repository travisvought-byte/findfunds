// Print-a-flyer and share buttons on event pages.
(function () {
  var p = document.querySelector('[data-print]');
  if (p) p.addEventListener('click', function () { window.print(); });
  var s = document.querySelector('[data-share]');
  if (s) s.addEventListener('click', function () {
    var data = { title: s.dataset.title, url: location.href };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(function () {
      s.querySelector('span').textContent = 'Link copied';
    });
  });
})();
