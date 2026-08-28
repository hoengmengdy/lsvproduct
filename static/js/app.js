document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!confirm(form.dataset.confirm)) event.preventDefault();
}));
document.querySelector('[data-admin-menu]')?.addEventListener('click', () => document.querySelector('.admin-side')?.classList.toggle('open'));
setTimeout(() => document.querySelectorAll('.alert').forEach(el => window.bootstrap?.Alert.getOrCreateInstance(el).close()), 5000);

// Reveal content as it enters the viewport without delaying page interaction.
const revealTargets = document.querySelectorAll('.product-card, .section-head, .brand-nav a, .panel, .stat-card');
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  revealTargets.forEach((element, index) => {
    element.classList.add('reveal-on-scroll');
    element.style.setProperty('--reveal-delay', `${(index % 4) * 70}ms`);
  });
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -35px' });
  revealTargets.forEach(element => revealObserver.observe(element));
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