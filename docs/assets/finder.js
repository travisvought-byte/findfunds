// ZIP-code search: sorts listings by straight-line distance from the ZIP's center.
(function () {
  var form = document.querySelector('.zipform');
  if (!form) return;
  var me = document.currentScript || document.querySelector('script[data-zips]');
  var zipsUrl = me.getAttribute('data-zips');
  var status = document.querySelector('.finder .status');
  var grouped = document.querySelector('[data-results]');
  var sorted = document.querySelector('[data-sorted]');
  var jump = document.querySelector('.jump');
  var zips = null;
  function miles(a, b) {
    var r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 3958.8 * 2 * Math.asin(Math.sqrt(h));
  }
  function show(zip, limit) {
    var here = zips[zip];
    if (!here) { status.textContent = 'We don’t have ZIP code ' + zip + ' on file. Try a nearby Ohio ZIP code.'; return; }
    var cards = Array.prototype.slice.call(grouped.querySelectorAll('.card[data-lat]'));
    var list = cards.map(function (c) { return { c: c, d: miles(here, [parseFloat(c.dataset.lat), parseFloat(c.dataset.lon)]) }; })
      .filter(function (x) { return !limit || x.d <= limit; })
      .sort(function (a, b) { return a.d - b.d; });
    sorted.innerHTML = '';
    list.forEach(function (x) {
      var copy = x.c.cloneNode(true);
      var d = copy.querySelector('.dist');
      d.textContent = 'About ' + Math.max(1, Math.round(x.d)) + ' miles away';
      d.hidden = false;
      sorted.appendChild(copy);
    });
    grouped.hidden = true; if (jump) jump.hidden = true; sorted.hidden = false;
    status.textContent = list.length ? 'Showing the closest first to ZIP code ' + zip + '.' : 'Nothing listed within ' + limit + ' miles of ' + zip + ' yet. Try a longer distance.';
    if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: 'search/zip', title: 'ZIP search', event: true });
  }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var zip = (form.zip.value || '').trim();
    var limit = parseInt(form.miles.value, 10) || 0;
    if (!/^\d{5}$/.test(zip)) { status.textContent = 'Please enter a five-digit ZIP code.'; form.zip.focus(); return; }
    var p = new URLSearchParams(location.search); p.set('zip', zip); p.set('miles', limit); history.replaceState(null, '', '?' + p.toString());
    if (zips) return show(zip, limit);
    status.textContent = 'Looking up your ZIP code…';
    fetch(zipsUrl).then(function (r) { return r.json(); }).then(function (z) { zips = z; show(zip, limit); })
      .catch(function () { status.textContent = 'Sorry, the ZIP search didn’t load. The full list is below by county.'; });
  });
  var q = new URLSearchParams(location.search);
  if (q.get('zip')) { form.zip.value = q.get('zip'); if (q.get('miles')) form.miles.value = q.get('miles'); form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit')); }
})();
