import React, { useEffect, useState } from 'react';
import './WelcomeSplash.css';

interface WelcomeSplashProps {
  /** Called after the full animation + fade-out completes */
  onComplete: () => void;
}

const WelcomeSplash: React.FC<WelcomeSplashProps> = ({ onComplete }) => {
  const [fadingOut, setFadingOut] = useState(false);

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
