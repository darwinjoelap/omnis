"""
PWA: manifest, service worker, página sin conexión, visor de PDF e instrucciones de instalación (de Ordo).

Service worker (versión base, Fase 01):
- precarga estáticos y /offline/;
- estáticos: primero caché (llevan hash gracias a WhiteNoise);
- páginas: siempre red; sin conexión o si la red tarda más de ESPERA ms, muestra /offline/.
El modo offline de consulta (borradores, cola e idempotencia de Pediae) se agrega en la Fase 12.
No se guarda HTML de la app en caché: los datos son por tenant y por usuario.
"""
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_control, never_cache

PRECARGA = [
    'vendor/bootstrap/bootstrap.min.css',
    'vendor/bootstrap-icons/bootstrap-icons.min.css',
    'css/omnis.css',
    'vendor/bootstrap/bootstrap.bundle.min.js',
    'vendor/htmx/htmx.min.js',
    'js/pwa.js',
    'img/marca/omnis-simbolo.png',
    'img/marca/omnis-palabra.png',
    'img/marca/omnis-logo.png',
    'vendor/fuentes/inter-latin.woff2',
    'vendor/fuentes/outfit-latin.woff2',
    'img/marca/pwa/icon-192.png',
]

COLOR_TEMA = '#FFFFFF'   # barra del sistema clara, como la barra superior


@cache_control(max_age=3600, public=True)
def manifest(request):
    datos = {
        'id': '/',
        'name': 'Omnis — Consultas médicas',
        'short_name': 'Omnis',
        'description': 'Historia clínica, agenda, récipes y cobros para consultorios y clínicas.',
        'lang': 'es',
        'start_url': '/?origen=app',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'any',
        'background_color': '#FBF9F4',
        'theme_color': COLOR_TEMA,
        'icons': [
            {'src': static('img/marca/pwa/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'},
            {'src': static('img/marca/pwa/icon-512.png'), 'sizes': '512x512', 'type': 'image/png'},
            {'src': static('img/marca/pwa/icon-maskable-512.png'), 'sizes': '512x512', 'type': 'image/png',
             'purpose': 'maskable'},
        ],
        'shortcuts': [
            {'name': 'Pacientes', 'url': '/pacientes/',
             'icons': [{'src': static('img/marca/pwa/icon-192.png'), 'sizes': '192x192'}]},
        ],
    }
    return JsonResponse(datos, content_type='application/manifest+json', json_dumps_params={'ensure_ascii': False})


@never_cache
def service_worker(request):
    precarga = [static(r) for r in PRECARGA] + ['/offline/']
    js = (SW_JS.replace('__VERSION__', settings.OMNIS_VERSION).replace('__PRECARGA__', json.dumps(precarga))
          .replace('__STATIC__', settings.STATIC_URL))
    r = HttpResponse(js, content_type='application/javascript; charset=utf-8')
    r['Service-Worker-Allowed'] = '/'
    return r


@cache_control(max_age=86400, public=True)
def offline(request):
    return render(request, 'core/offline.html', {'titulo': 'Sin conexión'})


SW_JS = r"""// Omnis service worker · versión __VERSION__
const CACHE = 'omnis-__VERSION__';
const PRECARGA = __PRECARGA__;
const STATIC = '__STATIC__';
const ESPERA = 8000;   // ms que se espera una página antes de mostrar «sin conexión»

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECARGA)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(claves.filter((k) => k.startsWith('omnis-') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith(STATIC)) {
    e.respondWith(
      caches.match(req).then((r) => r || fetch(req).then((resp) => {
        if (resp.ok) { const copia = resp.clone(); caches.open(CACHE).then((c) => c.put(req, copia)); }
        return resp;
      }))
    );
    return;
  }

  if (req.mode === 'navigate') {
    const red = fetch(req);
    const limite = new Promise((ok) => setTimeout(() => ok(null), ESPERA));
    e.respondWith(
      Promise.race([red, limite]).then((resp) => resp || caches.match('/offline/'), () => caches.match('/offline/'))
    );
  }
});
"""


@login_required
def visor_pdf(request):
    """
    Muestra un PDF de la app DENTRO de la app (pdf.js). En la PWA instalada, abrir el PDF directo saca al usuario
    de la app (problema de constancias de Pediae en el móvil). Solo acepta rutas internas (?u=/recipes/5/pdf/).
    """
    u = request.GET.get('u', '')
    if not u.startswith('/') or u.startswith('//') or '\\' in u \
            or not url_has_allowed_host_and_scheme(u, allowed_hosts=None):
        raise Http404
    return render(request, 'core/visor_pdf.html', {'titulo': 'Documento', 'url_pdf': u})


def instalar(request):
    return render(request, 'core/instalar.html', {'titulo': 'Instalar Omnis'})
