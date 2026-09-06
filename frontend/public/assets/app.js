/* ==========================================================================
   MigPAL — Runtime compartido del frontend
   --------------------------------------------------------------------------
   Sin build step ni dependencias: nginx sirve `frontend/public/` tal cual.
   Todas las páginas usan este módulo en vez de repetir `fetch` y manejo de
   token, que era exactamente la duplicación que había entre registro.html y
   caso.html.

   Resuelve tres problemas reales del frontend anterior:

   1. `API_BASE` estaba hardcodeado a `http://localhost:8010` en cada
      archivo -- el producto no podía desplegarse fuera de la máquina de
      desarrollo. Ahora se resuelve en runtime (ver `resolveApiBase`).
   2. El token vivía en una variable en memoria: refrescar la pestaña
      cerraba la sesión. Ahora persiste en localStorage con control de
      expiración real leída del propio JWT.
   3. El texto del backend se interpolaba con `innerHTML` sin escapar
      (riesgo señalado por la auditoría independiente de Hito 4). Ahora
      existe `escapeHtml` y las páginas lo usan para todo dato dinámico.
   ========================================================================== */

window.MigPAL = (function () {
  'use strict';

  /* ---------------------------------------------------------------- config */

  function resolveApiBase() {
    // 1) Override explícito (assets/config.js, generado por despliegue).
    if (window.MIGPAL_API_BASE) return String(window.MIGPAL_API_BASE).replace(/\/$/, '');

    // 2) Desarrollo local: el backend expone 8010 en el host (docker-compose).
    var host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host === '') {
      return 'http://localhost:8010';
    }

    // 3) Producción: mismo origen, el reverse proxy enruta al backend
    //    (ver deploy/nginx.conf).
    return window.location.origin;
  }

  var API_BASE = resolveApiBase();

  /* --------------------------------------------------------------- session */

  var TOKEN_KEY = 'migpal.token';
  var USER_KEY = 'migpal.username';

  function decodeJwtExp(token) {
    try {
      var payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
      return typeof payload.exp === 'number' ? payload.exp * 1000 : null;
    } catch (e) {
      return null;
    }
  }

  var session = {
    get token() {
      var t = null;
      try { t = localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
      if (!t) return null;
      var exp = decodeJwtExp(t);
      if (exp && Date.now() >= exp) { session.clear(); return null; }
      return t;
    },
    get username() {
      try { return localStorage.getItem(USER_KEY); } catch (e) { return null; }
    },
    save: function (token, username) {
      try {
        localStorage.setItem(TOKEN_KEY, token);
        if (username) localStorage.setItem(USER_KEY, username);
      } catch (e) { /* navegación privada: la sesión dura lo que la pestaña */ }
    },
    clear: function () {
      try {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      } catch (e) { /* noop */ }
    },
    get isAuthenticated() { return !!session.token; },
    /** Redirige al login si no hay sesión. Devuelve true si hay sesión. */
    requireAuth: function (redirectTo) {
      if (session.isAuthenticated) return true;
      var next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.replace((redirectTo || '/login.html') + '?next=' + next);
      return false;
    },
    logout: function () {
      session.clear();
      window.location.href = '/';
    }
  };

  /* ------------------------------------------------------------------- api */

  /** Error de API con el status HTTP y el detalle del backend ya extraído. */
  function ApiError(status, detail) {
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.message = detail || ('Error ' + status);
  }
  ApiError.prototype = Object.create(Error.prototype);

  function extractDetail(body, status) {
    if (!body) return 'Error ' + status;
    if (typeof body.detail === 'string') return body.detail;
    // FastAPI devuelve una lista de errores para fallos de validación.
    if (Array.isArray(body.detail)) {
      return body.detail.map(function (d) { return d.msg || JSON.stringify(d); }).join(' · ');
    }
    if (typeof body.message === 'string') return body.message;
    return 'Error ' + status;
  }

  async function request(path, options) {
    options = options || {};
    var headers = Object.assign({}, options.headers || {});
    var token = session.token;
    if (token && options.auth !== false) headers['Authorization'] = 'Bearer ' + token;

    var init = { method: options.method || 'GET', headers: headers };

    if (options.json !== undefined) {
      headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(options.json);
    } else if (options.form !== undefined) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
      init.body = new URLSearchParams(options.form).toString();
    }

    var res;
    try {
      res = await fetch(API_BASE + path, init);
    } catch (e) {
      throw new ApiError(0, window.MigPALi18n ? window.MigPALi18n.t('toast.noNetwork')
        : 'No se pudo contactar al servidor.');
    }

    // Sesión vencida o inválida: limpiar y mandar al login, salvo que la
    // llamada sea justamente el login.
    if (res.status === 401 && options.auth !== false) {
      session.clear();
      if (!options.silent401) {
        var next = encodeURIComponent(window.location.pathname);
        window.location.replace('/login.html?expired=1&next=' + next);
      }
      throw new ApiError(401, window.MigPALi18n ? window.MigPALi18n.t('toast.sessionExpired')
        : 'Tu sesión expiró.');
    }

    var body = null;
    if (res.status !== 204) {
      try { body = await res.json(); } catch (e) { body = null; }
    }

    if (!res.ok) throw new ApiError(res.status, extractDetail(body, res.status));
    return body;
  }

  var api = {
    base: API_BASE,
    request: request,
    get:  function (p, o) { return request(p, Object.assign({ method: 'GET' }, o)); },
    post: function (p, o) { return request(p, Object.assign({ method: 'POST' }, o)); },

    /* — Endpoints del producto — */
    login: async function (username, password) {
      var data = await request('/api/v1/auth/token', {
        method: 'POST',
        auth: false,
        form: { username: username, password: password }
      });
      session.save(data.access_token, username);
      return data;
    },
    register: function (email, username, password) {
      return request('/v1/auth/register', {
        method: 'POST', auth: false,
        json: { email: email, username: username, password: password }
      });
    },
    openCase:          function () { return api.post('/v1/case'); },
    sendMessage:       function (message) { return api.post('/v1/messages', { json: { message: message } }); },
    createAssessment:  function (profileText) { return api.post('/v1/assessment', { json: { profile_text: profileText } }); },
    getAssessment:     function () { return api.get('/v1/assessment'); },
    createRecommendation: function () { return api.post('/v1/recommendation'); },
    getRecommendation:    function () { return api.get('/v1/recommendation'); },
    acceptRecommendation:  function (id) { return api.post('/v1/recommendation/' + encodeURIComponent(id) + '/accept'); },
    discardRecommendation: function (id) { return api.post('/v1/recommendation/' + encodeURIComponent(id) + '/discard'); },
    selectRoute: function (id, alternativeIndex) {
      return api.post('/v1/recommendation/' + encodeURIComponent(id) + '/select-route', {
        json: { alternative_index: alternativeIndex }
      });
    },
    createPlan:   function () { return api.post('/v1/execution-plan'); },
    getPlan:      function () { return api.get('/v1/execution-plan'); },
    completeStep: function (stepId) {
      return api.post('/v1/execution-plan/steps/' + encodeURIComponent(stepId) + '/complete');
    }
  };

  /* ----------------------------------------------------------------- toast */

  function toastHost() {
    var host = document.querySelector('.toast-host');
    if (!host) {
      host = document.createElement('div');
      host.className = 'toast-host';
      host.setAttribute('role', 'status');
      host.setAttribute('aria-live', 'polite');
      document.body.appendChild(host);
    }
    return host;
  }

  function toast(message, kind, ms) {
    var marks = { success: '✅', error: '⚠️', info: 'ℹ️' };
    kind = kind || 'info';
    var el = document.createElement('div');
    el.className = 'toast toast-' + kind;
    var mark = document.createElement('span');
    mark.className = 'toast-mark';
    mark.textContent = marks[kind] || marks.info;
    var text = document.createElement('div');
    text.textContent = message;           // textContent: nunca innerHTML
    el.appendChild(mark);
    el.appendChild(text);
    toastHost().appendChild(el);

    setTimeout(function () {
      el.classList.add('is-out');
      setTimeout(function () { el.remove(); }, 260);
    }, ms || (kind === 'error' ? 6000 : 3800));
    return el;
  }

  /* -------------------------------------------------------------------- ui */

  /** Escapa texto para interpolarlo con innerHTML sin abrir un XSS.
      Necesario porque los títulos/descripciones vienen del backend y, en
      cuanto un hito futuro los haga generar por IA o editables por el
      usuario, el riesgo pasa a ser real (auditoría de Hito 4). */
  function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Pone un botón en estado "trabajando" y devuelve la función para
      restaurarlo — evita el doble submit y da feedback real. */
  function busy(btn, labelWhileBusy) {
    if (!btn) return function () {};
    var original = btn.innerHTML;
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '<span class="spinner"></span>' +
      (labelWhileBusy ? '<span>' + escapeHtml(labelWhileBusy) + '</span>' : '');
    return function restore() {
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
      btn.innerHTML = original;
    };
  }

  /* ----------------------------------------------------------------- theme */

  var THEME_KEY = 'migpal.theme';
  var theme = {
    get current() {
      try { return localStorage.getItem(THEME_KEY) || 'system'; } catch (e) { return 'system'; }
    },
    apply: function (value) {
      if (value === 'system') document.documentElement.removeAttribute('data-theme');
      else document.documentElement.setAttribute('data-theme', value);
      try { localStorage.setItem(THEME_KEY, value); } catch (e) { /* noop */ }
    },
    toggle: function () {
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
        (theme.current === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      theme.apply(isDark ? 'light' : 'dark');
      return !isDark;
    },
    init: function () {
      var saved = theme.current;
      if (saved !== 'system') document.documentElement.setAttribute('data-theme', saved);
    }
  };

  theme.init();

  /* -------------------------------------------------------------- exports */

  /** Atajo a i18n. Se resuelve en cada llamada (no se captura) para que
      cambiar de idioma actualice tambien los textos que genera el JS. */
  function t(key, vars) {
    return window.MigPALi18n ? window.MigPALi18n.t(key, vars) : key;
  }

  return {
    api: api,
    session: session,
    toast: toast,
    escapeHtml: escapeHtml,
    busy: busy,
    theme: theme,
    t: t,
    get lang() { return window.MigPALi18n ? window.MigPALi18n.lang : 'es'; },
    ApiError: ApiError
  };
})();
