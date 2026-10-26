// Scene two's lifecycle — the cinematic film, presented.
//
// The section plays a 20-second seamless continuous loop composited with
// Vrishin's authentic cybersecurity & AI tool stack. What this file adds is
// smooth presentation: the film arrives smoothly from black when the section
// is reached, and decodes only while actually visible on screen.

// Scene two — interactive cybersecurity tool universe (WebGL).
//
// Refactored 3D orbital tech cube / card system with dark high-tech glassmorphism,
// wide open horseshoe radius, zero character clipping, and pointer interactivity.

import { createGL } from '../gl/renderer.js';
import { Universe } from './universe.js';
import { T2 } from './timeline2.js';

export async function initUniverse() {
  const section = document.getElementById('universe');
  const canvas = document.getElementById('uniStage');
  const film = document.getElementById('uniFilm');
  const veil = document.getElementById('uniVeil');
  if (!section) return null;

  // Attempt live WebGL 3D glassmorphic orbital universe
  if (canvas) {
    const gl = createGL(canvas);
    if (gl) {
      try {
        const uni = new Universe(canvas, gl);
        await uni.load();

        const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
        const coarseMQ = matchMedia('(pointer: coarse)');

        const state = {
          started: 0,
          running: false,
          visible: false,
          raf: 0,
          last: 0,
          scroll: 0,
        };

        function place() {
          const dpr = Math.min(window.devicePixelRatio || 1, 2);
          uni.resize(window.innerWidth, window.innerHeight, dpr);
        }

        function frame(now) {
          if (!state.running) return;
          const t = reduced ? T2.alive + 0.5 : Math.max(0, (now - state.started) / 1000);
          const dt = Math.min(0.05, (now - state.last) / 1000 || 0.016);
          state.last = now;
          uni.render(t, dt, state.scroll);
          state.raf = requestAnimationFrame(frame);
        }

        function start() {
          if (state.running) return;
          state.running = true;
          if (!state.started) state.started = performance.now();
          else if (reduced) state.started = performance.now() - (T2.alive + 0.5) * 1000;
          state.last = performance.now();
          section.classList.add('is-on');
          if (veil) veil.style.opacity = '0';
          state.raf = requestAnimationFrame(frame);
        }

        function stop() {
          state.running = false;
          cancelAnimationFrame(state.raf);
        }

        section.addEventListener('pointermove', (e) => {
          if (coarseMQ.matches) return;
          const r = section.getBoundingClientRect();
          uni.pointer.tx = ((e.clientX - r.left) / r.width) * 2 - 1;
          uni.pointer.ty = ((e.clientY - r.top) / r.height) * 2 - 1;
          uni.pointer.inside = true;
          const hit = uni.pick(e.clientX - r.left, e.clientY - r.top);
          if (hit !== uni.hovered) {
            if (uni.hovered >= 0) uni.cards[uni.hovered].hover = 0;
            uni.hovered = hit;
          }
        }, { passive: true });

        section.addEventListener('pointerleave', () => {
          uni.pointer.inside = false;
          uni.pointer.tx = 0;
          uni.pointer.ty = 0;
          if (uni.hovered >= 0) uni.cards[uni.hovered].hover = 0;
          uni.hovered = -1;
        });

        window.addEventListener('scroll', () => {
          if (!state.visible) return;
          const r = section.getBoundingClientRect();
          const travel = Math.max(1, r.height - window.innerHeight);
          state.scroll = Math.max(0, Math.min(1, -r.top / travel));
        }, { passive: true });

        new IntersectionObserver((entries) => {
          for (const e of entries) {
            state.visible = e.isIntersecting;
            if (e.isIntersecting) start();
            else stop();
          }
        }, { threshold: 0.22 }).observe(section);

        window.addEventListener('resize', place);
        place();

        // If film element exists in background, pause it to save GPU resources
        if (film) film.pause();

        return { uni, section };
      } catch (err) {
        console.warn('WebGL Universe fallback to video film:', err);
      }
    }
  }

  // Fallback: seamless video loop presentation
  if (!film || !veil) return null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = { visible: false, entered: false };

  const play = () => {
    film.play().catch(() => {
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

  return { film, section };
}
