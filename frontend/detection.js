const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');

const connStatus = document.getElementById('conn-status');
const connText = document.getElementById('conn-text');
const runStatus = document.getElementById('run-status');
const runText = document.getElementById('run-text');

const humanCount = document.getElementById('human-count');
const fpsValue = document.getElementById('fps-value');
const fpsDisplay = document.getElementById('fps-display');

const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');

const errorDisplay = document.getElementById('error-display');
const personsList = document.getElementById('persons-list');
const logsList = document.getElementById('logs-list');

let ws = null;
let isRunning = false;
let lastFrameTime = Date.now();
let frameCount = 0;
let fpsInterval = null;

let lastLogTime = 0;
let lastDetectionCount = 0;
let stableDetectionCount = 0;
let stableCountFrames = 0;

let pendingFrame = null;
let isRendering = false;

const piIpAddress =
  localStorage.getItem('piIpAddress') ||
  window.location.hostname ||
  'localhost';

const serverUrl =
  piIpAddress === 'localhost' || piIpAddress === window.location.hostname
    ? ''
    : `http://${piIpAddress}:8000`;

console.log('Connecting to server:', piIpAddress);

// ---------------- ERROR HANDLING ----------------
function showError(message) {
  errorDisplay.textContent = message;
  errorDisplay.classList.add('show');
  console.error('Error:', message);
}

function hideError() {
  errorDisplay.classList.remove('show');
}

// ---------------- LOGGING ----------------
async function logDetection(count, persons) {
  try {
    await fetch(`${serverUrl}/log_detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        count: count,
        persons: persons.map(p => ({
          confidence: p.bbox_conf
        }))
      })
    });

    await loadLogs();
  } catch (e) {
    console.error('Failed to log detection:', e);
  }
}

async function loadLogs() {
  try {
    const res = await fetch(`${serverUrl}/logs?limit=10`);
    const data = await res.json();

    if (data.logs && data.logs.length > 0) {
      let logsHTML = '';

      data.logs.forEach(log => {
        const date = new Date(log.timestamp);

        logsHTML += `
          <div class="log-item">
            <div class="log-time">${date.toLocaleTimeString()}</div>
            <div class="log-detail">
              ${date.toLocaleDateString()} - ${log.count} human${log.count !== 1 ? 's' : ''} detected
            </div>
          </div>
        `;
      });

      logsList.innerHTML = logsHTML;
    }
  } catch (e) {
    console.error('Failed to load logs:', e);
  }
}

// ---------------- SKELETON ----------------
const skeleton = [
  [0, 1], [0, 2], [1, 3], [2, 4],
  [0, 5], [0, 6], [5, 6],
  [5, 7], [7, 9], [6, 8], [8, 10],
  [5, 11], [6, 12], [11, 12],
  [11, 13], [13, 15], [12, 14], [14, 16]
];

// ---------------- CANVAS ----------------
function resizeCanvas() {
  const container = document.getElementById('canvas-container');
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ---------------- RENDERING ----------------
function drawFrame(data) {
  pendingFrame = data;

  if (!isRendering) {
    isRendering = true;
    requestAnimationFrame(renderFrame);
  }
}

function renderFrame() {
  if (!pendingFrame) {
    isRendering = false;
    return;
  }

  const data = pendingFrame;
  pendingFrame = null;

  if (data.frame) {
    const img = new Image();

    img.onload = () => {
      const scale = Math.min(
        canvas.width / img.width,
        canvas.height / img.height
      );

      const x = (canvas.width - img.width * scale) / 2;
      const y = (canvas.height - img.height * scale) / 2;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // mirror
      ctx.save();
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(
        img,
        canvas.width - x - img.width * scale,
        y,
        img.width * scale,
        img.height * scale
      );
      ctx.restore();

      if (data.persons && data.persons.length > 0) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);

        for (const person of data.persons) {
          const kps = person.keypoints;

          if (person.bbox) {
            const [x1, y1, x2, y2] = person.bbox;
            const conf = person.bbox_conf || 1.0;

            const flippedX1 = img.width - x2;
            const flippedX2 = img.width - x1;

            ctx.strokeStyle = `rgba(0,255,136,${conf})`;
            ctx.lineWidth = 3 / scale;
            ctx.strokeRect(flippedX1, y1, flippedX2 - flippedX1, y2 - y1);

            ctx.fillStyle = `rgba(0,255,136,${conf})`;
            ctx.font = `${16 / scale}px Arial`;
            ctx.fillText(
              `Person ${(conf * 100).toFixed(0)}%`,
              flippedX1,
              y1 - 5 / scale
            );
          }

          // skeleton
          ctx.strokeStyle = 'rgba(0,212,255,0.8)';
          ctx.lineWidth = 3 / scale;
          ctx.beginPath();

          for (const [a, b] of skeleton) {
            if (
              kps[a] && kps[b] &&
              kps[a][2] > 0.3 && kps[b][2] > 0.3
            ) {
              ctx.moveTo(img.width - kps[a][0], kps[a][1]);
              ctx.lineTo(img.width - kps[b][0], kps[b][1]);
            }
          }

          ctx.stroke();
        }

        ctx.restore();
      }

      frameCount++;
      isRendering = false;

      if (pendingFrame) {
        requestAnimationFrame(renderFrame);
      }
    };

    img.src = 'data:image/jpeg;base64,' + data.frame;
  }

  // stats
  if (data.persons) {
    humanCount.textContent = data.persons.length;
  }
}

// ---------------- FPS ----------------
function updateFPS() {
  fpsValue.textContent = frameCount;
  fpsDisplay.textContent = `FPS: ${frameCount}`;
  frameCount = 0;
}

// ---------------- WEBSOCKET ----------------
function connect() {
  const wsHost = piIpAddress;
  const wsPort = '8000';

  ws = new WebSocket(`ws://${wsHost}:${wsPort}/ws`);

  ws.onopen = () => {
    connStatus.classList.add('connected');
    connText.textContent = 'Connected';
    fpsInterval = setInterval(updateFPS, 1000);
    loadLogs();
  };

  ws.onclose = () => {
    connStatus.classList.remove('connected');
    connText.textContent = 'Disconnected';

    if (fpsInterval) clearInterval(fpsInterval);

    setTimeout(connect, 2000);
  };

  ws.onerror = () => ws.close();

  ws.onmessage = ev => {
    try {
      const data = JSON.parse(ev.data);

      if (data.error) showError(data.error);
      else {
        hideError();
        drawFrame(data);
      }
    } catch {
      showError('Failed to parse server data');
    }
  };
}

// ---------------- CONTROLS ----------------
async function startDetection() {
  const res = await fetch(`${serverUrl}/start`, { method: 'POST' });
  const data = await res.json();

  if (data.is_running) {
    runStatus.classList.add('running');
    runText.textContent = 'Running';
    startBtn.disabled = true;
    stopBtn.disabled = false;
  }
}

async function stopDetection() {
  const res = await fetch(`${serverUrl}/stop`, { method: 'POST' });
  const data = await res.json();

  if (!data.is_running) {
    runStatus.classList.remove('running');
    runStatus.classList.add('stopped');
    runText.textContent = 'Stopped';

    startBtn.disabled = false;
    stopBtn.disabled = true;

    humanCount.textContent = '0';
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

connect();