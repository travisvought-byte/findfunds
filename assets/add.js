// Turns the add-your-event form into an email draft. Nothing is sent until the person presses Send.
(function () {
  var form = document.querySelector('.addform');
  if (!form) return;
  var q = new URLSearchParams(location.search);
  if (q.get('event')) form.querySelector('#f-name').value = q.get('event').replace(/-/g, ' ');
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (!form.reportValidity()) return;
    var lines = [], service = [];
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name) return;
      if (el.type === 'checkbox') { if (el.checked) service.push(el.value); return; }
      lines.push(el.name + ': ' + (el.value.trim() || 'not given'));
    });
    lines.splice(8, 0, 'Service: ' + (service.join(', ') || 'not given'));
    var subject = 'New event for FindFundraisers.org: ' + form.querySelector('#f-name').value;
    location.href = 'mailto:' + form.dataset.mailto + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
  });
})();
