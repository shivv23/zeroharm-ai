import React, { useRef, useEffect, useMemo } from 'react';

function gaussian(x, y, cx, cy, sigmaX, sigmaY) {
  const dx = x - cx, dy = y - cy;
  return Math.exp(-0.5 * (dx * dx / (sigmaX * sigmaX) + dy * dy / (sigmaY * sigmaY)));
}

export default function GasDispersionOverlay({ emergency, zoneRisks, plantState }) {
  const canvasRef = useRef(null);
  const isActive = emergency && ['gas_leak', 'explosion'].includes(emergency.type);

  const params = useMemo(() => {
    if (!isActive) return null;
    const leakRate = emergency.context?.leak_rate || 50;
    const windDir = emergency.context?.wind_direction || 90;
    const zoneId = emergency.zone || 'Z07';
    const zoneData = plantState?.zones?.find(z => z.id === zoneId);
    return {
      cx: zoneData?.x || 300, cy: zoneData?.y || 200,
      sigmaX: 30 + leakRate * 0.5, sigmaY: 15 + leakRate * 0.2,
      windRad: windDir * Math.PI / 180,
      leakRate, windDir,
    };
  }, [isActive, emergency, plantState]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !params) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.parentElement?.offsetWidth || 600;
    const H = canvas.height = canvas.parentElement?.offsetHeight || 400;
    ctx.clearRect(0, 0, W, H);

    const imgData = ctx.createImageData(W, H);
    const data = imgData.data;

    const { cx, cy, sigmaX, sigmaY, windRad } = params;
    const a = sigmaX * sigmaY;

    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const dx = (x - cx) * Math.cos(windRad) + (y - cy) * Math.sin(windRad);
        const dy = -(x - cx) * Math.sin(windRad) + (y - cy) * Math.cos(windRad);
        const val = gaussian(dx, dy, 0, 0, sigmaX, sigmaY);
        const idx = (y * W + x) * 4;
        if (val > 0.05) {
          const alpha = Math.min(val * 0.6, 0.6);
          data[idx] = 255;     // R
          data[idx + 1] = Math.round(165 * (1 - val)); // G
          data[idx + 2] = 0;    // B
          data[idx + 3] = Math.round(alpha * 255);
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Draw contour lines
    ctx.strokeStyle = 'rgba(255,165,0,0.3)';
    ctx.lineWidth = 1;
    for (let level = 0.2; level <= 0.8; level += 0.2) {
      ctx.beginPath();
      for (let angle = 0; angle < 360; angle += 2) {
        const rad = angle * Math.PI / 180;
        const r = level * 150;
        const lx = cx + r * Math.cos(rad + windRad) * 0.8;
        const ly = cy + r * Math.sin(rad + windRad) * 0.4;
        if (angle === 0) ctx.moveTo(lx, ly);
        else ctx.lineTo(lx, ly);
      }
      ctx.stroke();
    }

    // Label
    ctx.fillStyle = '#ffa000';
    ctx.font = '11px monospace';
    ctx.fillText(`\u{26A0}\uFE0F Gas Dispersion | Leak Rate: ${params.leakRate} kg/h | Wind: ${params.windDir}\u00B0`, 10, 20);
  }, [params]);

  if (!isActive) return null;

  return (
    <canvas ref={canvasRef} style={{
      position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
      pointerEvents: 'none', zIndex: 10,
    }} />
  );
}
