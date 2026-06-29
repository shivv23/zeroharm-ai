import React from 'react';
import { COLORS } from '../store/theme';

const TOAST_STYLES = {
  critical: { bg: 'linear-gradient(135deg, rgba(255,23,68,0.95), rgba(213,0,0,0.9))', icon: '\u{1F525}', border: COLORS.riskCritical },
  warning: { bg: 'linear-gradient(135deg, rgba(255,160,0,0.9), rgba(255,109,0,0.85))', icon: '\u{26A0}\uFE0F', border: COLORS.riskElevated },
  success: { bg: 'linear-gradient(135deg, rgba(0,230,118,0.9), rgba(0,200,83,0.85))', icon: '\u{2705}', border: COLORS.riskNormal },
  info: { bg: 'linear-gradient(135deg, rgba(0,229,255,0.85), rgba(0,188,212,0.8))', icon: '\u{2139}\uFE0F', border: COLORS.accent },
};

export default function Toast({ toasts = [] }) {
  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', top: 12, right: 12, zIndex: 9999,
      display: 'flex', flexDirection: 'column', gap: 6,
      maxWidth: 360,
    }}>
      {toasts.map((toast) => {
        const style = TOAST_STYLES[toast.type] || TOAST_STYLES.info;
        return (
          <div key={toast.id} style={{
            background: style.bg,
            border: `1px solid ${style.border}`,
            borderRadius: 8, padding: '8px 14px',
            display: 'flex', alignItems: 'center', gap: 8,
            boxShadow: `0 4px 20px rgba(0,0,0,0.4), 0 0 10px ${style.border}33`,
            animation: 'slideIn 0.3s ease-out',
            color: '#fff', fontSize: 12, fontWeight: 500,
            backdropFilter: 'blur(8px)',
          }}>
            <span style={{ fontSize: 16 }}>{style.icon}</span>
            <span>{toast.message}</span>
          </div>
        );
      })}
    </div>
  );
}
