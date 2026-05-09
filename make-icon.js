// Generates a 1024×1024 RGB PNG app icon for Robot Soccer 3D.
// No external deps — uses only zlib (built-in) for the PNG IDAT chunk.

const fs   = require('fs');
const zlib = require('zlib');

const W = 1024, H = 1024;
const buf = Buffer.alloc(W * H * 3); // RGB (no alpha — icon must be opaque)

// ---------- pixel helpers ----------
function clamp255(v) { return v < 0 ? 0 : v > 255 ? 255 : v | 0; }
function setPx(x, y, r, g, b) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  const i = (y * W + x) * 3;
  buf[i] = clamp255(r); buf[i+1] = clamp255(g); buf[i+2] = clamp255(b);
}
function blendPx(x, y, r, g, b, a) {
  if (x < 0 || y < 0 || x >= W || y >= H || a <= 0) return;
  const i = (y * W + x) * 3;
  const af = a;
  buf[i]   = clamp255(r * af + buf[i]   * (1 - af));
  buf[i+1] = clamp255(g * af + buf[i+1] * (1 - af));
  buf[i+2] = clamp255(b * af + buf[i+2] * (1 - af));
}

// ---------- 1. background: vertical gradient (sky blue → field green) ----------
for (let y = 0; y < H; y++) {
  // top: bright sky #5dade2; bottom: pitch green #2d6a3e
  const t = y / (H - 1);
  // ease toward bottom for richer field tone
  const e = t * t;
  const r = 0x5d + (0x2d - 0x5d) * e;
  const g = 0xad + (0x6a - 0xad) * e;
  const b = 0xe2 + (0x3e - 0xe2) * e;
  for (let x = 0; x < W; x++) setPx(x, y, r, g, b);
}

// ---------- 2. green field stripes near the bottom for context ----------
const FIELD_TOP = Math.round(H * 0.62);
for (let y = FIELD_TOP; y < H; y++) {
  const stripeIdx = Math.floor((y - FIELD_TOP) / ((H - FIELD_TOP) / 8));
  const dark = stripeIdx % 2 === 0;
  const r = dark ? 0x2d : 0x35;
  const g = dark ? 0x6a : 0x7e;
  const b = dark ? 0x3e : 0x4c;
  for (let x = 0; x < W; x++) {
    // mix existing gradient with stripe so the field still feels lit
    blendPx(x, y, r, g, b, 0.85);
  }
}

// ---------- 3. drop shadow under the ball ----------
const ballCX = W / 2;
const ballCY = H * 0.55;
const ballR  = 290;
{
  const shadowCY = ballCY + ballR + 50;
  const sxR = ballR * 1.05, syR = ballR * 0.22;
  for (let y = shadowCY - syR; y <= shadowCY + syR; y++) {
    for (let x = ballCX - sxR; x <= ballCX + sxR; x++) {
      const dx = (x - ballCX) / sxR, dy = (y - shadowCY) / syR;
      const d2 = dx * dx + dy * dy;
      if (d2 < 1) {
        const a = (1 - d2) * 0.35;
        blendPx(Math.round(x), Math.round(y), 0, 0, 0, a);
      }
    }
  }
}

// ---------- 4. white soccer ball with sphere shading ----------
function inCircle(x, y, cx, cy, r) {
  const dx = x - cx, dy = y - cy;
  return Math.sqrt(dx * dx + dy * dy) - r; // <0 inside
}
for (let y = Math.floor(ballCY - ballR - 2); y <= Math.ceil(ballCY + ballR + 2); y++) {
  for (let x = Math.floor(ballCX - ballR - 2); x <= Math.ceil(ballCX + ballR + 2); x++) {
    const sd = inCircle(x, y, ballCX, ballCY, ballR);
    if (sd > 1) continue;
    // anti-aliased edge: alpha falls off in last 1.5px
    const a = sd <= 0 ? 1 : Math.max(0, 1 - sd / 1.5);
    // sphere shading: brighter top-left, darker bottom-right
    const nx = (x - ballCX) / ballR, ny = (y - ballCY) / ballR;
    const lit = Math.max(0, -nx * 0.6 - ny * 0.6); // dot with light from top-left
    const shade = 0.78 + lit * 0.22;               // 0.78 .. 1.0
    const v = Math.round(255 * shade);
    blendPx(x, y, v, v, v, a);
  }
}

// ---------- 5. dark outline around the ball ----------
for (let y = Math.floor(ballCY - ballR - 3); y <= Math.ceil(ballCY + ballR + 3); y++) {
  for (let x = Math.floor(ballCX - ballR - 3); x <= Math.ceil(ballCX + ballR + 3); x++) {
    const dx = x - ballCX, dy = y - ballCY;
    const d = Math.sqrt(dx * dx + dy * dy);
    const t = d - ballR; // 0 = exactly on rim
    if (t > -1 && t < 3) {
      const a = Math.exp(-((t - 1) * (t - 1)) / 1.6) * 0.85;
      blendPx(x, y, 12, 12, 16, a);
    }
  }
}

// ---------- 6. black pentagons (12 placed at icosahedron vertex projection) ----------
// Iconic soccer-ball look: central black pentagon + 5 around the front face.
function fillPolygon(pts, r, g, b, alpha = 1) {
  let minX = pts[0][0], maxX = pts[0][0], minY = pts[0][1], maxY = pts[0][1];
  for (const [px, py] of pts) {
    if (px < minX) minX = px; if (px > maxX) maxX = px;
    if (py < minY) minY = py; if (py > maxY) maxY = py;
  }
  for (let y = Math.floor(minY); y <= Math.ceil(maxY); y++) {
    for (let x = Math.floor(minX); x <= Math.ceil(maxX); x++) {
      // 4-sample anti-aliasing
      let hits = 0;
      for (const ox of [0.25, 0.75]) {
        for (const oy of [0.25, 0.75]) {
          let inside = false;
          for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
            const xi = pts[i][0], yi = pts[i][1];
            const xj = pts[j][0], yj = pts[j][1];
            if (((yi > y + oy) !== (yj > y + oy)) &&
                (x + ox < (xj - xi) * (y + oy - yi) / (yj - yi) + xi)) {
              inside = !inside;
            }
          }
          if (inside) hits++;
        }
      }
      if (hits) blendPx(x, y, r, g, b, (hits / 4) * alpha);
    }
  }
}
function pentagon(cx, cy, r, rot) {
  const pts = [];
  for (let i = 0; i < 5; i++) {
    const a = i * (Math.PI * 2 / 5) - Math.PI / 2 + rot;
    pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
  }
  return pts;
}

// Center pentagon (front face)
const PENT_R = 70;
fillPolygon(pentagon(ballCX, ballCY, PENT_R, 0), 18, 18, 24);
// 5 outer pentagons
const OUTER_DIST = PENT_R * 2.55;
const OUTER_R    = PENT_R * 0.9;
for (let i = 0; i < 5; i++) {
  const a = i * (Math.PI * 2 / 5) - Math.PI / 2 + Math.PI / 5;
  const cx = ballCX + Math.cos(a) * OUTER_DIST;
  const cy = ballCY + Math.sin(a) * OUTER_DIST;
  fillPolygon(pentagon(cx, cy, OUTER_R, a + Math.PI / 2), 18, 18, 24);
}

// ---------- 7. specular highlight on the ball (sky reflection) ----------
{
  const hx = ballCX - ballR * 0.45;
  const hy = ballCY - ballR * 0.55;
  const hRX = ballR * 0.30, hRY = ballR * 0.14;
  for (let y = hy - hRY; y <= hy + hRY; y++) {
    for (let x = hx - hRX; x <= hx + hRX; x++) {
      const dx = (x - hx) / hRX, dy = (y - hy) / hRY;
      const d2 = dx * dx + dy * dy;
      if (d2 < 1) {
        const a = (1 - d2) * 0.55;
        // only inside the ball
        if (inCircle(x, y, ballCX, ballCY, ballR - 8) <= 0) {
          blendPx(Math.round(x), Math.round(y), 255, 255, 255, a);
        }
      }
    }
  }
}

// ---------- 8. small robot peeking from behind the ball ----------
// Just two glowing cyan eyes + an antenna ball at the top edge of the ball,
// to telegraph "robot soccer" without crowding the icon.
{
  const eyeY = ballCY - ballR * 0.85;
  const eyeOffX = 95;
  // helmet/cap arc behind the ball top
  const capR = 70;
  for (let y = eyeY - capR; y <= eyeY + 5; y++) {
    for (let x = ballCX - capR; x <= ballCX + capR; x++) {
      const dx = x - ballCX, dy = y - eyeY;
      const d = Math.sqrt(dx * dx + dy * dy);
      const t = d - capR;
      if (t < 0 && y < eyeY) {
        const a = Math.min(1, -t / 6);
        blendPx(x, y, 0x1b, 0x4f, 0x72, 0.92 * a);
      }
    }
  }
  // antenna pole
  for (let y = eyeY - capR - 60; y < eyeY - capR + 6; y++) {
    for (let x = ballCX - 3; x <= ballCX + 3; x++) {
      blendPx(x, y, 0x88, 0x88, 0x88, 1);
    }
  }
  // antenna tip (yellow ball with glow)
  const tipR = 22;
  for (let y = eyeY - capR - 70 - tipR; y <= eyeY - capR - 70 + tipR; y++) {
    for (let x = ballCX - tipR; x <= ballCX + tipR; x++) {
      const dx = x - ballCX, dy = y - (eyeY - capR - 70);
      const d2 = dx * dx + dy * dy;
      const r = tipR;
      if (d2 < r * r) {
        const ratio = Math.sqrt(d2) / r;
        const a = ratio < 0.85 ? 1 : Math.max(0, 1 - (ratio - 0.85) / 0.15);
        // glow halo
        blendPx(x, y, 0xff, 0xed, 0x4a, a);
      } else if (d2 < r * r * 4) {
        const a = Math.max(0, 1 - (Math.sqrt(d2) - r) / r) * 0.35;
        blendPx(x, y, 0xff, 0xed, 0x4a, a);
      }
    }
  }
  // glowing cyan eyes
  function eye(cx, cy) {
    const er = 13;
    // outer glow
    for (let y = cy - er * 2.5; y <= cy + er * 2.5; y++) {
      for (let x = cx - er * 2.5; x <= cx + er * 2.5; x++) {
        const dx = x - cx, dy = y - cy;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d <= er * 2.5) {
          const a = Math.max(0, 1 - d / (er * 2.5)) * 0.5;
          blendPx(Math.round(x), Math.round(y), 0x00, 0xe5, 0xff, a * 0.4);
        }
      }
    }
    // bright core
    for (let y = cy - er; y <= cy + er; y++) {
      for (let x = cx - er; x <= cx + er; x++) {
        const dx = x - cx, dy = y - cy;
        const d2 = dx * dx + dy * dy;
        if (d2 <= er * er) {
          const a = d2 < (er - 2) * (er - 2) ? 1 : Math.max(0, 1 - (Math.sqrt(d2) - (er - 2)) / 2);
          blendPx(x, y, 0xe0, 0xff, 0xff, a);
        }
      }
    }
  }
  eye(ballCX - eyeOffX, eyeY);
  eye(ballCX + eyeOffX, eyeY);
}

// ---------- PNG encoder (no deps) ----------
function crc32(data) {
  // build table once
  if (!crc32.table) {
    crc32.table = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      crc32.table[n] = c >>> 0;
    }
  }
  let c = 0xFFFFFFFF;
  for (let i = 0; i < data.length; i++) c = (c >>> 8) ^ crc32.table[(c ^ data[i]) & 0xFF];
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function chunk(type, body) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(body.length, 0);
  const tBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([tBuf, body])), 0);
  return Buffer.concat([len, tBuf, body, crcBuf]);
}
const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(W, 0);
ihdr.writeUInt32BE(H, 4);
ihdr[8]  = 8;   // bit depth
ihdr[9]  = 2;   // color type RGB
ihdr[10] = 0;
ihdr[11] = 0;
ihdr[12] = 0;
// raw image data: each row prefixed with filter byte (0 = none)
const stride = W * 3;
const raw = Buffer.alloc(H * (1 + stride));
for (let y = 0; y < H; y++) {
  raw[y * (1 + stride)] = 0;
  buf.copy(raw, y * (1 + stride) + 1, y * stride, (y + 1) * stride);
}
const idat = zlib.deflateSync(raw, { level: 9 });
const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
const png = Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);

const outPath = process.argv[2] || 'AppIcon-512@2x.png';
fs.writeFileSync(outPath, png);
console.log('wrote', outPath, png.length, 'bytes', W + 'x' + H);
