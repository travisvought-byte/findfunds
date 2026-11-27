// Filters a page's event list by county, month, kind and text. Works from URL parameters too
// (county, month, kind, q), so the home page search can link straight to results.
(function () {
  var form = document.querySelector(".filterform");
  var box = document.querySelector("[data-filterable]");
  if (!form || !box) return;
  var status = document.querySelector(".finder .status");
  var empty = document.querySelector("[data-empty]");
  var items = Array.prototype.slice.call(box.querySelectorAll("li.item"));
  var groups = Array.prototype.slice.call(box.querySelectorAll("[data-month-group]"));
  var fields = ["county", "month", "kind", "q"];

  function val(name) {
    var el = form.elements[name];
    return el ? el.value.trim() : "";
  }

  function apply(announce) {
    var county = val("county"), month = val("month"), kind = val("kind"), q = val("q").toLowerCase();
    var shown = 0;
    items.forEach(function (li) {
      var ok = (!county || li.getAttribute("data-county") === county) &&
        (!month || li.getAttribute("data-month") === month) &&
        (!kind || li.getAttribute("data-kind") === kind) &&
        (!q || li.getAttribute("data-text").indexOf(q) !== -1);
      li.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector("li.item:not([hidden])");
    });
    if (empty) empty.hidden = shown !== 0;
    if (announce && status) {
      var filtered = county || month || kind || q;
      status.textContent = !filtered ? "Showing all events." : shown ? "Showing events that match your search." : "No events match your search.";
    }
  }

  var params = new URLSearchParams(window.location.search);
  var any = false;
  fields.forEach(function (name) {
    var el = form.elements[name];
    if (el && params.get(name)) { el.value = params.get(name); any = true; }
  });
  apply(any);

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var p = new URLSearchParams();
    fields.forEach(function (name) { if (val(name)) p.set(name, val(name)); });
    var qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : window.location.pathname);
    apply(true);
  });
  form.addEventListener("change", function () { apply(true); });
})();
