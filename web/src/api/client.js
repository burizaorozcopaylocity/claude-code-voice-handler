import axios from 'axios';

const API_BASE = '/api';

export const api = {
  // Daemon endpoints
  daemon: {
    getStatus: () => axios.get(`${API_BASE}/daemon/status`).then(r => r.data),
    start: () => axios.post(`${API_BASE}/daemon/start`).then(r => r.data),
    stop: () => axios.post(`${API_BASE}/daemon/stop`).then(r => r.data),
    restart: () => axios.post(`${API_BASE}/daemon/restart`).then(r => r.data),
  },

  // Queue endpoints
  queue: {
    getStatus: () => axios.get(`${API_BASE}/queue/status`).then(r => r.data),
    clear: () => axios.post(`${API_BASE}/queue/clear`).then(r => r.data),
  },

  // Config endpoints
  config: {
    get: () => axios.get(`${API_BASE}/config`).then(r => r.data),
    update: (voiceSettings) =>
      axios.put(`${API_BASE}/config`, { voice_settings: voiceSettings }).then(r => r.data),
  },

  // Hook endpoints
  hooks: {
    getAll: () => axios.get(`${API_BASE}/hooks`).then(r => r.data),
    toggle: (hookName, enabled) =>
      axios.post(`${API_BASE}/hooks/toggle`, { hook_name: hookName, enabled }).then(r => r.data),
  },

  // TTS endpoints
  tts: {
    test: (text, voice = 'nova') =>
      axios.post(`${API_BASE}/tts/test`, { text, voice }).then(r => r.data),
  },
};
