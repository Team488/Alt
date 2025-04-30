const socket = io(window.location.origin, { transports: ['websocket'], upgrade: false });

const statusBoxes = new Map();
const groupContainers = new Map();
let activeTab = null;

function createElement(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}

function createStatusBox(status, key) {
  const box = createElement('div', 'status-box');
  box.dataset.activeTab = 'logs'; // default to logs

  const header = createElement('div', 'status-header');
  const nameDiv = createElement('div', 'status-name', `${status.group} - ${status.name}`);
  const indicator = createElement('span', 'status-indicator');
  const statusText = createElement('div', 'status-text', status.status);
  header.append(indicator, nameDiv, statusText);

  const description = createElement('div', 'description', status.description);

  const tabbedSection = createElement('div', 'tabbed-section');
  const innerTabs = createElement('div', 'inner-tabs');

  let logContent = null;

  if (status.logIp) {
    const logTab = createElement('div', 'inner-tab active', 'Logs');
    logTab.dataset.tab = 'logs';
    innerTabs.appendChild(logTab);

    logContent = createElement('div', 'inner-content logs-content active');
    logContent.dataset.tab = 'logs';
    const logBox = createElement('div', 'errors-box');
    logBox.textContent = 'Connecting...';
    logContent.appendChild(logBox);

    const maxLineSize = 800;
    let logBuffer = [];

    function addLogLine(newLine) {
      logBuffer.push(newLine);
      if (logBuffer.length > maxLineSize) logBuffer.shift();
      logBox.innerText = logBuffer.join("\n");
      logBox.scrollTop = logBox.scrollHeight;
    }

    const eventSource = new EventSource(status.logIp);
    eventSource.onmessage = (event) => addLogLine(event.data);
    eventSource.onopen = () => logBox.innerText = "";
    eventSource.onerror = () => {
      logBox.innerText = "\n[Error connecting to log stream]";
      eventSource.close();
    };
  }

  const errorsTab = createElement('div', 'inner-tab', 'Errors');
  errorsTab.dataset.tab = 'errors';
  innerTabs.appendChild(errorsTab);

  let streamContent = null;

  status.streamPaths.forEach(pathList => {
    streamName = pathList[0];
    streamPath = pathList[1];
    const cameraTab = createElement('div', 'inner-tab', streamName);
    cameraTab.dataset.tab = 'stream';
    innerTabs.appendChild(cameraTab);

    streamContent = createElement('div', 'inner-content stream-content');
    streamContent.dataset.tab = 'stream';
    const img = createElement('img', 'camera-stream');
    img.dataset.lastIp = streamPath;
    streamContent.appendChild(img);

    document.addEventListener('visibilitychange', () => {
      if (!img) return;
      const visible = streamContent?.classList.contains('active');
      img.src = document.hidden || !visible ? "" : img.dataset.lastIp;
    });
  });

  const errorsContent = createElement('div', 'inner-content errors-content');
  errorsContent.dataset.tab = 'errors';
  const errorsBox = createElement('div', 'errors-box', status.errors || 'None');
  errorsContent.appendChild(errorsBox);

  tabbedSection.append(innerTabs);
  if (streamContent) tabbedSection.appendChild(streamContent);
  tabbedSection.appendChild(errorsContent);
  if (logContent) tabbedSection.appendChild(logContent);

  const timers = createElement('div', 'timers');
  const timerCreate = createElement('span', 'timer');
  const timerPeriodic = createElement('span', 'timer');
  const timerShutdown = createElement('span', 'timer');
  const timerClose = createElement('span', 'timer');
  timers.append(timerCreate, timerPeriodic, timerShutdown, timerClose);

  box.append(header, description, tabbedSection, timers);

  const boxObj = {
    container: box,
    indicator,
    statusText,
    description,
    errorsBox,
    streamImg: streamContent?.querySelector('img'),
    timerCreate,
    timerPeriodic,
    timerShutdown,
    timerClose
  };

  innerTabs.addEventListener('click', function(event) {
    const target = event.target;
    if (target.classList.contains('inner-tab')) {
      const tabId = target.dataset.tab;
      innerTabs.querySelectorAll('.inner-tab').forEach(t => t.classList.remove('active'));
      tabbedSection.querySelectorAll('.inner-content').forEach(c => c.classList.remove('active'));
      target.classList.add('active');
      const activeContent = tabbedSection.querySelector(`.inner-content[data-tab="${tabId}"]`);
      if (activeContent) activeContent.classList.add('active');
      box.dataset.activeTab = tabId;
      if (tabId === 'stream' && boxObj.streamImg) {
        boxObj.streamImg.src = boxObj.streamImg.dataset.lastIp;
      } else if (boxObj.streamImg) {
        boxObj.streamImg.src = '';
      }
    }
  });

  updateStatusBox(boxObj, status);
  return boxObj;
}

function updateStatusBox(boxObj, status) {
  const isActive = status.active.toLowerCase() === 'active';
  const newClass = 'status-indicator ' + (isActive ? 'status-active' : 'status-inactive');
  if (boxObj.indicator.className !== newClass) {
    boxObj.indicator.className = newClass;
  }

  if (boxObj.statusText.textContent !== status.status) {
    boxObj.statusText.textContent = status.status;
  }

  if (boxObj.description.textContent !== status.description) {
    boxObj.description.textContent = status.description;
  }

  if (boxObj.errorsBox.textContent !== (status.errors || 'None')) {
    boxObj.errorsBox.textContent = status.errors || 'None';
  }

  const format = val => (val !== undefined && val >= 0) ? val.toFixed(2) : 'N/A';
  const timerValues = {
    timerCreate: `create: ${format(status.create)}`,
    timerPeriodic: `runPeriodic: ${format(status.runPeriodic)}`,
    timerShutdown: `shutdown: ${format(status.shutdown)}`,
    timerClose: `close: ${format(status.close)}`
  };

  for (const [key, val] of Object.entries(timerValues)) {
    if (boxObj[key].textContent !== val) {
      boxObj[key].textContent = val;
    }
  }
}

socket.on('status_update', data => {
  data.forEach(status => {
    const group = status.group || 'default';
    const uniqueKey = `${group}:${status.name}`; // Ensure uniqueness across groups

    if (!groupContainers.has(group)) {
      const container = document.createElement('div');
      container.className = 'tab-content';
      groupContainers.set(group, container);
      document.getElementById('status-container').appendChild(container);

      const tab = createElement('div', 'tab', group);
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        container.classList.add('active');
        activeTab = group;
      });
      document.getElementById('tab-bar').appendChild(tab);

      if (!activeTab) tab.click();
    }

    if (!statusBoxes.has(uniqueKey)) {
      const boxObj = createStatusBox(status, uniqueKey);
      groupContainers.get(group).appendChild(boxObj.container);
      statusBoxes.set(uniqueKey, boxObj);
    } else {
      const boxObj = statusBoxes.get(uniqueKey);
      updateStatusBox(boxObj, status);
    }
  });
});
