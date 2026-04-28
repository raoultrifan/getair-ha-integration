class GetAirSpeedScaleCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      entity: config.entity,
      min_speed: config.min_speed || 0.5,
      max_speed: config.max_speed || 4.0,
      step: config.step || 0.5,
      ...config,
    };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateScale();
  }

  get _fanState() {
    return this._hass?.states[this._config.entity];
  }

  get _currentSpeed() {
    if (!this._hass) return null;
    const speedSensor = this._config.speed_sensor;
    if (speedSensor) {
      const val = parseFloat(this._hass.states[speedSensor]?.state);
      return isNaN(val) ? null : val;
    }
    // fallback: derive from percentage
    const pct = parseFloat(this._fanState?.attributes?.percentage);
    if (isNaN(pct) || pct === 0) return 0;
    const min = this._config.min_speed;
    const max = this._config.max_speed;
    return Math.round((min + (pct / 100) * (max - min)) * 10) / 10;
  }

  _getSteps() {
    const steps = [];
    const { min_speed, max_speed, step } = this._config;
    for (let s = min_speed; s <= max_speed + 0.001; s = Math.round((s + step) * 10) / 10) {
      steps.push(Math.round(s * 10) / 10);
    }
    return steps;
  }

  _speedToPercent(speed) {
    const { min_speed, max_speed } = this._config;
    return ((speed - min_speed) / (max_speed - min_speed)) * 100;
  }

  render() {
    const steps = this._getSteps();

    this.shadowRoot.innerHTML = `
      <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

        :host { display: block; font-family: 'JetBrains Mono', monospace; }

        .card {
          background: #0e1117;
          border-radius: 16px;
          padding: 16px 20px 14px;
          position: relative;
          overflow: hidden;
        }

        .label-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          position: relative;
        }

        .label {
          font-size: 10px;
          color: #2d4f63;
          text-align: center;
          flex: 1;
          transition: color 0.3s ease;
          cursor: pointer;
          user-select: none;
          -webkit-tap-highlight-color: transparent;
          padding: 2px 0;
        }
        .label.active {
          color: #20b2dc;
          font-weight: 600;
        }
        .label.near {
          color: #4a7a96;
        }

        .track-wrap {
          position: relative;
          height: 24px;
          display: flex;
          align-items: center;
        }

        .track {
          position: absolute;
          left: 0;
          right: 0;
          height: 3px;
          background: rgba(255,255,255,0.06);
          border-radius: 2px;
        }

        .track-fill {
          position: absolute;
          left: 0;
          height: 3px;
          background: linear-gradient(90deg, #0d4f6e, #20b2dc);
          border-radius: 2px;
          transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .ticks {
          position: absolute;
          left: 0;
          right: 0;
          display: flex;
          justify-content: space-between;
        }

        .tick {
          width: 2px;
          height: 8px;
          background: rgba(255,255,255,0.08);
          border-radius: 1px;
          transition: background 0.3s ease, height 0.3s ease;
          flex: 1;
          display: flex;
          justify-content: center;
        }
        .tick-inner {
          width: 2px;
          height: 100%;
          background: rgba(255,255,255,0.08);
          border-radius: 1px;
          transition: background 0.3s ease, height 0.3s ease;
        }
        .tick.active .tick-inner {
          background: #20b2dc;
          height: 12px;
          margin-top: -2px;
        }
        .tick.past .tick-inner {
          background: rgba(32,178,220,0.3);
        }

        .thumb {
          position: absolute;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #20b2dc;
          box-shadow: 0 0 12px rgba(32,178,220,0.6);
          transform: translateX(-50%);
          transition: left 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                      box-shadow 0.3s ease;
          top: 50%;
          margin-top: -8px;
          z-index: 2;
        }
        .thumb.off {
          background: #2d4f63;
          box-shadow: none;
        }

        .speed-readout {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 10px;
        }
        .speed-label {
          font-size: 10px;
          color: #2d4f63;
          text-transform: uppercase;
          letter-spacing: 1.5px;
        }
        .speed-value {
          font-size: 13px;
          color: #20b2dc;
          font-weight: 600;
          letter-spacing: 0.5px;
          transition: color 0.3s ease;
        }
        .speed-value.off {
          color: #2d4f63;
        }
      </style>

      <div class="card">
        <div class="label-row" id="labels">
          ${steps.map(s => `<span class="label" data-speed="${s}">${s.toFixed(1)}</span>`).join('')}
        </div>
        <div class="track-wrap">
          <div class="track"></div>
          <div class="track-fill" id="track-fill"></div>
          <div class="ticks" id="ticks">
            ${steps.map(s => `<div class="tick" data-speed="${s}"><div class="tick-inner"></div></div>`).join('')}
          </div>
          <div class="thumb" id="thumb"></div>
        </div>
        <div class="speed-readout">
          <span class="speed-label">Fan Speed</span>
          <span class="speed-value" id="speed-value">—</span>
        </div>
      </div>
    `;

    this._attachListeners();
  }

  _attachListeners() {
    // Tap on labels to set speed
    this.shadowRoot.querySelectorAll('.label').forEach(label => {
      label.addEventListener('click', () => {
        const speed = parseFloat(label.dataset.speed);
        this._setSpeed(speed);
      });
    });
  }

  _setSpeed(speed) {
    if (!this._hass || !this._config.entity) return;
    const { min_speed, max_speed } = this._config;
    const pct = Math.round(((speed - min_speed) / (max_speed - min_speed)) * 100);
    this._hass.callService('fan', 'set_percentage', {
      entity_id: this._config.entity,
      percentage: pct,
    });
  }

  updateScale() {
    if (!this.shadowRoot.getElementById('thumb')) return;

    const speed = this._currentSpeed;
    const steps = this._getSteps();
    const { min_speed, max_speed } = this._config;
    const isOff = speed === 0 || speed === null;

    const fillPct = isOff ? 0 : this._speedToPercent(speed);

    // Track fill
    const fill = this.shadowRoot.getElementById('track-fill');
    if (fill) fill.style.width = `${fillPct}%`;

    // Thumb
    const thumb = this.shadowRoot.getElementById('thumb');
    if (thumb) {
      thumb.style.left = isOff ? '0%' : `${fillPct}%`;
      thumb.classList.toggle('off', isOff);
    }

    // Labels
    this.shadowRoot.querySelectorAll('.label').forEach(label => {
      const s = parseFloat(label.dataset.speed);
      const isActive = !isOff && Math.abs(s - speed) < 0.05;
      const isNear = !isOff && Math.abs(s - speed) < 0.6 && !isActive;
      label.classList.toggle('active', isActive);
      label.classList.toggle('near', isNear);
    });

    // Ticks
    this.shadowRoot.querySelectorAll('.tick').forEach(tick => {
      const s = parseFloat(tick.dataset.speed);
      const isActive = !isOff && Math.abs(s - speed) < 0.05;
      const isPast = !isOff && s <= speed;
      tick.classList.toggle('active', isActive);
      tick.classList.toggle('past', isPast && !isActive);
    });

    // Readout
    const readout = this.shadowRoot.getElementById('speed-value');
    if (readout) {
      readout.textContent = isOff ? 'Off' : `${speed.toFixed(1)}`;
      readout.classList.toggle('off', isOff);
    }
  }

  getCardSize() { return 1; }

  static getStubConfig() {
    return {
      entity: 'fan.getair_comfortcontrol_pro_bt_getair_fan',
      speed_sensor: 'sensor.getair_comfortcontrol_pro_bt_fan_speed',
      min_speed: 0.5,
      max_speed: 4.0,
      step: 0.5,
    };
  }
}

customElements.define('getair-speed-scale', GetAirSpeedScaleCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'getair-speed-scale',
  name: 'getAir Speed Scale',
  description: 'Horizontal speed scale with tick marks for getAir fan',
});
