/**
 * REBORNFENIX (RBFX) — app.js
 * Wallet connection, mint interface, particle canvas, countdown, rune gallery, animations
 */

'use strict';

/* ══════════════════════════════════════════════════
   1. CONSTANTS & STATE
══════════════════════════════════════════════════ */

const CONFIG = {
  MINT_DATE:                new Date('2025-07-01T18:00:00Z'), // Set your actual mint date
  TOTAL_SUPPLY:             22222,
  MINT_PRICE_USDC:          10,
  MINT_PRICE_LAMPORTS:      10_000_000, // 10 USDC, 6 decimals
  FOUNDING_WARRIOR_PRICE:   10_000_000 * 10, // 100 USDC, 6 decimals
  FOUNDING_WARRIOR_SUPPLY:  22,
  GENERATION_SIZE:          2222,       // warriors per generation
  GENERATION_COUNT:         10,
  CONTRACT_ADDRESS:         'TBA', // Replace with actual Candy Machine ID pre-launch
  NETWORK:                  'mainnet-beta',
  MAX_PER_WALLET:           1,
};

// Simulated minted count — replace with on-chain fetch in production
let state = {
  mintedCount:         1847,  // Demo value — hook to Candy Machine API
  foundingMinted:      0,     // Demo value — Founding Warriors claimed
  walletConnected:     false,
  walletAddress:       null,
  walletAdapter:       null,
  minting:             false,
  fwMinting:           false,
  // fw wallet state (separate connect flow)
  fwWalletConnected:   false,
  fwWalletAddress:     null,
};

/* ══════════════════════════════════════════════════
   GENERATION DEFINITIONS
══════════════════════════════════════════════════ */

const GENERATIONS = [
  { gen: 1,  name: 'Phoenix Guard',  color: '#C0392B', start: 1,     end: 2222  },
  { gen: 2,  name: 'Gold Battalion', color: '#D4AC0D', start: 2223,  end: 4444  },
  { gen: 3,  name: 'Azure Vanguard', color: '#1E8BC3', start: 4445,  end: 6666  },
  { gen: 4,  name: 'Emerald Order',  color: '#27AE60', start: 6667,  end: 8888  },
  { gen: 5,  name: 'Violet Cohort',  color: '#8E44AD', start: 8889,  end: 11110 },
  { gen: 6,  name: 'Amber Legion',   color: '#E67E22', start: 11111, end: 13332 },
  { gen: 7,  name: 'Teal Warband',   color: '#17A589', start: 13333, end: 15554 },
  { gen: 8,  name: 'Crimson Rose',   color: '#E91E8C', start: 15555, end: 17776 },
  { gen: 9,  name: 'Silver Phalanx', color: '#ABADB3', start: 17777, end: 19998 },
  { gen: 10, name: 'Iron Born',      color: '#6D6A6A', start: 19999, end: 22222 },
];

/**
 * Returns the generation object for a given token number (1-indexed).
 * @param {number} tokenNumber
 * @returns {object}
 */
function getGenerationForToken(tokenNumber) {
  for (const g of GENERATIONS) {
    if (tokenNumber >= g.start && tokenNumber <= g.end) return g;
  }
  return GENERATIONS[GENERATIONS.length - 1]; // fallback: Iron Born
}

/**
 * Returns the generation the NEXT mint would fall into,
 * based on current minted count (next token = mintedCount + 1).
 */
function getCurrentGeneration() {
  const nextToken = state.mintedCount + 1;
  return getGenerationForToken(nextToken);
}

/* ══════════════════════════════════════════════════
   2. ELDER FUTHARK RUNE DATA
══════════════════════════════════════════════════ */

const ELDER_FUTHARK = [
  { sym: 'ᚠ', name: 'Fehu',   meaning: 'Cattle, wealth', lore: 'The rune of prosperity and abundance. Fehu is the primal force of creation — mobile wealth that flows and grows. It is the fire of ambition and the reward for bold action.' },
  { sym: 'ᚢ', name: 'Uruz',   meaning: 'Aurochs, strength', lore: 'Raw, untamed power. The auroch that cannot be domesticated. Uruz is the force within you that refuses to break — primordial endurance, the strength of the wild.' },
  { sym: 'ᚦ', name: 'Thurisaz',meaning: 'Giant, thorn', lore: 'The force of chaos, directed. A thorn that wounds what touches it carelessly. Thurisaz is the warrior\'s instinct — the power to destroy what must be destroyed.' },
  { sym: 'ᚨ', name: 'Ansuz',  meaning: 'God, word, breath', lore: 'The breath of Odin. Divine inspiration, wisdom transmitted through sound. Ansuz is the rune of the poet, the strategist, the one who sees through the noise to truth.' },
  { sym: 'ᚱ', name: 'Raidho',  meaning: 'Ride, journey', lore: 'The cosmic wheel in motion. Every warrior is on a journey — Raidho ensures the path is taken with correct rhythm. Right action at the right moment.' },
  { sym: 'ᚲ', name: 'Kenaz',  meaning: 'Torch, fire', lore: 'Controlled fire — the torch that illuminates without consuming. Kenaz is the craftsman\'s fire, the forge, the creative spark that transforms raw material into art.' },
  { sym: 'ᚷ', name: 'Gebo',   meaning: 'Gift, exchange', lore: 'The sacred exchange between equals. What you give, you receive. Gebo is the rune of balance — every act of generosity returns amplified. The economy of spirit.' },
  { sym: 'ᚹ', name: 'Wunjo',  meaning: 'Joy, harmony', lore: 'The culmination of effort. Wunjo is not idle happiness — it is the deep satisfaction of a warrior who has fought well and earned their peace. The harmony of a life aligned.' },
  { sym: 'ᚺ', name: 'Hagalaz', meaning: 'Hail, disruption', lore: 'Controlled chaos. The hailstorm that destroys the old crop so the new one can grow. Hagalaz is transformation through trial — the necessary catastrophe before rebirth.' },
  { sym: 'ᚾ', name: 'Naudhiz', meaning: 'Need, necessity', lore: 'The fire born of friction. Necessity is the forge of will. Naudhiz is the rune of the warrior who has nothing left but still fights — the primal force of survival.' },
  { sym: 'ᛁ', name: 'Isa',    meaning: 'Ice, stillness', lore: 'Perfect stillness. Not weakness — the power of the pause before the strike. Isa is the warrior who waits, who observes, who moves only when the moment is right.' },
  { sym: 'ᛃ', name: 'Jera',   meaning: 'Year, harvest', lore: 'The slow turning of the cosmic wheel. What is planted is harvested. Jera is the rune of patience — the absolute certainty that sustained effort bears fruit, always.' },
  { sym: 'ᛇ', name: 'Eihwaz', meaning: 'Yew tree, axis', lore: 'The axis mundi — the world tree Yggdrasil. The connection between all realms. Eihwaz is the rune of the warrior who stands firm when all others shake.' },
  { sym: 'ᛈ', name: 'Perthro', meaning: 'Lot cup, fate', lore: 'The mystery of fate. The cup from which fate is cast. Perthro is the rune of the unknowable — the coin flip that changes everything. Embrace uncertainty.' },
  { sym: 'ᛉ', name: 'Algiz',  meaning: 'Elk, protection', lore: 'The elk horn that wards off wolves. Algiz is pure protection — the warrior\'s shield, the border that cannot be crossed. The instinct that saves your life.' },
  { sym: 'ᛊ', name: 'Sowilo', meaning: 'Sun, victory', lore: 'The sun wheel. Unstoppable momentum. Victory is not a destination — it is a direction. Sowilo is the rune of the warrior who has aligned with the force of the cosmos itself.' },
  { sym: 'ᛏ', name: 'Tiwaz',  meaning: 'Tyr, justice', lore: 'The rune of the war god Tyr, who sacrificed his hand for cosmic order. Tiwaz is the warrior who pays the price for what is right, without hesitation and without regret.' },
  { sym: 'ᛒ', name: 'Berkano', meaning: 'Birch, rebirth', lore: 'The birch tree that grows through cracks in stone. Berkano is the rune of regeneration — the phoenix principle. What is burned will grow back, stronger.' },
  { sym: 'ᛖ', name: 'Ehwaz',  meaning: 'Horse, movement', lore: 'The bond between warrior and horse — trust, partnership, synchronized motion. Ehwaz is the rune of aligned action. When you move in perfect harmony with your allies.' },
  { sym: 'ᛗ', name: 'Mannaz', meaning: 'Human, self', lore: 'The rune of humanity. Not weakness — humanity at its highest expression. Mannaz is the reminder that you are both the warrior and the weapon; master yourself.' },
  { sym: 'ᛚ', name: 'Laguz',  meaning: 'Water, flow', lore: 'The flow of the river that cannot be stopped — only redirected. Laguz is the rune of intuition and adaptability. The warrior who flows around obstacles rather than breaking against them.' },
  { sym: 'ᛜ', name: 'Ingwaz', meaning: 'Ing, potential', lore: 'The contained potential of the seed before it germinates. Ingwaz is the rune of internal completion — the energy that builds until it must express itself. Explosive potential.' },
  { sym: 'ᛞ', name: 'Dagaz',  meaning: 'Day, dawn', lore: 'The moment of dawn — the liminal space between darkness and light. Dagaz is the rune of the breakthrough moment, the paradigm shift. The day the warrior was reborn.' },
  { sym: 'ᛟ', name: 'Othalan', meaning: 'Inheritance, home', lore: 'The ancestral inheritance. Not just land — the accumulated wisdom of every warrior who came before you. Othalan is the rune of legacy. What will you leave?' },
];

/* ══════════════════════════════════════════════════
   3. LOADING SCREEN
══════════════════════════════════════════════════ */

function dismissLoadingScreen() {
  const screen = document.getElementById('loading-screen');
  if (!screen) return;
  // Wait for loading bar animation to finish, then fade out
  setTimeout(() => {
    screen.classList.add('fade-out');
    screen.addEventListener('transitionend', () => {
      screen.remove();
    }, { once: true });
  }, 1600);
}

/* ══════════════════════════════════════════════════
   4. PARTICLE CANVAS — Norse Runes
══════════════════════════════════════════════════ */

function initParticleCanvas() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }

  resize();
  window.addEventListener('resize', resize);

  const RUNES = ['ᚠ', 'ᚢ', 'ᚦ', 'ᚨ', 'ᚱ', 'ᚲ', 'ᚷ', 'ᚹ', 'ᚺ', 'ᚾ', 'ᛁ', 'ᛃ', 'ᛈ', 'ᛉ', 'ᛊ', 'ᛏ', 'ᛒ', 'ᛖ', 'ᛗ', 'ᛚ', 'ᛜ', 'ᛞ', 'ᛟ'];
  const PARTICLE_COUNT = 55;

  class Particle {
    constructor() { this.reset(true); }

    reset(initial = false) {
      this.x     = Math.random() * (canvas.width  || window.innerWidth);
      this.y     = initial
        ? Math.random() * (canvas.height || window.innerHeight)
        : (canvas.height || window.innerHeight) + 20;
      this.vy    = -(Math.random() * 0.4 + 0.15);
      this.vx    = (Math.random() - 0.5) * 0.3;
      this.size  = Math.random() * 18 + 10;
      this.rune  = RUNES[Math.floor(Math.random() * RUNES.length)];
      this.alpha = 0;
      this.maxAlpha = Math.random() * 0.22 + 0.06;
      this.fadeIn  = true;
      this.rotate  = Math.random() * Math.PI * 2;
      this.rotateV = (Math.random() - 0.5) * 0.005;
      this.life    = 0;
      this.maxLife = Math.random() * 800 + 400;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.rotate += this.rotateV;
      this.life++;

      const lifeRatio = this.life / this.maxLife;

      if (lifeRatio < 0.1) {
        this.alpha = (lifeRatio / 0.1) * this.maxAlpha;
      } else if (lifeRatio > 0.8) {
        this.alpha = ((1 - lifeRatio) / 0.2) * this.maxAlpha;
      } else {
        this.alpha = this.maxAlpha;
      }

      if (this.life >= this.maxLife) this.reset();
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.rotate);
      ctx.globalAlpha = this.alpha;
      ctx.font = `${this.size}px 'Cinzel Decorative', serif`;
      ctx.fillStyle = '#c9a84c';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this.rune, 0, 0);
      ctx.restore();
    }
  }

  // Starfield particles
  class Star {
    constructor() { this.reset(true); }

    reset(initial = false) {
      this.x = Math.random() * (canvas.width || window.innerWidth);
      this.y = initial
        ? Math.random() * (canvas.height || window.innerHeight)
        : Math.random() * (canvas.height || window.innerHeight);
      this.size  = Math.random() * 1.5;
      this.alpha = Math.random() * 0.6 + 0.1;
      this.twinkle = Math.random() * Math.PI * 2;
      this.twinkleSpeed = Math.random() * 0.02 + 0.005;
    }

    update() {
      this.twinkle += this.twinkleSpeed;
      this.alpha = 0.1 + Math.sin(this.twinkle) * 0.35 + 0.25;
    }

    draw() {
      ctx.save();
      ctx.globalAlpha = Math.max(0, this.alpha);
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  const particles = Array.from({ length: PARTICLE_COUNT }, () => new Particle());
  const stars     = Array.from({ length: 120 }, () => new Star());

  let rafId;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    stars.forEach(s => { s.update(); s.draw(); });
    particles.forEach(p => { p.update(); p.draw(); });

    rafId = requestAnimationFrame(animate);
  }

  animate();

  // Pause when tab is hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(rafId);
    else animate();
  });
}

/* ══════════════════════════════════════════════════
   5. COUNTDOWN TIMER
══════════════════════════════════════════════════ */

function initCountdown() {
  const els = {
    days:  document.getElementById('cd-days'),
    hours: document.getElementById('cd-hours'),
    mins:  document.getElementById('cd-mins'),
    secs:  document.getElementById('cd-secs'),
  };

  if (!els.days) return;

  function pad(n) { return String(n).padStart(2, '0'); }

  function tick() {
    const now  = Date.now();
    const diff = CONFIG.MINT_DATE.getTime() - now;

    if (diff <= 0) {
      // Mint is live!
      els.days.textContent  = '00';
      els.hours.textContent = '00';
      els.mins.textContent  = '00';
      els.secs.textContent  = '00';

      const label = document.querySelector('.countdown-label');
      if (label) {
        label.textContent = '🔥 Mint is LIVE!';
        label.style.color = '#c9a84c';
      }
      return;
    }

    const days  = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const mins  = Math.floor((diff % 3600000)  / 60000);
    const secs  = Math.floor((diff % 60000)    / 1000);

    els.days.textContent  = pad(days);
    els.hours.textContent = pad(hours);
    els.mins.textContent  = pad(mins);
    els.secs.textContent  = pad(secs);
  }

  tick();
  setInterval(tick, 1000);
}

/* ══════════════════════════════════════════════════
   6. RUNE GALLERY
══════════════════════════════════════════════════ */

function buildRuneGallery() {
  const grid = document.getElementById('rune-grid');
  if (!grid) return;

  ELDER_FUTHARK.forEach((rune, i) => {
    const card = document.createElement('div');
    card.className = 'rune-card';
    card.setAttribute('role', 'listitem');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', `${rune.name}: ${rune.meaning}`);
    card.style.animationDelay = `${i * 0.04}s`;

    card.innerHTML = `
      <span class="rune-symbol" aria-hidden="true">${rune.sym}</span>
      <div class="rune-name">${rune.name}</div>
      <div class="rune-meaning">${rune.meaning}</div>
      <div class="rune-tooltip" aria-hidden="true">
        <span class="rune-symbol">${rune.sym}</span>
        <div class="rune-name">${rune.name}</div>
        <div class="rune-lore">${rune.lore}</div>
      </div>
    `;

    grid.appendChild(card);
  });
}

/* ══════════════════════════════════════════════════
   7. SUPPLY DISPLAY
══════════════════════════════════════════════════ */

function updateSupplyDisplay() {
  const minted    = state.mintedCount;
  const total     = CONFIG.TOTAL_SUPPLY;
  const remaining = total - minted;
  const pct       = (minted / total) * 100;

  const mintedEl    = document.getElementById('minted-count');
  const barEl       = document.getElementById('supply-bar');
  const remainingEl = document.getElementById('remaining-text');

  if (mintedEl)    mintedEl.textContent    = minted.toLocaleString();
  if (barEl)       barEl.style.width       = `${Math.max(pct, 0.3)}%`;
  if (remainingEl) remainingEl.textContent = `${remaining.toLocaleString()} remaining`;

  // Update generation banner
  updateGenerationBanner();

  // Update founding warrior counter
  updateFoundingWarriorCounter();
}

function updateGenerationBanner() {
  const gen        = getCurrentGeneration();
  const nextToken  = state.mintedCount + 1;
  const nameEl     = document.getElementById('current-gen-name');
  const tokensEl   = document.getElementById('current-gen-tokens');
  const bannerEl   = document.getElementById('current-gen-banner');

  if (!nameEl || !gen) return;

  nameEl.textContent   = `Generation ${gen.gen} — ${gen.name}`;
  nameEl.style.color   = gen.color;
  if (tokensEl) {
    tokensEl.textContent = `Token #${nextToken.toLocaleString()} of #${gen.start.toLocaleString()}–${gen.end.toLocaleString()}`;
  }

  // Pulse border color to match current generation
  if (bannerEl) {
    bannerEl.style.borderColor = `${gen.color}55`;
    bannerEl.style.background  = `linear-gradient(135deg, ${gen.color}08, transparent)`;
  }
}

function updateFoundingWarriorCounter() {
  const fw          = CONFIG.FOUNDING_WARRIOR_SUPPLY;
  const minted      = state.foundingMinted;
  const remaining   = fw - minted;
  const pct         = (minted / fw) * 100;

  const remainingEl = document.getElementById('fw-remaining');
  const barEl       = document.getElementById('fw-supply-bar');

  if (remainingEl) remainingEl.textContent = remaining;
  if (barEl)       barEl.style.width       = `${Math.max(pct, 0)}%`;
}

/* ══════════════════════════════════════════════════
   8. WALLET CONNECTION (Phantom / Solana)
══════════════════════════════════════════════════ */

function getProvider() {
  if ('phantom' in window) {
    const provider = window.phantom?.solana;
    if (provider?.isPhantom) return provider;
  }

  // Fallback: check for generic Solana adapter
  if ('solana' in window && window.solana?.isPhantom) {
    return window.solana;
  }

  return null;
}

function shortenAddress(addr) {
  if (!addr) return '';
  return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}

function setWalletUI(connected, address = null) {
  const connectBtn  = document.getElementById('connect-wallet-btn');
  const mintBtn     = document.getElementById('mint-button');
  const walletInfo  = document.getElementById('wallet-connected-info');
  const addrDisplay = document.getElementById('wallet-address-display');

  state.walletConnected = connected;
  state.walletAddress   = address;

  if (connected && address) {
    if (connectBtn)  connectBtn.style.display  = 'none';
    if (mintBtn)     mintBtn.style.display      = 'inline-flex';
    if (walletInfo)  walletInfo.style.display   = 'block';
    if (addrDisplay) addrDisplay.textContent    = shortenAddress(address);
  } else {
    if (connectBtn)  connectBtn.style.display   = '';
    if (mintBtn)     mintBtn.style.display       = 'none';
    if (walletInfo)  walletInfo.style.display    = 'none';
  }
}

function showMintStatus(msg, type = 'info') {
  const el = document.getElementById('mint-status');
  if (!el) return;
  el.textContent  = msg;
  el.className    = `mint-status ${type}`;
  el.style.display = 'block';
}

function hideMintStatus() {
  const el = document.getElementById('mint-status');
  if (el) el.style.display = 'none';
}

async function connectWallet() {
  const provider = getProvider();

  if (!provider) {
    // Phantom not installed — open install page
    showMintStatus(
      'Phantom wallet not detected. Opening download page...',
      'error'
    );
    setTimeout(() => window.open('https://phantom.app/', '_blank'), 1200);
    return;
  }

  try {
    showMintStatus('Requesting wallet connection...', 'info');
    const resp = await provider.connect();
    const pubkey = resp.publicKey.toString();

    state.walletAdapter = provider;
    setWalletUI(true, pubkey);
    showMintStatus(`Connected: ${shortenAddress(pubkey)}`, 'success');

    // Listen for disconnect
    provider.on('disconnect', () => {
      setWalletUI(false);
      showMintStatus('Wallet disconnected.', 'info');
    });

    // Listen for account change
    provider.on('accountChanged', (pubkey) => {
      if (pubkey) {
        setWalletUI(true, pubkey.toString());
      } else {
        provider.connect().catch(() => setWalletUI(false));
      }
    });

  } catch (err) {
    if (err.code === 4001) {
      showMintStatus('Connection cancelled by user.', 'error');
    } else {
      console.error('Wallet connect error:', err);
      showMintStatus(`Connection failed: ${err.message || 'Unknown error'}`, 'error');
    }
  }
}

/* ══════════════════════════════════════════════════
   9. MINT LOGIC
   In production: integrate with Metaplex Candy Machine v3 SDK
   This demo simulates the flow with a realistic UX
══════════════════════════════════════════════════ */

async function mintNFT() {
  if (!state.walletConnected || !state.walletAdapter) {
    showMintStatus('Please connect your wallet first.', 'error');
    return;
  }

  if (state.minting) return;
  state.minting = true;

  const mintBtn = document.getElementById('mint-button');
  if (mintBtn) {
    mintBtn.disabled    = true;
    mintBtn.textContent = '⏳  Minting...';
  }

  try {
    // ─── PRODUCTION INTEGRATION POINT ───────────────────────────
    // Replace this block with actual Candy Machine v3 mint:
    //
    // import { Metaplex, walletAdapterIdentity } from "@metaplex-foundation/js";
    // import { Connection, clusterApiUrl } from "@solana/web3.js";
    //
    // const connection = new Connection(clusterApiUrl('mainnet-beta'));
    // const metaplex   = Metaplex.make(connection)
    //   .use(walletAdapterIdentity(state.walletAdapter));
    //
    // const candyMachineAddress = new PublicKey(CONFIG.CONTRACT_ADDRESS);
    // const candyMachine        = await metaplex.candyMachines().findByAddress({ address: candyMachineAddress });
    //
    // const { nft, response } = await metaplex.candyMachines().mint({
    //   candyMachine,
    //   collectionUpdateAuthority: candyMachine.authorityAddress,
    // });
    //
    // const txHash = response.signature;
    // ────────────────────────────────────────────────────────────

    showMintStatus('Approving transaction in your wallet...', 'info');

    // Simulate wallet approval delay
    await sleep(1500);

    showMintStatus('Transaction submitted. Confirming on Solana...', 'info');

    // Simulate blockchain confirmation
    await sleep(2500);

    // Pick a random rune for the success modal
    const mintedRune = ELDER_FUTHARK[Math.floor(Math.random() * ELDER_FUTHARK.length)];
    const fakeTxHash = generateFakeTxHash();

    // Update state
    state.mintedCount += 1;
    updateSupplyDisplay();

    // Show success
    showMintStatus(`Success! ${mintedRune.name} (${mintedRune.sym}) has been claimed.`, 'success');
    openSuccessModal(mintedRune, fakeTxHash);

  } catch (err) {
    console.error('Mint error:', err);

    let userMsg = 'Mint failed. ';
    if (err.message?.includes('insufficient funds')) {
      userMsg += 'Insufficient USDC or SOL for fees.';
    } else if (err.message?.includes('already minted')) {
      userMsg += 'This wallet has already claimed a rune.';
    } else if (err.code === 4001) {
      userMsg = 'Transaction cancelled by user.';
    } else {
      userMsg += err.message || 'Unknown error. Please try again.';
    }

    showMintStatus(userMsg, 'error');

  } finally {
    state.minting = false;
    if (mintBtn) {
      mintBtn.disabled   = false;
      mintBtn.innerHTML  = 'ᚠ &nbsp; JOIN THE LEGION — 10 USDC';
    }
  }
}

/* ══════════════════════════════════════════════════
   FOUNDING WARRIOR — WALLET + MINT
══════════════════════════════════════════════════ */

function showFWMintStatus(msg, type = 'info') {
  const el = document.getElementById('fw-mint-status');
  if (!el) return;
  el.textContent   = msg;
  el.className     = `mint-status ${type}`;
  el.style.display = 'block';
}

function hideFWMintStatus() {
  const el = document.getElementById('fw-mint-status');
  if (el) el.style.display = 'none';
}

function setFWWalletUI(connected, address = null) {
  const connectBtn  = document.getElementById('fw-connect-wallet-btn');
  const mintBtn     = document.getElementById('fw-mint-button');
  const walletInfo  = document.getElementById('fw-wallet-connected-info');
  const addrDisplay = document.getElementById('fw-wallet-address-display');

  state.fwWalletConnected = connected;
  state.fwWalletAddress   = address;

  if (connected && address) {
    if (connectBtn)  connectBtn.style.display  = 'none';
    if (mintBtn)     mintBtn.style.display      = 'inline-flex';
    if (walletInfo)  walletInfo.style.display   = 'block';
    if (addrDisplay) addrDisplay.textContent    = shortenAddress(address);
  } else {
    if (connectBtn)  connectBtn.style.display   = '';
    if (mintBtn)     mintBtn.style.display       = 'none';
    if (walletInfo)  walletInfo.style.display    = 'none';
  }
}

async function connectFWWallet() {
  const provider = getProvider();

  if (!provider) {
    showFWMintStatus('Phantom wallet not detected. Opening download page...', 'error');
    setTimeout(() => window.open('https://phantom.app/', '_blank'), 1200);
    return;
  }

  try {
    showFWMintStatus('Requesting wallet connection...', 'info');
    const resp   = await provider.connect();
    const pubkey = resp.publicKey.toString();

    state.walletAdapter = provider;
    setFWWalletUI(true, pubkey);
    showFWMintStatus(`Connected: ${shortenAddress(pubkey)}`, 'success');

    provider.on('disconnect', () => {
      setFWWalletUI(false);
      showFWMintStatus('Wallet disconnected.', 'info');
    });

    provider.on('accountChanged', (pk) => {
      if (pk) setFWWalletUI(true, pk.toString());
      else provider.connect().catch(() => setFWWalletUI(false));
    });

  } catch (err) {
    if (err.code === 4001) {
      showFWMintStatus('Connection cancelled by user.', 'error');
    } else {
      showFWMintStatus(`Connection failed: ${err.message || 'Unknown error'}`, 'error');
    }
  }
}

async function mintFoundingWarrior() {
  if (!state.fwWalletConnected && !state.walletConnected) {
    showFWMintStatus('Please connect your wallet first.', 'error');
    return;
  }

  const remaining = CONFIG.FOUNDING_WARRIOR_SUPPLY - state.foundingMinted;
  if (remaining <= 0) {
    showFWMintStatus('All 22 Founding Warrior slots have been claimed.', 'error');
    return;
  }

  if (state.fwMinting) return;
  state.fwMinting = true;

  const mintBtn = document.getElementById('fw-mint-button');
  if (mintBtn) {
    mintBtn.disabled    = true;
    mintBtn.textContent = '⏳  Processing...';
  }

  try {
    // ─── PRODUCTION INTEGRATION POINT ───────────────────────────
    // Founding Warriors use a separate Candy Machine or mint authority
    // with a price of 100 USDC (100_000_000 micro-USDC).
    //
    // After minting, the team contacts the buyer via email associated
    // with their wallet or via Discord to collect:
    //   - Chosen warrior name
    //   - Zodiac sign
    //
    // The NFT metadata is then configured and the token delivered.
    // ────────────────────────────────────────────────────────────

    showFWMintStatus('Approving transaction in your wallet... (100 USDC)', 'info');
    await sleep(1500);

    showFWMintStatus('Transaction submitted. Confirming on Solana...', 'info');
    await sleep(2500);

    // Update state
    state.foundingMinted += 1;
    updateFoundingWarriorCounter();

    const fakeTxHash = generateFakeTxHash();
    showFWMintStatus(`Success! Founding Warrior slot #${state.foundingMinted} claimed. Check your email — we will be in touch within 24 hours.`, 'success');
    openFWSuccessModal(fakeTxHash);

  } catch (err) {
    console.error('Founding Warrior mint error:', err);

    let userMsg = 'Mint failed. ';
    if (err.message?.includes('insufficient funds')) {
      userMsg += 'Insufficient USDC (100 USDC required) or SOL for fees.';
    } else if (err.code === 4001) {
      userMsg = 'Transaction cancelled by user.';
    } else {
      userMsg += err.message || 'Unknown error. Please try again.';
    }

    showFWMintStatus(userMsg, 'error');

  } finally {
    state.fwMinting = false;
    if (mintBtn) {
      mintBtn.disabled   = false;
      mintBtn.innerHTML  = '⚜ &nbsp; CLAIM YOUR TITLE — 100 USDC';
    }
  }
}

function openFWSuccessModal(txHash) {
  const modal   = document.getElementById('fw-success-modal');
  const txEl    = document.getElementById('fw-success-tx');
  const shareBtn= document.getElementById('fw-share-btn');
  if (!modal) return;

  if (txEl) txEl.textContent = `TX: ${shortenAddress(txHash)}`;

  if (shareBtn) {
    shareBtn.onclick = () => {
      const text = encodeURIComponent(
        `I just became one of the 22 FOUNDING WARRIORS of REBORNFENIX. ` +
        `The Imperial Purple is mine. #RBFX #Solana #NFT #FoundingWarrior`
      );
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(window.location.href)}`, '_blank');
    };
  }

  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';

  const closeBtn = document.getElementById('fw-close-modal-btn');
  if (closeBtn) closeBtn.focus();
}

function closeFWSuccessModal() {
  const modal = document.getElementById('fw-success-modal');
  if (!modal) return;
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

function generateFakeTxHash() {
  const chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  return Array.from({ length: 88 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ══════════════════════════════════════════════════
   10. SUCCESS MODAL
══════════════════════════════════════════════════ */

function openSuccessModal(rune, txHash) {
  const modal       = document.getElementById('success-modal');
  const runeDisplay = document.getElementById('success-rune-display');
  const txDisplay   = document.getElementById('success-tx');
  const shareBtn    = document.getElementById('share-btn');
  const subtitleEl  = document.getElementById('success-subtitle');
  const genBadgeEl  = document.getElementById('success-gen-badge');

  if (!modal) return;

  if (runeDisplay) runeDisplay.textContent = rune.sym;
  if (txDisplay)   txDisplay.textContent   = `TX: ${shortenAddress(txHash)}`;

  // Determine which generation the new warrior joined
  const tokenNumber = state.mintedCount; // already incremented before this call
  const gen = getGenerationForToken(tokenNumber);

  if (subtitleEl && gen) {
    subtitleEl.textContent = `Token #${tokenNumber.toLocaleString()} — Generation ${gen.gen}: ${gen.name}. Your place in the Legion of Honour is now permanent on the Solana blockchain.`;
  }

  if (genBadgeEl && gen) {
    genBadgeEl.textContent     = `GEN ${gen.gen} — ${gen.name.toUpperCase()}`;
    genBadgeEl.style.color     = gen.color;
    genBadgeEl.style.background= `${gen.color}18`;
    genBadgeEl.style.border    = `1px solid ${gen.color}55`;
  }

  if (shareBtn) {
    shareBtn.onclick = () => {
      const genText = gen ? ` — Generation ${gen.gen}: ${gen.name}` : '';
      const text = encodeURIComponent(
        `I just joined the REBORNFENIX Legion of Honour${genText}! ` +
        `Token #${tokenNumber.toLocaleString()} of 22,222. One fire. #RBFX #Solana #NFT`
      );
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(window.location.href)}`, '_blank');
    };
  }

  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';

  // Focus trap
  const closeBtn = document.getElementById('close-modal-btn');
  if (closeBtn) closeBtn.focus();
}

function closeSuccessModal() {
  const modal = document.getElementById('success-modal');
  if (!modal) return;
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

/* ══════════════════════════════════════════════════
   11. FAQ ACCORDION
══════════════════════════════════════════════════ */

function initFAQ() {
  const items = document.querySelectorAll('.faq-item');
  items.forEach(item => {
    const btn = item.querySelector('.faq-question');
    if (!btn) return;

    btn.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');

      // Close all others
      items.forEach(i => {
        i.classList.remove('open');
        const b = i.querySelector('.faq-question');
        if (b) b.setAttribute('aria-expanded', 'false');
      });

      if (!isOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });

    // Keyboard support
    btn.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        btn.click();
      }
    });
  });
}

/* ══════════════════════════════════════════════════
   12. SCROLL REVEAL ANIMATIONS
══════════════════════════════════════════════════ */

function initScrollReveal() {
  const revealClasses = ['reveal', 'reveal-left', 'reveal-right'];
  const targets = document.querySelectorAll(revealClasses.map(c => `.${c}`).join(', '));

  if (!('IntersectionObserver' in window)) {
    // Fallback: show everything immediately
    targets.forEach(el => el.classList.add('revealed'));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  targets.forEach(el => observer.observe(el));
}

/* ══════════════════════════════════════════════════
   13. RARITY BAR ANIMATION (Intersection Observer)
══════════════════════════════════════════════════ */

function initRarityBars() {
  const tiers = document.querySelectorAll('.rarity-tier');
  if (!tiers.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Trigger CSS transitions by re-setting widths
        const bar = entry.target.querySelector('.rarity-bar');
        if (bar) {
          const w = bar.style.width;
          bar.style.width = '0%';
          requestAnimationFrame(() => {
            requestAnimationFrame(() => { bar.style.width = w; });
          });
        }
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  tiers.forEach(t => observer.observe(t));
}

/* ══════════════════════════════════════════════════
   14. NAVBAR — scroll effect + hamburger
══════════════════════════════════════════════════ */

function initNavbar() {
  const navbar    = document.getElementById('navbar');
  const hamburger = document.getElementById('nav-hamburger');
  const navLinks  = document.getElementById('nav-links');

  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }, { passive: true });

  hamburger?.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  // Close mobile menu on link click
  navLinks?.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger?.setAttribute('aria-expanded', 'false');
    });
  });
}

/* ══════════════════════════════════════════════════
   15. CONTRACT COPY BUTTON
══════════════════════════════════════════════════ */

function initCopyContract() {
  const btn  = document.getElementById('copy-contract');
  const addr = document.getElementById('contract-address');
  if (!btn || !addr) return;

  btn.addEventListener('click', () => {
    const text = addr.textContent.trim();
    if (text.startsWith('TBA')) {
      btn.textContent = 'Not yet!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    }).catch(() => {
      // Fallback for non-HTTPS
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity  = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    });
  });
}

/* ══════════════════════════════════════════════════
   16. STAGGER ANIMATION INDICES
══════════════════════════════════════════════════ */

function initStaggerChildren() {
  document.querySelectorAll('.stagger-children').forEach(parent => {
    Array.from(parent.children).forEach((child, i) => {
      child.style.transitionDelay = `${i * 0.12}s`;
    });
  });
}

/* ══════════════════════════════════════════════════
   17. AUTO-CONNECT (if previously connected)
══════════════════════════════════════════════════ */

async function tryAutoConnect() {
  const provider = getProvider();
  if (!provider) return;

  try {
    // Silently check if already connected (eagerly connect)
    if (provider.isConnected && provider.publicKey) {
      const pubkey = provider.publicKey.toString();
      setWalletUI(true, pubkey);
      setFWWalletUI(true, pubkey);
      state.walletAdapter = provider;
    }
  } catch (e) {
    // Not previously connected — that's fine
  }
}

/* ══════════════════════════════════════════════════
   18. RUNE GRID KEYBOARD NAVIGATION
══════════════════════════════════════════════════ */

function initRuneGridKeyboard() {
  const grid = document.getElementById('rune-grid');
  if (!grid) return;

  grid.addEventListener('keydown', e => {
    const card = e.target.closest('.rune-card');
    if (!card) return;

    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      // Toggle tooltip visibility via class
      card.classList.toggle('keyboard-active');
    } else if (e.key === 'Escape') {
      card.classList.remove('keyboard-active');
    }
  });
}

/* ══════════════════════════════════════════════════
   19. PHANTOM DEEP LINK (mobile support)
══════════════════════════════════════════════════ */

function getConnectURL() {
  // On mobile, Phantom uses a deep link
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  if (isMobile && !getProvider()) {
    return `https://phantom.app/ul/browse/${encodeURIComponent(window.location.href)}?ref=${encodeURIComponent(window.location.origin)}`;
  }
  return null;
}

/* ══════════════════════════════════════════════════
   20. EVENT LISTENERS SETUP
══════════════════════════════════════════════════ */

function setupEventListeners() {
  // ── Legion — Connect wallet ──
  document.getElementById('connect-wallet-btn')?.addEventListener('click', () => {
    const mobileLink = getConnectURL();
    if (mobileLink) {
      window.location.href = mobileLink;
      return;
    }
    connectWallet();
  });

  // ── Legion — Mint button ──
  document.getElementById('mint-button')?.addEventListener('click', mintNFT);

  // ── Legion — Close success modal ──
  document.getElementById('close-modal-btn')?.addEventListener('click', closeSuccessModal);
  document.getElementById('success-modal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeSuccessModal();
  });

  // ── Founding Warrior — Connect wallet ──
  document.getElementById('fw-connect-wallet-btn')?.addEventListener('click', () => {
    const mobileLink = getConnectURL();
    if (mobileLink) {
      window.location.href = mobileLink;
      return;
    }
    connectFWWallet();
  });

  // ── Founding Warrior — Mint button ──
  document.getElementById('fw-mint-button')?.addEventListener('click', mintFoundingWarrior);

  // ── Founding Warrior — Close success modal ──
  document.getElementById('fw-close-modal-btn')?.addEventListener('click', closeFWSuccessModal);
  document.getElementById('fw-success-modal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeFWSuccessModal();
  });

  // ── ESC key to close any open modal ──
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeSuccessModal();
      closeFWSuccessModal();
    }
  });

  // ── Smooth scroll for anchor links ──
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const offset = 80; // Navbar height
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
}

/* ══════════════════════════════════════════════════
   21. TYPING EFFECT for hero subtitle (optional enhancement)
══════════════════════════════════════════════════ */

function glowOnScroll() {
  // Add subtle parallax to the hero backdrop
  const hero = document.getElementById('hero');
  const backdrop = hero?.querySelector('.hero-backdrop');
  if (!backdrop) return;

  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY;
    if (scrolled < window.innerHeight) {
      backdrop.style.transform = `translateY(${scrolled * 0.3}px)`;
    }
  }, { passive: true });
}

/* ══════════════════════════════════════════════════
   22. FETCH LIVE MINT COUNT (production stub)
══════════════════════════════════════════════════ */

async function fetchMintedCount() {
  // In production, replace with:
  // const connection = new Connection(clusterApiUrl('mainnet-beta'));
  // const candyMachine = await metaplex.candyMachines().findByAddress({ address: ... });
  // state.mintedCount = Number(candyMachine.itemsMinted);
  //
  // For now, we use the simulated value already set in state.
  // Refresh every 30 seconds in production:
  // setInterval(fetchMintedCount, 30000);

  updateSupplyDisplay();
}

/* ══════════════════════════════════════════════════
   23. BOOT SEQUENCE
══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  // Order matters: build DOM elements first, then init behaviors

  // 1. Rune gallery (needs DOM to be ready)
  buildRuneGallery();

  // 2. Supply display
  fetchMintedCount();

  // 3. UI components
  initFAQ();
  initNavbar();
  initStaggerChildren();
  initCopyContract();
  initRuneGridKeyboard();

  // 4. Canvas & animations
  initParticleCanvas();
  initCountdown();
  glowOnScroll();

  // 5. Scroll-driven animations
  initScrollReveal();
  initRarityBars();

  // 5b. Puzzle lightbox (founder section)
  initPuzzleLightbox();

  // 6. Wallet auto-connect (after a brief delay so provider can initialize)
  setTimeout(tryAutoConnect, 800);

  // 7. Event listeners
  setupEventListeners();

  // 8. Dismiss loading screen (after minimum display time)
  dismissLoadingScreen();

  // 9. Log helpful info to console for developers
  console.log(
    '%c⚡ REBORNFENIX (RBFX) %c\n22 Founding Warriors · 22,222 Legion of Honour · One fire.\nSolana NFT Collection\n\nContract: ' + CONFIG.CONTRACT_ADDRESS + '\nNetwork: ' + CONFIG.NETWORK,
    'color: #9D4EDD; font-size: 18px; font-weight: bold;',
    'color: #a8a8b8; font-size: 12px;'
  );
});

/* ══════════════════════════════════════════════════
   24. PUZZLE LIGHTBOX
══════════════════════════════════════════════════ */

function initPuzzleLightbox() {
  const items = document.querySelectorAll('.puzzle-item');
  if (!items.length) return;

  let lightboxEl = null;

  function openLightbox(src, alt, title) {
    // Remove existing lightbox if any
    closeLightbox();

    lightboxEl = document.createElement('div');
    lightboxEl.className = 'puzzle-lightbox';
    lightboxEl.setAttribute('role', 'dialog');
    lightboxEl.setAttribute('aria-modal', 'true');
    lightboxEl.setAttribute('aria-label', title || alt);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'puzzle-lightbox-close';
    closeBtn.textContent = 'ESC · Fechar';
    closeBtn.setAttribute('aria-label', 'Fechar imagem');

    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.className = 'puzzle-lightbox-img';
    // Prevent click on image from closing the lightbox
    img.addEventListener('click', e => e.stopPropagation());

    const caption = document.createElement('div');
    caption.className = 'puzzle-lightbox-caption';
    caption.textContent = title || alt;

    lightboxEl.appendChild(closeBtn);
    lightboxEl.appendChild(img);
    lightboxEl.appendChild(caption);

    document.body.appendChild(lightboxEl);
    document.body.style.overflow = 'hidden';

    // Close on backdrop click
    lightboxEl.addEventListener('click', closeLightbox);

    // Close button
    closeBtn.addEventListener('click', e => {
      e.stopPropagation();
      closeLightbox();
    });

    // Focus the close button for accessibility
    closeBtn.focus();
  }

  function closeLightbox() {
    if (lightboxEl) {
      lightboxEl.remove();
      lightboxEl = null;
    }
    document.body.style.overflow = '';
  }

  // Keyboard: ESC closes lightbox (add to the existing ESC handler)
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && lightboxEl) {
      closeLightbox();
    }
  });

  // Attach click handler to each puzzle item
  items.forEach(item => {
    const img   = item.querySelector('img');
    const title = item.getAttribute('data-title') || '';
    const alt   = img?.getAttribute('alt') || '';
    const src   = img?.getAttribute('src') || '';

    item.addEventListener('click', () => {
      if (src) openLightbox(src, alt, title);
    });

    // Keyboard accessibility
    item.setAttribute('tabindex', '0');
    item.setAttribute('role', 'button');
    item.setAttribute('aria-label', `Ver puzzle: ${title || alt}`);
    item.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (src) openLightbox(src, alt, title);
      }
    });
  });
}

/* ══════════════════════════════════════════════════
   25. PERFORMANCE — Passive listeners & cleanup
══════════════════════════════════════════════════ */

// Debounce utility
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// Throttle utility
function throttle(fn, ms) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= ms) { last = now; fn(...args); }
  };
}

// Expose for external use if needed (e.g., Candy Machine SDK integration)
window.RBFX = {
  config:                   CONFIG,
  state:                    state,
  generations:              GENERATIONS,
  connectWallet,
  mintNFT,
  connectFWWallet,
  mintFoundingWarrior,
  getProvider,
  updateSupplyDisplay,
  getGenerationForToken,
  getCurrentGeneration,
};
