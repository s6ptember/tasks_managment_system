// PWA Registration and Management
// Filename: pwa-register.js

(function() {
  'use strict';

  // Проверка поддержки Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      registerServiceWorker();
      checkForUpdates();
      setupInstallPrompt();
      setupPushNotifications();
    });
  }

  // Регистрация Service Worker
  function registerServiceWorker() {
    navigator.serviceWorker
      .register('/static/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('[PWA] Service Worker registered:', registration.scope);

        // Проверка обновлений каждые 60 минут
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);

        // Обработка обновлений Service Worker
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              showUpdateNotification();
            }
          });
        });
      })
      .catch((error) => {
        console.error('[PWA] Service Worker registration failed:', error);
      });
  }

  // Показать уведомление об обновлении
  function showUpdateNotification() {
    if (confirm('Доступна новая версия приложения. Обновить?')) {
      window.location.reload();
    }
  }

  // Проверка обновлений
  function checkForUpdates() {
    navigator.serviceWorker.ready.then((registration) => {
      registration.update();
    });
  }

  // Настройка промпта установки PWA
  let deferredPrompt;

  function setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      // Предотвращаем автоматический показ
      e.preventDefault();
      deferredPrompt = e;

      // Показываем кнопку установки
      showInstallButton();
    });

    // Обработка успешной установки
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] App installed successfully');
      deferredPrompt = null;
      hideInstallButton();

      // Можно показать уведомление пользователю
      if (window.Alpine && window.Alpine.store) {
        // Используем Alpine.js для показа toast
        window.dispatchEvent(new CustomEvent('show-toast', {
          detail: {
            message: 'Приложение успешно установлено!',
            type: 'success'
          }
        }));
      }
    });
  }

  // Показать кнопку установки
  function showInstallButton() {
    // Создаем кнопку установки если её нет
    let installBtn = document.getElementById('pwa-install-btn');

    if (!installBtn) {
      installBtn = document.createElement('button');
      installBtn.id = 'pwa-install-btn';
      installBtn.innerHTML = `
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
        </svg>
        Установить приложение
      `;
      installBtn.className = 'fixed bottom-4 right-4 z-50 px-6 py-3 bg-purple-600 text-white font-semibold rounded-2xl shadow-lg hover:bg-purple-700 transition-all flex items-center gap-2';

      installBtn.addEventListener('click', handleInstallClick);
      document.body.appendChild(installBtn);
    }

    installBtn.style.display = 'flex';
  }

  // Скрыть кнопку установки
  function hideInstallButton() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'none';
    }
  }

  // Обработка клика на кнопку установки
  async function handleInstallClick() {
    if (!deferredPrompt) {
      return;
    }

    // Показываем промпт
    deferredPrompt.prompt();

    // Ждем выбора пользователя
    const { outcome } = await deferredPrompt.userChoice;

    console.log(`[PWA] User response: ${outcome}`);

    // Очищаем отложенный промпт
    deferredPrompt = null;
    hideInstallButton();
  }

  // Настройка Push уведомлений
  function setupPushNotifications() {
    if (!('PushManager' in window)) {
      console.log('[PWA] Push notifications not supported');
      return;
    }

    // Проверяем текущее разрешение
    if (Notification.permission === 'granted') {
      console.log('[PWA] Push notifications already enabled');
      subscribeToPush();
    }
  }

  // Подписка на Push уведомления
  function subscribeToPush() {
    navigator.serviceWorker.ready.then((registration) => {
      registration.pushManager.getSubscription()
        .then((subscription) => {
          if (subscription) {
            console.log('[PWA] Already subscribed to push');
            return;
          }

          // Здесь можно добавить логику подписки
          // const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY';
          // subscription = registration.pushManager.subscribe({...});
        });
    });
  }

  // Запрос разрешения на уведомления
  window.requestNotificationPermission = async function() {
    if (!('Notification' in window)) {
      console.log('[PWA] Notifications not supported');
      return false;
    }

    const permission = await Notification.requestPermission();

    if (permission === 'granted') {
      console.log('[PWA] Notification permission granted');
      subscribeToPush();
      return true;
    }

    return false;
  };

  // Утилита для определения режима standalone (установленное PWA)
  window.isStandalonePWA = function() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  };

  // Событие изменения статуса сети
  window.addEventListener('online', () => {
    console.log('[PWA] Back online');

    // Синхронизируем данные если есть Service Worker
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      navigator.serviceWorker.ready.then((registration) => {
        return registration.sync.register('sync-tasks');
      });
    }
  });

  window.addEventListener('offline', () => {
    console.log('[PWA] Gone offline');

    // Можно показать уведомление пользователю
    if (window.Alpine) {
      window.dispatchEvent(new CustomEvent('show-toast', {
        detail: {
          message: 'Нет подключения к интернету. Работаем в офлайн режиме.',
          type: 'warning'
        }
      }));
    }
  });

  // API для очистки кэша (для отладки)
  window.clearPWACache = function() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.controller.postMessage({
        type: 'CLEAR_CACHE'
      });

      console.log('[PWA] Cache cleared');
      return true;
    }
    return false;
  };

  // Экспортируем полезные функции
  window.PWA = {
    isStandalone: window.isStandalonePWA,
    requestNotifications: window.requestNotificationPermission,
    clearCache: window.clearPWACache,
    showInstallPrompt: function() {
      if (deferredPrompt) {
        handleInstallClick();
        return true;
      }
      return false;
    }
  };

})();
