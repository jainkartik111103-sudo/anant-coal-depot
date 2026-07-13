/* Anant Business service worker — offline shell, cache-first within /app/ */
var V = 'anant-app-v3';
var SHELL = ['/app/','/app/index.html','/app/invoice/','/app/invoice/index.html',
             '/app/templates/','/app/templates/index.html','/app/register/','/app/register/index.html','/app/customers/','/app/customers/index.html','/app/db.js','/app/manifest.webmanifest','/icon-192.png'];
self.addEventListener('install', function(e){
  e.waitUntil(caches.open(V).then(function(c){ return c.addAll(SHELL); }).then(function(){ return self.skipWaiting(); }));
});
self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.filter(function(k){ return k!==V; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener('fetch', function(e){
  var u = new URL(e.request.url);
  if (u.pathname.indexOf('/app/') !== 0 && SHELL.indexOf(u.pathname) === -1) return; // never intercept the public site
  e.respondWith(
    caches.match(e.request, {ignoreSearch:true}).then(function(hit){
      var net = fetch(e.request).then(function(res){
        if (res && res.ok) { var cp = res.clone(); caches.open(V).then(function(c){ c.put(e.request, cp); }); }
        return res;
      }).catch(function(){ return hit; });
      return hit || net;
    })
  );
});
