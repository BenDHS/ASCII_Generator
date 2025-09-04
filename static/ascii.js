// Client-side ASCII conversion matching Python behavior

function drawToCanvas(img, width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, width, height);
  return { canvas, ctx };
}

function getLuminance(data, invert) {
  const lum = (0.2126 * data[0] + 0.7152 * data[1] + 0.0722 * data[2]);
  return invert ? (255 - lum) : lum;
}

async function toAscii(img, settings) {
  const { output_width, char_aspect, black_threshold, ascii_chars, invert } = settings;
  const aspectRatio = img.naturalHeight / img.naturalWidth;
  const outH = Math.max(1, Math.floor(output_width * aspectRatio * char_aspect));
  const { canvas, ctx } = drawToCanvas(img, output_width, outH);
  let pixels;
  try {
    pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  } catch (e) {
    throw new Error('Unable to read pixels from canvas. If using remote images, CORS may block access. Use local uploads.');
  }

  const chars = ascii_chars && ascii_chars.length ? ascii_chars : '@%#*+=-:. ';
  const n = chars.length;
  const lines = [];

  for (let y = 0; y < outH; y++) {
    let line = '';
    for (let x = 0; x < output_width; x++) {
  const idx = (y * output_width + x) * 4;
  const r = pixels[idx + 0], g = pixels[idx + 1], b = pixels[idx + 2];
  const lum = getLuminance([r, g, b], invert);
      if (lum <= black_threshold) {
        line += ' ';
      } else {
        const ci = Math.min(n - 1, Math.floor((lum / 255) * n));
        line += chars[ci];
      }
    }
    lines.push(line);
  }
  return lines.join('\n');
}

function asciiToCanvas(ascii, settings) {
  const { font_size, fg_color, bg_color } = settings;
  const lines = ascii.split('\n');
  const maxLen = Math.max(0, ...lines.map(l => l.length));

  // Measure with an offscreen canvas
  const measure = document.createElement('canvas');
  const mctx = measure.getContext('2d');
  mctx.font = `${font_size}px monospace`;
  const metrics = mctx.measureText('M');
  const charW = Math.max(1, Math.ceil(metrics.width));
  const charH = Math.max(1, Math.ceil(font_size * 1.2));

  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, charW * maxLen);
  canvas.height = Math.max(1, charH * lines.length);
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = bg_color || 'white';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = fg_color || 'black';
  ctx.font = `${font_size}px monospace`;
  ctx.textBaseline = 'top';

  lines.forEach((line, i) => {
    ctx.fillText(line, 0, i * charH);
  });

  return canvas;
}

// Expose
window.toAscii = toAscii;
window.asciiToCanvas = asciiToCanvas;
