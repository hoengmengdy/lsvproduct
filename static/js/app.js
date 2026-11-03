document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!confirm(form.dataset.confirm)) event.preventDefault();
}));
document.querySelector('[data-admin-menu]')?.addEventListener('click', () => document.querySelector('.admin-side')?.classList.toggle('open'));
setTimeout(() => document.querySelectorAll('.alert').forEach(el => window.bootstrap?.Alert.getOrCreateInstance(el).close()), 5000);

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Reveal content as it enters the viewport, each group with its own entrance.
const revealGroups = [
  ['.product-card', index => (index % 2 ? 'flip' : 'up')],
  ['.section-head', () => 'left'],
  ['.brand-nav a', () => 'zoom'],
  ['.quality-recognition-item', () => 'zoom'],
  ['.panel, .stat-card', index => (index % 2 ? 'right' : 'up')],
];
if ('IntersectionObserver' in window && !reduceMotion) {
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const element = entry.target;
      element.classList.add('is-visible');
      revealObserver.unobserve(element);
      // Drop reveal styles once finished so hover/tilt transforms respond instantly.
      const cleanup = event => {
        if (event.target !== element || event.propertyName !== 'transform') return;
        element.removeEventListener('transitionend', cleanup);
        element.classList.remove('reveal-on-scroll', 'is-visible');
        element.removeAttribute('data-reveal');
        element.style.removeProperty('--reveal-delay');
      };
      element.addEventListener('transitionend', cleanup);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -35px' });
  revealGroups.forEach(([selector, pickVariant]) => {
    document.querySelectorAll(selector).forEach((element, index) => {
      element.classList.add('reveal-on-scroll');
      element.dataset.reveal = pickVariant(index);
      element.style.setProperty('--reveal-delay', `${(index % 4) * 110}ms`);
      revealObserver.observe(element);
    });
  });
}

// Scroll progress bar and compact navbar.
const progressBar = document.createElement('div');
progressBar.className = 'scroll-progress';
document.body.prepend(progressBar);
const navbar = document.querySelector('.navbar');
const onScroll = () => {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  progressBar.style.transform = `scaleX(${max > 0 ? window.scrollY / max : 0})`;
  navbar?.classList.toggle('is-scrolled', window.scrollY > 40);
};
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

if (!reduceMotion) {
  // 3D tilt on product cards for mouse users.
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.product-card').forEach(card => {
      card.addEventListener('pointermove', event => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        card.style.setProperty('--tilt-x', `${x * 14}deg`);
        card.style.setProperty('--tilt-y', `${y * -14}deg`);
        card.classList.add('is-tilting');
      });
      card.addEventListener('pointerleave', () => card.classList.remove('is-tilting'));
    });
  }

  // Ripple on button press.
  document.addEventListener('pointerdown', event => {
    const button = event.target.closest('.btn, .icon-btn');
    if (!button || button.disabled) return;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.cssText = `width:${size}px;height:${size}px;left:${event.clientX - rect.left - size / 2}px;top:${event.clientY - rect.top - size / 2}px`;
    button.append(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  });

  // Bounce the cart badge when it has items.
  const cartBadge = document.querySelector('.cart-badge');
  if (cartBadge && Number(cartBadge.textContent) > 0) setTimeout(() => cartBadge.classList.add('bump'), 600);
}
// Keep admin image uploads below Vercel's request limit.
const productForm = document.querySelector('[data-product-form]');
const imageInput = productForm?.querySelector('[data-image-upload]');
const imageStatus = productForm?.querySelector('[data-image-status]');

productForm?.addEventListener('submit', async event => {
  const file = imageInput?.files?.[0];
  if (!file || productForm.dataset.imagePrepared === 'true') return;
  if (file.size <= 1_800_000) return;

  event.preventDefault();
  const submitButton = event.submitter || productForm.querySelector('button[type="submit"], button:not([type])');
  if (file.type === 'image/gif') {
    imageStatus.textContent = 'GIF ធំពេក។ សូមប្រើរូបតូចជាង 1.8 MB។';
    imageStatus.classList.add('text-danger');
    return;
  }

  submitButton?.setAttribute('disabled', 'disabled');
  imageStatus.classList.remove('text-danger');
  imageStatus.textContent = 'កំពុងបង្រួមរូបភាព… / Compressing image…';

  try {
    const bitmap = await createImageBitmap(file);
    const maxSide = 1600;
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    canvas.getContext('2d', { alpha: true }).drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();

    const compressed = await new Promise(resolve => canvas.toBlob(resolve, 'image/webp', 0.82));
    if (!compressed || compressed.size > 2_500_000) throw new Error('compressed image is still too large');

    const transfer = new DataTransfer();
    const safeName = file.name.replace(/\.[^.]+$/, '') || 'product';
    transfer.items.add(new File([compressed], `${safeName}.webp`, { type: 'image/webp' }));
    imageInput.files = transfer.files;
    productForm.dataset.imagePrepared = 'true';
    imageStatus.textContent = `បានបង្រួមរួច: ${(file.size / 1048576).toFixed(1)} MB → ${(compressed.size / 1048576).toFixed(1)} MB`;
    productForm.requestSubmit(submitButton);
  } catch (error) {
    imageStatus.textContent = 'មិនអាចបង្រួមរូបនេះបានទេ។ សូមប្រើ JPG, PNG ឬ WEBP តូចជាង 2.5 MB។';
    imageStatus.classList.add('text-danger');
    submitButton?.removeAttribute('disabled');
  }
});