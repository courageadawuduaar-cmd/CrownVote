// Mobile nav toggle
function toggleNav() {
  const links = document.getElementById('navLinks');
  links.classList.toggle('open');
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
});

// ---- Hero Video Crossfade ----
document.addEventListener('DOMContentLoaded', function () {
  const videos = document.querySelectorAll('.hero-video');
  if (!videos.length) return;

  let current = 0;

  function crossfadeTo(next) {
    // Fade out current
    videos[current].style.opacity = '0';

    // Fade in next
    videos[next].style.opacity = '1';
    videos[next].currentTime   = 0;
    videos[next].play();

    current = next;
  }

  // When each video ends, crossfade to next
  videos.forEach((video, index) => {
    video.addEventListener('ended', function () {
      const next = (index + 1) % videos.length;
      crossfadeTo(next);
    });

    // Fallback — if video stalls for 8s, move to next
    video.addEventListener('stalled', function () {
      setTimeout(() => {
        if (video.paused || video.ended) return;
        const next = (index + 1) % videos.length;
        crossfadeTo(next);
      }, 8000);
    });
  });

  // Start playing first video
  if (videos[0]) {
    videos[0].play().catch(() => {
      // Autoplay blocked — show static fallback gracefully
      console.log('Autoplay blocked by browser.');
    });
  }
});