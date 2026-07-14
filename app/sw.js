/* Anant Business SW v5 — network-first for app shell (instant deploys), cache fallback offline */
var V='anant-app-v6';
var SHELL=['/app/','/app/index.html','/app/invoice/','/app/invoice/index.html','/app/templates/','/app/templates/index.html',
 '/app/register/','/app/register/index.html','/app/customers/','/app/customers/index.html','/app/db.js','/app/manifest.webmanifest','/icon-192.png'];
self.addEventListener('install',function(e){e.waitUntil(caches.open(V).then(function(c){return c.addAll(SHELL);}).then(function(){return self.skipWaiting();}));});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==V;}).map(function(k){return caches.delete(k);}));}).then(function(){return self.clients.claim();}));});
self.addEventListener('fetch',function(e){
  var u=new URL(e.request.url);
  if(u.pathname.indexOf('api.php')>=0) return;                       // sync API: always network
  if(u.pathname.indexOf('/app/')!==0 && SHELL.indexOf(u.pathname)===-1) return; // never touch public site
  var isShell = e.request.mode==='navigate' || u.pathname.slice(-3)==='.js' || u.pathname.slice(-5)==='.html' || u.pathname.slice(-1)==='/';
  if(isShell){
    e.respondWith(fetch(e.request).then(function(res){ if(res&&res.ok){var cp=res.clone();caches.open(V).then(function(c){c.put(e.request,cp);});} return res; })
      .catch(function(){ return caches.match(e.request,{ignoreSearch:true}); }));
  } else {
    e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(function(hit){ return hit||fetch(e.request).then(function(res){ if(res&&res.ok){var cp=res.clone();caches.open(V).then(function(c){c.put(e.request,cp);});} return res; }); }));
  }
});