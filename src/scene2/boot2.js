// Scene two — interactive cybersecurity tool universe (WebGL).
//
// Replaces the pre-rendered reference video with a live 3D amphitheater:
// live room choreography, authentic cybersecurity & AI defense stack,
// interactive pointer parallax, card hover, and sharp DOM typography.

import { createGL } from '../gl/renderer.js';
import { Universe } from './universe.js';
import { T2 } from './timeline2.js';

export async function initUniverse() {
  const section = document.getElementById('universe');
  const canvas = document.getElementById('uniStage');
  if (!section || !canvas) return null;

  const gl = createGL(canvas);
  if (!gl) {
    section.classList.add('is-fallback');
    return null;
  }

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarseMQ = matchMedia('(pointer: coarse)');
  const uni = new Universe(canvas, gl);
  await uni.load();

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
    const t = reduced
      ? T2.alive + 0.5
      : Math.max(0, (now - state.started) / 1000);
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
    state.raf = requestAnimationFrame(frame);
  }

  function stop() {
    state.running = false;
    cancelAnimationFrame(state.raf);
  }

  // pointer parallax + hover
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

  // light scroll dolly while the section is pinned in view
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

  window.addEventListener('resize', () => {
    place();
  });
  place();

  // damp hover toward the picked card each frame via render's existing card.hover
  const _render = uni.render.bind(uni);
  uni.render = (t, dt, scroll) => {
    for (const c of uni.cards) {
      const want = c.i === uni.hovered ? 1 : 0;
      c.hover += (want - c.hover) * Math.min(1, dt * 10);
    }
    _render(t, dt, scroll);
  };

  return { uni, section };
}
