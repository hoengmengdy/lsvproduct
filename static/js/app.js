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
