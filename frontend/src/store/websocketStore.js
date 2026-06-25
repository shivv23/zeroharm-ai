const WS_URL = 'ws://localhost:8000/ws';
const API_BASE = 'http://localhost:8000/api';

class ZeroHarmWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.isConnected = false;
    this.reconnectTimer = null;
    this.plantState = null;
    this.riskData = null;
  }

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);
      this.ws.onopen = () => {
        this.isConnected = true;
        this.notify('connection', { connected: true });
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
        this.isConnected = false;
        this.notify('connection', { connected: false });
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };
      this.ws.onerror = () => {
        this.ws.close();
      };
    } catch (e) {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
  }

  send(data) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  notify(event, data) {
    this.listeners.get(event)?.forEach(cb => cb(data));
  }

  async fetchAPI(endpoint, options = {}) {
    try {
      const fetchOpts = { method: options.method || 'GET', headers: { 'Content-Type': 'application/json', ...options.headers } };
      if (options.body) fetchOpts.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
      const res = await fetch(`${API_BASE}${endpoint}`, fetchOpts);
      return await res.json();
    } catch (e) {
      console.error(`API fetch error: ${endpoint}`, e);
      return null;
    }
  }
}

const ws = new ZeroHarmWebSocket();
export default ws;
