import { WS_URL, API_BASE } from './apiRoutes';

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;
const RECONNECT_MAX_RETRIES = 20;

class ZeroHarmWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.isConnected = false;
    this.reconnectTimer = null;
    this.plantState = null;
    this.riskData = null;
    this._reconnectAttempts = 0;
    this._intentionalDisconnect = false;
    this._sendQueue = [];
  }

  connect() {
    this._intentionalDisconnect = false;
    this._reconnectAttempts = 0;
    try {
      this.ws = new WebSocket(WS_URL);
      this.ws.onopen = () => {
        this.isConnected = true;
        this._reconnectAttempts = 0;
        this._flushQueue();
        this.notify('connection', { connected: true });
        this.send({ action: 'sync_state' });
      };
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'state_update') {
            this.plantState = data.plant;
            this.riskData = data.risk;
          }
          this.notify(data.type, data);
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };
      this.ws.onclose = () => {
        if (this.isConnected) {
          this.isConnected = false;
          this.notify('connection', { connected: false });
        }
        if (!this._intentionalDisconnect) {
          this._scheduleReconnect();
        }
      };
      this.ws.onerror = () => {};
    } catch (e) {
      if (!this._intentionalDisconnect) {
        this._scheduleReconnect();
      }
    }
  }

  _scheduleReconnect() {
    if (this._reconnectAttempts >= RECONNECT_MAX_RETRIES) {
      console.warn('WebSocket max reconnection attempts reached');
      return;
    }
    this._reconnectAttempts += 1;
    const delay = Math.min(
      RECONNECT_BASE_MS * Math.pow(2, this._reconnectAttempts - 1) + Math.random() * 1000,
      RECONNECT_MAX_MS
    );
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  disconnect() {
    this._intentionalDisconnect = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
    this._reconnectAttempts = RECONNECT_MAX_RETRIES;
  }

  send(data) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    this._sendQueue.push(data);
    return false;
  }

  _flushQueue() {
    while (this._sendQueue.length > 0) {
      const msg = this._sendQueue.shift();
      if (this.ws && this.isConnected) {
        this.ws.send(JSON.stringify(msg));
      }
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => {
      const s = this.listeners.get(event);
      if (s) {
        s.delete(callback);
        if (s.size === 0) this.listeners.delete(event);
      }
    };
  }

  notify(event, data) {
    const cbs = this.listeners.get(event);
    if (cbs) {
      cbs.forEach(cb => {
        try { cb(data); } catch (e) { console.error('WS listener error:', e); }
      });
    }
  }

  async fetchAPI(endpoint, options = {}) {
    try {
      const fetchOpts = { method: options.method || 'GET', headers: { 'Content-Type': 'application/json', ...options.headers } };
      if (options.body) fetchOpts.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
      const res = await fetch(`${API_BASE}${endpoint}`, fetchOpts);
      if (!res.ok) {
        const errMsg = `API error ${res.status}: ${endpoint}`;
        console.error(errMsg);
        this.notify('api_error', { endpoint, status: res.status });
        return null;
      }
      return await res.json();
    } catch (e) {
      console.error(`API fetch error: ${endpoint}`, e);
      this.notify('api_error', { endpoint, error: e.message });
      return null;
    }
  }
}

const ws = new ZeroHarmWebSocket();
export default ws;
