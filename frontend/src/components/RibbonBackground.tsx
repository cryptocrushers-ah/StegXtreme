import React, { useEffect, useRef } from 'react';
import './RibbonBackground.css';

const RibbonBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const ribbons = [
      { yRatio: 0.18, amp: 110, freq: 0.0022, speed: 0.00006, phase: 0.0, thickness: 90, r: 200, g: 210, b: 220, alpha: 0.18 },
      { yRatio: 0.32, amp: 130, freq: 0.0018, speed: 0.00004, phase: 1.8, thickness: 110, r: 180, g: 195, b: 210, alpha: 0.14 },
      { yRatio: 0.50, amp: 100, freq: 0.0026, speed: 0.00007, phase: 3.5, thickness: 95, r: 0, g: 255, b: 224, alpha: 0.12 },
      { yRatio: 0.65, amp: 140, freq: 0.0015, speed: 0.00004, phase: 0.9, thickness: 120, r: 160, g: 180, b: 200, alpha: 0.13 },
      { yRatio: 0.80, amp: 90, freq: 0.0030, speed: 0.00008, phase: 2.4, thickness: 80, r: 139, g: 92, b: 246, alpha: 0.10 },
      { yRatio: 0.42, amp: 120, freq: 0.0020, speed: 0.00005, phase: 5.1, thickness: 100, r: 220, g: 225, b: 235, alpha: 0.12 },
    ];

    let t = 0;

    const buildPath = (
      width: number, height: number,
      yRatio: number, amp: number, freq: number, phase: number, offset: number
    ): [number, number][] => {
      const pts: [number, number][] = [];
      for (let x = -10; x <= width + 10; x += 12) {
        const y = height * yRatio
          + Math.sin(x * freq + phase) * amp
          + Math.sin(x * freq * 1.6 + phase * 0.7) * (amp * 0.35)
          + offset;
        pts.push([x, y]);
      }
      return pts;
    };

    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      for (const rb of ribbons) {
        const phase = rb.phase + t * rb.speed * 1000;
        const half = rb.thickness / 2;

        const topPts = buildPath(width, height, rb.yRatio, rb.amp, rb.freq, phase, -half);
        const botPts = buildPath(width, height, rb.yRatio, rb.amp, rb.freq, phase, +half);

        const midY = height * rb.yRatio;
        const grad = ctx.createLinearGradient(0, midY - half, 0, midY + half);
        grad.addColorStop(0, `rgba(${rb.r},${rb.g},${rb.b},0)`);
        grad.addColorStop(0.25, `rgba(${rb.r},${rb.g},${rb.b},${rb.alpha})`);
        grad.addColorStop(0.5, `rgba(${rb.r},${rb.g},${rb.b},${rb.alpha * 1.7})`);
        grad.addColorStop(0.75, `rgba(${rb.r},${rb.g},${rb.b},${rb.alpha})`);
        grad.addColorStop(1, `rgba(${rb.r},${rb.g},${rb.b},0)`);

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(topPts[0][0], topPts[0][1]);
        for (let i = 1; i < topPts.length; i++) {
          const [px, py] = topPts[i - 1];
          const [cx, cy] = topPts[i];
          ctx.quadraticCurveTo(px, py, (px + cx) / 2, (py + cy) / 2);
        }
        for (let i = botPts.length - 1; i > 0; i--) {
          const [px, py] = botPts[i];
          const [cx, cy] = botPts[i - 1];
          ctx.quadraticCurveTo(px, py, (px + cx) / 2, (py + cy) / 2);
        }
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.restore();
      }

      t += 1;
      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="ribbon-canvas" aria-hidden="true" />;
};

export default RibbonBackground;
