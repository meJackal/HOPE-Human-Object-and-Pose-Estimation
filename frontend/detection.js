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
let flashTimeout = null;

const reusableImg = new Image();
let isDecoding = false;

const piIpAddress = localStorage.getItem('piIpAddress') || window.location.hostname || 'localhost';
const serverUrl = piIpAddress === 'localhost' || piIpAddress === window.location.hostname
  ? ''
  : `http://${piIpAddress}:8000`;

console.log('Connecting to server:', piIpAddress);

function showError(message) {
  errorDisplay.textContent = message;
  errorDisplay.classList.add('show');
  console.error('Error:', message);
}

function hideError() {
  errorDisplay.classList.remove('show');
}

async function logDetection(count, persons) {
  try {
    await fetch(`${serverUrl}/log_detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        count: count,
        persons: persons.map(p => ({ confidence: p.bbox_conf }))
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
        const timeStr = date.toLocaleTimeString();
        const dateStr = date.toLocaleDateString();
        logsHTML += `
          <div class="log-item">
            <div class="log-time">${timeStr}</div>
            <div class="log-detail">${dateStr} - ${log.count} human${log.count !== 1 ? 's' : ''} detected</div>
          </div>
        `;
      });
      logsList.innerHTML = logsHTML;
    }
  } catch (e) {
    console.error('Failed to load logs:', e);
  }
}

const skeleton = [
  [0,1],[0,2],[1,3],[2,4],
  [0,5],[0,6],[5,6],
  [5,7],[7,9],[6,8],[8,10],
  [5,11],[6,12],[11,12],
  [11,13],[13,15],[12,14],[14,16]
];

function resizeCanvas() {
  const container = document.getElementById('canvas-container');
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function playDetectionSound() {
  const audio = new Audio('/static/alert.mp3');
  audio.volume = 1.0;
  audio.play().catch(e => console.warn('Audio error:', e));
}

function flashDetection() {
  const overlay = document.getElementById('flash-overlay');
  overlay.style.opacity = '1';
  setTimeout(() => {
    overlay.style.opacity = '0';
  }, 400);
}

function drawFrame(data) {
  if (isDecoding) return;

  isDecoding = true;
  reusableImg.onload = () => {
    renderFrame(data, reusableImg);
    isDecoding = false;
  };
  reusableImg.src = 'data:image/jpeg;base64,' + data.frame;
}

function renderFrame(data, img) {
  const scale = Math.min(canvas.width / img.width, canvas.height / img.height);
  const x = (canvas.width - img.width * scale) / 2;
  const y = (canvas.height - img.height * scale) / 2;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(img, canvas.width - x - img.width * scale, y, img.width * scale, img.height * scale);
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
        ctx.strokeStyle = `rgba(0, 255, 136, ${conf})`;
        ctx.lineWidth = 3 / scale;
        ctx.strokeRect(flippedX1, y1, flippedX2 - flippedX1, y2 - y1);
        ctx.fillStyle = `rgba(0, 255, 136, ${conf})`;
        ctx.font = `${16 / scale}px Arial`;
        ctx.fillText(`Person ${(conf * 100).toFixed(0)}%`, flippedX1, y1 - 5 / scale);
      }

      ctx.strokeStyle = 'rgba(0, 212, 255, 0.8)';
      ctx.lineWidth = 3 / scale;
      ctx.beginPath();
      for (const [a, b] of skeleton) {
        if (kps[a] && kps[b] &&
            kps[a][2] > 0.3 && kps[b][2] > 0.3 &&
            kps[a][0] > 1 && kps[a][1] > 1 &&
            kps[b][0] > 1 && kps[b][1] > 1) {
          ctx.moveTo(img.width - kps[a][0], kps[a][1]);
          ctx.lineTo(img.width - kps[b][0], kps[b][1]);
        }
      }
      ctx.stroke();

      for (const kp of kps) {
        if (kp[2] > 0.3 && kp[0] > 1 && kp[1] > 1) {
          ctx.fillStyle = `rgba(255, 200, 0, ${Math.min(kp[2] * 1.5, 1.0)})`;
          ctx.beginPath();
          ctx.arc(img.width - kp[0], kp[1], 6 / scale, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
    ctx.restore();
  }

  frameCount++;

  if (data.persons) {
    humanCount.textContent = data.persons.length;
    const now = Date.now();
    const currentCount = data.persons.length;

    if (currentCount > 0 && lastDetectionCount === 0) {
      playDetectionSound();
      flashDetection();
    } else if (currentCount !== lastDetectionCount && currentCount > 0) {
      flashDetection();
    }

    if (currentCount === stableDetectionCount) {
      stableCountFrames++;
    } else {
      stableDetectionCount = currentCount;
      stableCountFrames = 1;
    }

    let shouldLog = false;
    if (currentCount > 0) {
      if (stableCountFrames >= 3 && lastDetectionCount === 0) shouldLog = true;
      if (stableCountFrames >= 5 && Math.abs(currentCount - lastDetectionCount) > 1) shouldLog = true;
      if (now - lastLogTime > 30000) shouldLog = true;
    }

    if (shouldLog) {
      lastLogTime = now;
      logDetection(currentCount, data.persons);
    }
    lastDetectionCount = currentCount;

    if (data.persons.length > 0) {
      let listHTML = '';
      data.persons.forEach((person, idx) => {
        const conf = person.bbox_conf || 0;
        listHTML += `
          <div class="person-item">
            <span class="person-id">Person ${idx + 1}</span>
            <span class="person-conf">${(conf * 100).toFixed(1)}%</span>
          </div>
        `;
      });
      personsList.innerHTML = listHTML;
    } else {
      personsList.innerHTML = '<div class="empty-state">No detections</div>';
    }
  }
}

function updateFPS() {
  const fps = frameCount;
  fpsValue.textContent = fps;
  fpsDisplay.textContent = `FPS: ${fps}`;
  frameCount = 0;
}

function connect() {
  const wsHost = piIpAddress;
  const wsPort = '8000';
  const ws = new WebSocket(`ws://${wsHost}:${wsPort}/ws`);
  console.log('WebSocket connecting to:', `ws://${wsHost}:${wsPort}/ws`);

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

  ws.onerror = () => {
    ws.close();
  };

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.error) {
        showError(data.error);
      } else if (data.idle) {
        hideError();
      } else {
        hideError();
        drawFrame(data);
      }
    } catch (e) {
      console.error('Parse error:', e);
      showError('Failed to parse server data');
    }
  };
}

async function startDetection() {
  try {
    const res = await fetch(`${serverUrl}/start`, { method: 'POST' });
    const data = await res.json();
    if (data.is_running) {
      isRunning = true;
      runStatus.classList.add('running');
      runStatus.classList.remove('stopped');
      runText.textContent = 'Running';
      startBtn.disabled = true;
      stopBtn.disabled = false;
    }
  } catch (e) {
    console.error('Start failed:', e);
  }
}

async function stopDetection() {
  try {
    const res = await fetch(`${serverUrl}/stop`, { method: 'POST' });
    const data = await res.json();
    if (!data.is_running) {
      isRunning = false;
      runStatus.classList.remove('running');
      runStatus.classList.add('stopped');
      runText.textContent = 'Stopped';
      startBtn.disabled = false;
      stopBtn.disabled = true;
      humanCount.textContent = '0';
      personsList.innerHTML = '<div class="empty-state">No detections</div>';
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  } catch (e) {
    console.error('Stop failed:', e);
  }
}

connect();