function initCountdowns() {
  const els = document.querySelectorAll('.event-countdown');
  if (!els.length) return;

  function pad(n) {
    return n.toString().padStart(2, '0');
  }

  function update() {
    const now = new Date().getTime();

    els.forEach(function (el) {
      const start = new Date(el.dataset.start).getTime();
      const end   = new Date(el.dataset.end).getTime();
      let target, label;

      if (now < start) {
        target = start;
        label = 'Starts in';
      } else if (now <= end) {
        target = end;
        label = 'Ends in';
      } else {
        el.textContent = 'Voting has ended';
        return;
      }

      const diff    = target - now;
      const days    = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours   = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      el.textContent = label + ' ' + days + 'd ' + pad(hours) + 'h ' + pad(minutes) + 'm ' + pad(seconds) + 's';
    });
  }

  update();
  setInterval(update, 1000);
}

document.addEventListener('DOMContentLoaded', initCountdowns);