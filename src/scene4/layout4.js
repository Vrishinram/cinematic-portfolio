// Scene four's measured geometry — every number read off the supplied
// reference (section 4 image.jpg, 1600x900), which is the source of truth.
// The card sprites and the environment plate are cut from that image by
// tools/extract_s4.py; this module records where each piece goes back.
//
// Coordinates are reference-frame pixels. fitCover() maps the frame onto the
// viewport the way the plate shader does (cover: fill, centre-anchored), so
// the DOM cards and the canvas can never drift apart.

export const FRAME = [1600, 900];

export const CARDS = [
  { id: 'p01_timeless', title: 'Cybersicker: Autonomous SOC AI',
    desc: 'Dual-core autonomous SOC combining an LLM agentic engine (Gemini 2.5 Flash + LangChain) with a deep learning autoencoder, detecting 5+ IoT attack types with 95%+ accuracy.',
    tags: ['Python', 'LangChain', 'Gemini 2.5', 'TensorFlow', 'ChromaDB', 'Streamlit'],
    github: 'https://github.com/Vrishinram/Cybersicker',
    box: [213, 72, 384, 273], depth: 0.45,
    tint: [0.309, 0.334, 0.382] },
  { id: 'p02_game', title: 'IoT Intrusion Detection Model',
    desc: 'Published first-author research in IJNRD (IF 8.76) achieving 98.31% accuracy, 92.09% precision, and 91.90% F-score across 9 IoT attack categories using IMFOHDL-ID.',
    tags: ['Deep Learning', 'Network Security', 'IJNRD IF 8.76', 'BoT-IoT'],
    github: 'https://github.com/Vrishinram/portfolio',
    box: [63, 251, 428, 269], depth: 0.25,
    tint: [0.249, 0.267, 0.295] },
  { id: 'p03_build', title: 'PromptShield: LLM Security Middleware',
    desc: 'Defensive AI security console & real-time prompt injection defense proxy detecting jailbreaks, adversarial attacks, and system prompt leaks.',
    tags: ['AI Security', 'LLM Red Teaming', 'Prompt Injection', 'Python'],
    github: 'https://github.com/Vrishinram/PromptShield',
    box: [566, 41, 471, 288], depth: 0.6,
    tint: [0.414, 0.291, 0.291] },
  { id: 'p04_driven', title: 'ARGUS: Enterprise Security Gateway',
    desc: 'Enterprise LLM security gateway and reverse proxy enforcing real-time PII redaction, token-bucket rate limiting, and automated safety boundary compliance.',
    tags: ['LLM Gateway', 'PII Redaction', 'Safety Proxy', 'Docker'],
    github: 'https://github.com/Vrishinram/ARGUS',
    box: [998, 95, 460, 377], depth: 0.45,
    tint: [0.322, 0.278, 0.261] },
  { id: 'p05_ideas', title: 'GuardRift: LLM Jailbreak Benchmark',
    desc: 'Automated red-teaming framework and jailbreak evaluation suite benchmarking LLM safeguard robustness against multi-turn adversarial injection.',
    tags: ['Red Teaming', 'Jailbreak Eval', 'LLM Safety', 'Python'],
    github: 'https://github.com/Vrishinram/GuardRift',
    box: [394, 358, 232, 198], depth: 0.8,
    tint: [0.39, 0.303, 0.234] },
  { id: 'p06_sound', title: 'CyGuard: Password Strength Suite',
    desc: 'Client-side password evaluation system rating credentials across 5 strength tiers and validating against 10+ billion breached records via Have I Been Pwned k-anonymity API.',
    tags: ['JavaScript', 'HTML5', 'HIBP API', 'k-Anonymity'],
    live: 'https://vrishinram.github.io/Cyberguard/',
    github: 'https://github.com/Vrishinram/Cyberguard',
    box: [568, 364, 173, 203], depth: 0.9,
    tint: [0.336, 0.324, 0.333] },
  { id: 'p07_food', title: 'BruteShield: Adaptive Brute Defense',
    desc: 'Authentication security system enforcing progressive account lockouts, dynamic delay escalation, and real-time suspicious-IP flagging to block credential stuffing.',
    tags: ['Mitigation', 'Rate Limiting', 'Defense Engineering', 'JS'],
    live: 'https://vrishinram.github.io/BruteShield/',
    github: 'https://github.com/Vrishinram/BruteShield',
    box: [698, 366, 211, 204], depth: 1.0,
    tint: [0.336, 0.243, 0.217] },
  { id: 'p08_travel', title: 'CyDetect: ML Email Threat Classifier',
    desc: 'Trained a Random Forest model on 10,000+ samples across 5 threat categories (phishing, malware, BEC, spam, safe) with a 6-feature NLP extraction pipeline.',
    tags: ['Python', 'Flask', 'Scikit-Learn', 'NLTK', 'NLP'],
    github: 'https://github.com/Vrishinram/CyDetect',
    box: [844, 370, 195, 206], depth: 0.9,
    tint: [0.26, 0.32, 0.366] },
  { id: 'p09_space', title: 'rootsecurity: OWASP Top 10 Audit',
    desc: 'Interactive OWASP Top 10 security assessment web platform for startup applications covering 5 attack surfaces with live interactive vulnerability demos and PDF report generation.',
    tags: ['React 19', 'TanStack', 'Tailwind', 'OWASP Top 10'],
    github: 'https://github.com/Vrishinram/rootsecuity',
    box: [988, 364, 231, 208], depth: 0.8,
    tint: [0.336, 0.283, 0.269] },
  { id: 'p10_play', title: 'IGLOO: Living & Ops Orchestrator',
    desc: 'Progressive Web App (PWA) with AI maintenance triage, transparent financial tracking, and digitized visitor gate management built by Team AURA.',
    tags: ['PWA', 'Next.js', 'TypeScript', 'Tailwind CSS'],
    live: 'https://igloo-ruddy.vercel.app',
    github: 'https://github.com/Vrishinram/IGLOO',
    box: [1181, 251, 355, 242], depth: 0.3,
    tint: [0.448, 0.305, 0.235] },
  { id: 'p11_cleaner', title: 'CyAuth: Full-Stack Auth Platform',
    desc: 'Production-grade authentication platform engineered with bcrypt hashing, JWT session security, and rate-limiting aligned to OWASP Top 10 guidelines.',
    tags: ['Node.js', 'Express', 'React', 'JWT', 'Bcrypt'],
    github: 'https://github.com/Vrishinram/CyAuth',
    box: [118, 467, 345, 243], depth: 0.1,
    tint: [0.311, 0.339, 0.263] },
  { id: 'p12_steps', title: 'Port-Checker: Fast Subnet Scanner',
    desc: 'Multi-threaded port scanner covering a full Class-C subnet in under 30 seconds with real-time responsive web dashboard, cutting manual recon by 70%.',
    tags: ['Python', 'Multi-Threading', 'TCP/IP', 'Flask'],
    github: 'https://github.com/Vrishinram/Port-Checker',
    box: [1139, 478, 325, 234], depth: 0.1,
    tint: [0.31, 0.317, 0.302] },
];

// the central figure: crop box in frame px (his lighting is baked in)
export const PERSON = { x: 718, y: 483, w: 160, h: 335 };

// the floor's lit ellipses (centre x, centre y, rx, ry) and the overhead ring,
// used by the live glints the canvas draws over the baked plate
export const FLOOR_OUT = [798, 735, 372, 80];
export const FLOOR_IN = [798, 741, 240, 57];
export const RING = [802, 34, 392, 148];

/** Cover-fit the reference frame onto a viewport. */
export function fitCover(w, h) {
  const s = Math.max(w / FRAME[0], h / FRAME[1]);
  return { s, ox: (w - FRAME[0] * s) / 2, oy: (h - FRAME[1] * s) / 2 };
}

// --------------------------------------------------------------------------
// Portrait is a recomposition, not a crop: cover-fitting a 16:9 amphitheatre
// to a phone leaves only the centre quarter on screen. The plate still cover-
// fits (floor, circle and haze survive centred), and a curated set of cards
// restacks into a column that keeps the reference hierarchy: hero screen up
// top, the small row over the figure, the two green closers at his feet.
// Entries: card index -> centre x/y (viewport fractions), width (vw fraction).
// --------------------------------------------------------------------------
export const PORTRAIT = new Map([
  [2, { cx: 0.50, cy: 0.235, w: 0.80 }],   // build
  [0, { cx: 0.235, cy: 0.385, w: 0.50 }],  // timeless
  [3, { cx: 0.77, cy: 0.39, w: 0.48 }],    // driven
  [6, { cx: 0.325, cy: 0.53, w: 0.29 }],   // food
  [7, { cx: 0.675, cy: 0.53, w: 0.29 }],   // travel
  [10, { cx: 0.20, cy: 0.815, w: 0.48 }],  // cleaner
  [11, { cx: 0.80, cy: 0.815, w: 0.48 }],  // steps
]);
