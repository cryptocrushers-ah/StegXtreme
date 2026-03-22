import React, { useEffect, useRef, useState } from 'react';
import './WelcomeSplash.css';

interface WelcomeSplashProps {
  /** Called after the full animation + fade-out completes */
  onComplete: () => void;
}

const WelcomeSplash: React.FC<WelcomeSplashProps> = ({ onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const [fadingOut, setFadingOut] = useState(false);

  /* ── Star Field / Warp Speed (matches landing page) ── */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    resize();
    window.addEventListener('resize', resize);

    interface Star {
      x: number; y: number; z: number; pz: number;
      r: number; g: number; b: number; size: number;
    }

    const STAR_COUNT = 500;

    const randomTint = (): [number, number, number] => {
      const roll = Math.random();
      if (roll > 0.88) return [0, 255, 224];
      if (roll > 0.78) return [180, 150, 255];
      return [210, 220, 255];
    };

    const spawnStar = (): Star => {
      const [r, g, b] = randomTint();
      return {
        x: (Math.random() - 0.5) * 2,
        y: (Math.random() - 0.5) * 2,
        z: Math.random(),
        pz: Math.random(),
        r, g, b,
        size: Math.random() * 1.2 + 0.3,
      };
    };

    const stars: Star[] = Array.from({ length: STAR_COUNT }, spawnStar);

    // On the splash we start slow and ramp up for drama
    let speed = 0.002;
    const TARGET_SPEED = 0.012;

    const draw = () => {
      // Gradually accelerate — slow at first, then warp
      speed += (TARGET_SPEED - speed) * 0.008;

      ctx.fillStyle = 'rgba(4, 4, 10, 0.22)';
      ctx.fillRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;

      for (const s of stars) {
        s.pz = s.z;
        s.z -= speed;

        if (s.z <= 0) {
          s.x = (Math.random() - 0.5) * 2;
          s.y = (Math.random() - 0.5) * 2;
          s.z = 1;
          s.pz = 1;
          const [r, g, b] = randomTint();
          s.r = r; s.g = g; s.b = b;
          s.size = Math.random() * 1.2 + 0.3;
          continue;
        }

        const scale = 1 / s.z;
        const sx = cx + s.x * scale * cx;
        const sy = cy + s.y * scale * cy;

        const pScale = 1 / s.pz;
        const px = cx + s.x * pScale * cx;
        const py = cy + s.y * pScale * cy;

        const brightness = 1 - s.z;
        const alpha = Math.min(brightness * 1.4, 1);
        const radius = s.size * brightness * 2.2;

        if (s.pz < 1) {
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(sx, sy);
          ctx.strokeStyle = `rgba(${s.r},${s.g},${s.b},${alpha * 0.7})`;
          ctx.lineWidth = radius * 0.6;
          ctx.lineCap = 'round';
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(sx, sy, Math.max(radius * 0.5, 0.4), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${s.r},${s.g},${s.b},${alpha})`;
        ctx.fill();

        if (brightness > 0.7) {
          ctx.beginPath();
          ctx.arc(sx, sy, radius * 2.5, 0, Math.PI * 2);
          const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, radius * 2.5);
          glow.addColorStop(0, `rgba(${s.r},${s.g},${s.b},${(brightness - 0.7) * 0.25})`);
          glow.addColorStop(1, `rgba(${s.r},${s.g},${s.b},0)`);
          ctx.fillStyle = glow;
          ctx.fill();
        }
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, []);

/* ── Timing: progress bar ends ~2.7s in, then fade out, then unmount ── */
useEffect(() => {
  // progress bar animation is 1.6s starting at 1.1s => ends at 2.7s
  // hold for 0.4s then start fade-out
  const fadeTimer = setTimeout(() => setFadingOut(true), 3100);
  // after fade-out transition (0.9s), call onComplete
  const doneTimer = setTimeout(() => onComplete(), 4100);
  return () => { clearTimeout(fadeTimer); clearTimeout(doneTimer); };
}, [onComplete]);

return (
  <div className={`welcome-splash${fadingOut ? ' fade-out' : ''}`}>
    {/* Cloud canvas */}
    <canvas ref={canvasRef} className="splash-canvas" />

    {/* Scanline texture */}
    <div className="splash-scanline" />

    {/* Corner brackets */}
    <div className="splash-corner tl" />
    <div className="splash-corner tr" />
    <div className="splash-corner bl" />
    <div className="splash-corner br" />

    {/* Main content */}
    <div className="splash-content">
      <div className="splash-dot" />
      <p className="splash-label">Welcome to the</p>
      <h1 className="splash-title">
        <span>Workplace</span>
      </h1>
      <p className="splash-tagline">
        StegXtreme · Multi-domain steganography platform
      </p>
      <div className="splash-progress-wrap">
        <div className="splash-progress-bar" />
      </div>
    </div>

    {/* Version */}
    <span className="splash-version">v2.0 · StegXtreme</span>
  </div>
);
};

export default WelcomeSplash;