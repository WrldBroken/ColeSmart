// Instalación del Service Worker
self.addEventListener('install', (event) => {
    console.log('ColeSmart: Service Worker instalado');
    self.skipWaiting();
});

// Activación
self.addEventListener('activate', (event) => {
    console.log('ColeSmart: Service Worker activo');
    event.waitUntil(self.clients.claim());
});

// Control de las solicitudes
self.addEventListener('fetch', (event) => {
    // Por ahora, las solicitudes siguen llegando al servidor.
});