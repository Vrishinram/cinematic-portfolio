// Scene two's lifecycle — the cinematic film, presented.
//
// The section plays a 20-second seamless continuous loop composited with
// Vrishin's authentic cybersecurity & AI tool stack. What this file adds is
// smooth presentation: the film arrives smoothly from black when the section
// is reached, and decodes only while actually visible on screen.

export async function initUniverse() {
  const section = document.getElementById('universe');
  const film = document.getElementById('uniFilm');
  const veil = document.getElementById('uniVeil');
  if (!section || !film || !veil) return null;

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = { visible: false, entered: false };

  const play = () => {
    film.play().catch(() => {
      // autoplay refused: arm a one-shot retry on the first real interaction
      const retry = () => { film.play().catch(() => {}); };
      window.addEventListener('pointerdown', retry, { once: true });
      window.addEventListener('scroll', retry, { once: true });
    });
  };

  new IntersectionObserver((entries) => {
    for (const e of entries) {
      state.visible = e.isIntersecting;
      if (e.isIntersecting) {
        if (!state.entered) {
          state.entered = true;
          section.classList.add('is-on');
          veil.style.opacity = '0';
        }
        if (reduced) {
          film.currentTime = 5.0;
          film.pause();
          veil.style.opacity = '0';
        } else {
          play();
        }
      } else {
        film.pause();
      }
    }
  }, { threshold: 0.30 }).observe(section);

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') film.pause();
    else if (state.visible && !reduced) play();
  });

  film.addEventListener('error', () => section.classList.add('is-fallback'),
    { once: true });

  // warm the film once the page is otherwise idle, so scrolling into the
  // section never waits on a network fetch
  window.addEventListener('load', () => {
    if (!state.entered && film.preload !== 'auto') {
      film.preload = 'auto';
      film.load();
    }
  }, { once: true });

  return { film, section };
}
