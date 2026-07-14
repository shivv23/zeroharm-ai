const origFetch = window.fetch.bind(window);
window.fetch = function (input, init = {}) {
  const url = typeof input === 'string' ? input : input instanceof Request ? input.url : input;
  if (url.includes('/api/')) {
    const token = (() => { try { return localStorage.getItem('zeroharm_token') || ''; } catch { return ''; } })();
    if (!init.headers) init.headers = {};
    if (Array.isArray(init.headers)) {
      init.headers.push(['Authorization', `Bearer ${token}`]);
    } else if (init.headers instanceof Headers) {
      if (!init.headers.has('Authorization')) init.headers.set('Authorization', `Bearer ${token}`);
    } else {
      init.headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return origFetch(input, init);
};
