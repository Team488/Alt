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


    function createStatusBox(status) {
      const box = createElement('div', 'status-box');
      box.dataset.activeTab = 'logs'; // default to logs

      const header = createElement('div', 'status-header');
      const nameDiv = createElement('div', 'status-name', status.name);
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

          // Set up the circular buffer with a max size of 800 lines
          const maxLineSize = 800;
          let logBuffer = [];

          // Function to add a new log entry and maintain the buffer size
          function addLogLine(newLine) {
              // Add the new line to the buffer
              logBuffer.push(newLine);

              // If the buffer exceeds maxLineSize, remove the oldest line
              if (logBuffer.length > maxLineSize) {
                  logBuffer.shift();
              }

              // Update the logBox content with the current buffer
              logBox.innerText = logBuffer.join("\n");
              logBox.scrollTop = logBox.scrollHeight; // Auto-scroll to bottom
          }

          // Connect to SSE stream
          const eventSource = new EventSource(status.logIp);
          eventSource.onmessage = (event) => {

              addLogLine(event.data);
          };

          eventSource.onopen = () => {
              logBox.innerText = "";
          }

          eventSource.onerror = () => {
              logBox.innerText = "\n[Error connecting to log stream]";
              eventSource.close();
          };
        }


      const errorsTab = createElement('div', 'inner-tab', 'Errors');
      errorsTab.dataset.tab = 'errors';
      innerTabs.appendChild(errorsTab);

      let streamContent = null;

      if (status.streamIp) {
        // Create the camera tab
        const cameraTab = createElement('div', 'inner-tab', 'Camera');
        cameraTab.dataset.tab = 'stream';
        innerTabs.appendChild(cameraTab);

        // Create the content area for the video stream
        streamContent = createElement('div', 'inner-content stream-content');
        streamContent.dataset.tab = 'stream';

        const img = createElement('img', 'camera-stream');

        document.addEventListener('visibilitychange', () => {
          if (!img) return;
          const isCameraTabVisible = streamContent?.classList.contains('active');
          if (document.hidden || !isCameraTabVisible) {
            img.src = "";
          } else {
            img.src = status.streamIp;
          }
        });



        img.dataset.lastIp = status.streamIp;
        streamContent.appendChild(img);
      }






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

      innerTabs.addEventListener('click', function(event) {
      const target = event.target;
      if (target.classList.contains('inner-tab')) {
        const tabId = target.dataset.tab;

        // Remove active class from all tabs and contents
        innerTabs.querySelectorAll('.inner-tab').forEach(t => t.classList.remove('active'));
        tabbedSection.querySelectorAll('.inner-content').forEach(content => {
          content.classList.remove('active');
        });

        // Set active tab and content
        target.classList.add('active');
        const activeContent = tabbedSection.querySelector(`.inner-content[data-tab="${tabId}"]`);
        if (activeContent) activeContent.classList.add('active');

        box.dataset.activeTab = tabId;

        // If it's the stream tab, set img.src, otherwise clear it
        if (tabId === 'stream' && boxObj.streamImg) {
          boxObj.streamImg.src = boxObj.streamImg.dataset.lastIp;
        } else if (boxObj.streamImg) {
          boxObj.streamImg.src = '';
        }
      }
      });


      const boxObj = { container: box, indicator, statusText, description, errorsBox, streamImg: streamContent?.querySelector('img'), timerCreate, timerPeriodic, timerShutdown, timerClose };
      updateStatusBox(boxObj, status);
      return boxObj;
    }

    // Update function: only patches the parts that change.
      function updateStatusBox(boxObj, status) {
        // Update indicator if status changed
        const isActive = status.active.toLowerCase() === 'active';
        const newClass = 'status-indicator ' + (isActive ? 'status-active' : 'status-inactive');
        if (boxObj.indicator.className !== newClass) {
          boxObj.indicator.className = newClass;
        }

        // Update status text if changed
        if (boxObj.statusText.textContent !== status.status) {
          boxObj.statusText.textContent = status.status;
        }

        // Update description if changed
        if (boxObj.description.textContent !== status.description) {
          boxObj.description.textContent = status.description;
        }

        // Update errors if changed
        if (boxObj.errorsBox.textContent !== status.errors) {
          boxObj.errorsBox.textContent = status.errors || 'None';
        }

        // PROBLEM !

        // Update camera stream only if IP changed
        // if (boxObj.streamImg && boxObj.streamImg.dataset.lastIp !== status.streamIp) {
        //   boxObj.streamImg.src = status.streamIp;
        //   boxObj.streamImg.dataset.lastIp = status.streamIp;
        // }

        // Update timers only if changed
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
        if (!groupContainers.has(group)) {
          const container = document.createElement('div');
          container.className = 'tab-content';
          groupContainers.set(group, container);
          document.getElementById('status-container').appendChild(container);

          // Create a tab for this group
          const tab = createElement('div', 'tab', group);
          tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            container.classList.add('active');
            activeTab = group;
          });
          document.getElementById('tab-bar').appendChild(tab);

          // Activate first tab
          if (!activeTab) {
            tab.click();
          }
        }

        const key = status.name;
        if (!statusBoxes.has(key)) {
          const boxObj = createStatusBox(status);
          groupContainers.get(group).appendChild(boxObj.container);
          statusBoxes.set(key, boxObj);
        }
         else {
          const boxObj = statusBoxes.get(key);
          updateStatusBox(boxObj, status);
        }
      });
    });
