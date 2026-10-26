// The twelve tool cards.
//
// Nothing here is invented: each card's centre, apparent width and aspect were
// measured off the supplied reference artwork. Depth is then INFERRED from
// apparent size — a card drawn large in the poster is a card near the camera —
// and the world position is solved so that the perspective projection puts it
// back exactly where the poster had it.
//
// Solving it rather than eyeballing world coordinates matters for two reasons:
// the reconstruction is faithful at ANY viewport aspect (the composition
// re-fits instead of cropping), and the depths are physically consistent, so
// pointer parallax and the camera dolly come out right for free.

// name, centre x/y (fraction of the reference frame), apparent width, aspect
// name, centre x/y (fraction of the reference frame), apparent width, aspect
// Open horseshoe distribution: pushed outwards by 25-35%, central corridor completely cleared
const REF = [
  // Left horseshoe wing:
  ['wireshark',  0.220, 0.110, 0.170, 1.35],
  ['splunk',     0.130, 0.360, 0.155, 0.89],
  ['nmap',       0.260, 0.330, 0.088, 1.14],
  ['metasploit', 0.230, 0.490, 0.078, 0.99],
  ['burpsuite',  0.170, 0.650, 0.095, 0.98],
  ['docker',     0.285, 0.730, 0.082, 1.02],

  // Right horseshoe wing (Single Claude, Single ChatGPT):
  ['claude',     0.780, 0.140, 0.155, 0.82],
  ['langchain',  0.870, 0.350, 0.105, 1.04],
  ['chatgpt',    0.770, 0.450, 0.105, 1.25],
  ['snort',      0.840, 0.580, 0.110, 1.75],
  ['python',     0.710, 0.700, 0.088, 1.02], // Repositioned away from torso/legs
  ['linux',      0.820, 0.770, 0.092, 1.05],
];

// the largest card in the poster is taken as the near plane
const NEAREST = 0.185;

// Central character silhouette exclusion buffer:
// (x: [-1.2, 1.2], y: [-2, 2.5], z: [-0.5, 0.5])
const EXCLUSION_X = 1.2;
const EXCLUSION_Y_MIN = -2.0;
const EXCLUSION_Y_MAX = 2.5;
const EXCLUSION_Z = 0.5;

let seedState = 1;
function rnd() {
  seedState = (seedState * 1664525 + 1013904223) % 4294967296;
  return seedState / 4294967296;
}

export function buildCards() {
  seedState = 7;
  return REF.map(([name, rx, ry, rw, aspect], i) => ({
    name,
    i,
    ref: { rx, ry, rw, aspect },
    home: [0, 0, 0],
    size: [1, 1],
    rest: [
      (0.5 - ry) * 0.34 + (rnd() - 0.5) * 0.07,
      (0.5 - rx) * 0.58 + (rnd() - 0.5) * 0.07,
      (rnd() - 0.5) * 0.10,
    ],
    phase: rnd() * Math.PI * 2,
    speed: 0.55 + rnd() * 0.45,
    bobY: 0.05 + rnd() * 0.05,
    bobX: 0.018 + rnd() * 0.026,
    swing: 0.026 + rnd() * 0.028,
    launch: 0.85 + rnd() * 0.5,
    spin: (rnd() - 0.5) * 0.5,
    hover: 0,
    screen: null,
  }));
}

/**
 * Solve world position and size with expanded orbital radius (horseshoe layout)
 * and central character exclusion buffer.
 */
export function layoutCards(cards, aspect, fovY, camZ, opts = {}) {
  const tanH = Math.tan(fovY / 2);
  // Expand orbital ellipse radius by ~30%
  const spread = (opts.spread ?? 1) * 1.30;
  const lift = opts.lift ?? 1;
  const sizeMul = opts.sizeMul ?? 1;

  for (const c of cards) {
    const { rx, ry, rw } = c.ref;
    const f = rw / NEAREST;
    // Push Z-distance further out by ~25%
    let dist = (camZ / f) * 1.25;
    let z = camZ - dist;

    const ndcX = (rx - 0.5) * 2 * spread;
    const ndcY = -(ry - 0.5) * 2 * lift;

    let x = ndcX * tanH * aspect * dist;
    let y = ndcY * tanH * dist;

    // Apply exclusion buffer around central character mesh:
    if (Math.abs(x) < EXCLUSION_X && y > EXCLUSION_Y_MIN && y < EXCLUSION_Y_MAX && Math.abs(z) < EXCLUSION_Z) {
      const signX = x >= 0 ? 1 : -1;
      x = signX * (EXCLUSION_X + 0.35);
      z = z - 0.45;
      dist = camZ - z;
    }

    c.home = [x, y, z];
    const halfW = rw * sizeMul * tanH * aspect * dist;
    c.size = [halfW * 2, (halfW * 2) / c.ref.aspect];
    c.dist = dist;
  }
  return cards;
}

/** Where the figure stands, solved the same way. */
export function layoutFigure(aspect, fovY, camZ, refH = 0.60, refY = 0.60,
  apparent = 0.62) {
  const tanH = Math.tan(fovY / 2);
  const dist = camZ / apparent;
  return {
    z: camZ - dist,
    y: -(refY - 0.5) * 2 * tanH * dist,
    halfH: refH * tanH * dist,
    dist,
  };
}

/**
 * Pose a card for the current frame.
 *
 * `mat` is materialisation (0..1 — every card reads the SAME value, which is
 * what makes them arrive as one event), `rise` is the group's bottom-to-top
 * travel, `settle` drives the overshoot-and-correct, and `float` gates the idle
 * drift so nothing breathes until the whole group has come to rest.
 */
export function poseCard(c, t, s, pointer) {
  const [hx, hy, hz] = c.home;

  // --- rise: one shared journey, with small per-card variation -------------
  const lag = 1 - s.rise;
  // Scaled by distance so the SCREEN travel is the same for near and far cards
  // - the group has to read as one move. Kept short enough that they are still
  // on stage when they materialise; drop them further and the moment the brief
  // cares about most happens below the bottom edge.
  const drop = c.dist * 0.28 * c.launch;
  const y = hy - drop * lag * lag;

  // --- settle: a single damped correction, not a bounce --------------------
  const over = s.settle * c.dist * 0.030 * c.launch;

  // --- idle float, only once the group has settled -------------------------
  const p = t * c.speed + c.phase;
  const scale = c.dist * 0.09;
  const fy = Math.sin(p) * c.bobY * scale * s.float;
  const fx = Math.cos(p * 0.78 + 1.1) * c.bobX * scale * s.float;
  const fz = Math.sin(p * 0.51 + 2.2) * 0.10 * s.float;

  // --- pointer parallax: nearer cards react more, as they would in life ----
  const near = camNear(c.dist);
  const px = pointer.x * 0.55 * near * s.float;
  const py = -pointer.y * 0.34 * near * s.float;

  let posX = hx + fx + px;
  let posY = y + fy + over + py;
  let posZ = hz + fz + c.hover * 0.18;

  // Enforce exclusion zone during floating / hovering so idle motion never penetrates figure silhouette
  if (Math.abs(posX) < EXCLUSION_X && posY > EXCLUSION_Y_MIN && posY < EXCLUSION_Y_MAX && Math.abs(posZ) < EXCLUSION_Z) {
    const signX = posX >= 0 ? 1 : -1;
    posX = signX * (EXCLUSION_X + 0.35);
    posZ = posZ - 0.45;
  }

  const pos = [posX, posY, posZ];

  const rot = [
    c.rest[0] + Math.sin(p * 0.63) * c.swing * s.float
      - pointer.y * 0.07 * near + c.hover * 0.06,
    c.rest[1] + Math.cos(p * 0.55 + 0.7) * c.swing * s.float
      + pointer.x * 0.10 * near - c.hover * 0.07,
    c.rest[2] + c.spin * lag,
  ];

  // materialising cards arrive slightly small, so the group lands with a push
  const grow = (0.88 + 0.12 * s.mat) * (1 + c.hover * 0.04);
  return { pos, rot, scale: [c.size[0] * grow, c.size[1] * grow] };
}

function camNear(dist) {
  return Math.min(1.6, 8.2 / Math.max(dist, 1));
}
