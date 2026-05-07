let currentQty = 1;
const PRICE_PER_VOTE = 1;

function updateDisplay() {
  document.getElementById('qtyDisplay').textContent = currentQty;
  document.getElementById('quantityInput').value = currentQty;
  const total = (currentQty * PRICE_PER_VOTE).toFixed(2);
  document.getElementById('priceDisplay').textContent = '₵' + total;
}

function changeQty(delta) {
  currentQty = Math.max(1, currentQty + delta);
  updateDisplay();
}

function setQty(qty) {
  currentQty = qty;
  updateDisplay();
}

function selectNetwork(network, el) {
  document.querySelectorAll('.network-option').forEach(opt => opt.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('networkSelected').value = network;
  const radio = el.querySelector('input[type=radio]');
  if (radio) radio.checked = true;

  // Update phone placeholder by network
  const placeholders = {
    mtn:     '024 / 025 / 053 / 054 / 055 / 059',
    telecel: '020 / 050',
    airtel:  '027 / 057 / 026 / 056'
  };
  const phoneInput = document.getElementById('phoneInput');
  if (phoneInput && placeholders[network]) {
    phoneInput.placeholder = 'e.g. ' + placeholders[network].split('/')[0].trim() + '1234567';
  }
}

// Prevent double submission
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('voteForm');
  const btn  = document.getElementById('submitBtn');
  if (form && btn) {
    form.addEventListener('submit', function () {
      btn.disabled = true;
      btn.textContent = '⏳ Processing...';
      btn.style.opacity = '0.75';
    });
  }
});