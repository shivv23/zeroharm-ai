import { useEffect, useCallback } from 'react';
import ws from '../store/websocketStore';

const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY || null;

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map(ch => ch.charCodeAt(0)));
}

async function registerSW() {
  if (!('serviceWorker' in navigator)) return null;
  try {
    const reg = await navigator.serviceWorker.register('/service-worker.js', { scope: '/' });
    return reg;
  } catch (e) {
    console.error('SW registration failed:', e);
    return null;
  }
}

async function subscribeToPush(registration) {
  if (!registration || !('PushManager' in window)) return;
  try {
    const sub = await registration.pushManager.getSubscription();
    if (sub) return sub;
    if (!VAPID_PUBLIC_KEY) {
      console.warn('VAPID public key not configured — push subscriptions disabled');
      return null;
    }
    const applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
    const newSub = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey,
    });
    ws.send({ action: 'register_push', subscription: JSON.stringify(newSub) });
    return newSub;
  } catch (e) {
    console.error('Push subscription failed:', e);
    return null;
  }
}

async function requestNotificationPermission() {
  if (!('Notification' in window)) return 'denied';
  if (Notification.permission === 'granted') return 'granted';
  if (Notification.permission === 'denied') return 'denied';
  const result = await Notification.requestPermission();
  return result;
}

export default function PushNotificationManager({ onNavigate }) {
  const showNotification = useCallback((title, options = {}) => {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    try {
      const n = new Notification(title, {
        icon: '/icons/icon-192x192.png',
        badge: '/icons/icon-192x192.png',
        vibrate: [200, 100, 200],
        ...options,
      });
      n.onclick = () => {
        if (onNavigate && options.data?.tab) {
          onNavigate(options.data.tab);
        }
        window.focus();
        n.close();
      };
    } catch (e) {
      /* notification not available */
    }
  }, [onNavigate]);

  useEffect(() => {
    let reg = null;
    let handleSwMessage = null;

    async function init() {
      const permission = await requestNotificationPermission();
      if (permission !== 'granted') return;

      reg = await registerSW();
      await subscribeToPush(reg);

      if (reg) {
        handleSwMessage = (event) => {
          if (event.data?.type === 'navigate' && onNavigate) {
            onNavigate(event.data.tab);
          }
        };
        navigator.serviceWorker.addEventListener('message', handleSwMessage);
      }
    }

    init();

    const unsubAlert = ws.on('state_update', (d) => {
      const severity = d.risk?.severity || 'normal';
      const alertCount = d.risk?.alerts?.length || 0;

      if (severity === 'critical') {
        showNotification('CRITICAL: Compound Risk Condition', {
          body: 'Multiple hazard sources detected — immediate attention required.',
          tag: 'critical-risk',
          data: { tab: 'alerts' },
          requireInteraction: true,
        });
      }

      if (alertCount > 5) {
        showNotification(`${alertCount} Active Alerts`, {
          body: 'Review recommended — elevated alert levels detected.',
          tag: 'alert-count',
          data: { tab: 'alerts' },
        });
      }
    });

    const unsubEmergency = ws.on('emergency_triggered', (d) => {
      showNotification('EMERGENCY RESPONSE ACTIVATED', {
        body: `${d.data?.label || 'Emergency'} in ${d.data?.zone_name || 'Unknown Zone'}`,
        tag: 'emergency',
        data: { tab: 'emergency' },
        requireInteraction: true,
      });
    });

    return () => {
      unsubAlert();
      unsubEmergency();
      if (handleSwMessage) {
        navigator.serviceWorker.removeEventListener('message', handleSwMessage);
      }
    };
  }, [showNotification, onNavigate]);

  return null;
}
