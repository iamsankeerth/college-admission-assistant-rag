import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Palette, ChevronLeft, ChevronRight, X } from 'lucide-react';
import MeridianLanding from './MeridianLanding';
import AstraLanding from './AstraLanding';
import SageLanding from './SageLanding';
import NeonCircuitLanding from './NeonCircuitLanding';
import IvoryTowerLanding from './IvoryTowerLanding';
import './LandingVersionSwitcher.css';

const VERSIONS = [
  { id: 'meridian', name: 'Meridian', tagline: 'Warm Editorial', color: '#C45D3E' },
  { id: 'astra', name: 'Astra', tagline: 'Deep Space', color: '#6366F1' },
  { id: 'sage', name: 'Sage', tagline: 'Earthy & Calm', color: '#3D8B5F' },
  { id: 'neon', name: 'Neon Circuit', tagline: 'Electric Cyber', color: '#00FFB2' },
  { id: 'ivory', name: 'Ivory Tower', tagline: 'Academic Prestige', color: '#C5A04E' },
];

const LANDING_COMPONENTS = {
  meridian: MeridianLanding,
  astra: AstraLanding,
  sage: SageLanding,
  neon: NeonCircuitLanding,
  ivory: IvoryTowerLanding,
};

export default function LandingVersionSwitcher({ onNavigate }) {
  const [currentVersion, setCurrentVersion] = useState(0);
  const [panelOpen, setPanelOpen] = useState(true);
  const [direction, setDirection] = useState(1);

  const version = VERSIONS[currentVersion];
  const LandingComponent = LANDING_COMPONENTS[version.id];

  const goTo = (idx) => {
    setDirection(idx > currentVersion ? 1 : -1);
    setCurrentVersion(idx);
  };

  const next = () => {
    setDirection(1);
    setCurrentVersion((prev) => (prev + 1) % VERSIONS.length);
  };

  const prev = () => {
    setDirection(-1);
    setCurrentVersion((prev) => (prev - 1 + VERSIONS.length) % VERSIONS.length);
  };

  return (
    <div className="landing-switcher-root">
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={version.id}
          custom={direction}
          initial={{ opacity: 0, x: direction * 60 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: direction * -60 }}
          transition={{ duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
          style={{ minHeight: '100vh' }}
        >
          <LandingComponent onNavigate={onNavigate} />
        </motion.div>
      </AnimatePresence>

      {/* Floating Switcher Panel */}
      <AnimatePresence>
        {panelOpen && (
          <motion.div
            className="version-panel"
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            <div className="version-panel-header">
              <span className="version-panel-title">
                <Palette size={14} />
                Design Versions
              </span>
              <button className="version-panel-close" onClick={() => setPanelOpen(false)}>
                <X size={14} />
              </button>
            </div>
            <div className="version-panel-nav">
              <button className="version-nav-arrow" onClick={prev}><ChevronLeft size={16} /></button>
              <div className="version-dots">
                {VERSIONS.map((v, i) => (
                  <button
                    key={v.id}
                    className={`version-dot ${i === currentVersion ? 'active' : ''}`}
                    onClick={() => goTo(i)}
                    title={v.name}
                  >
                    <span
                      className="version-dot-color"
                      style={{ background: v.color }}
                    />
                  </button>
                ))}
              </div>
              <button className="version-nav-arrow" onClick={next}><ChevronRight size={16} /></button>
            </div>
            <div className="version-panel-info">
              <span className="version-panel-name">{version.name}</span>
              <span className="version-panel-tagline">{version.tagline}</span>
            </div>
            <div className="version-panel-counter">
              {currentVersion + 1} / {VERSIONS.length}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toggle button when panel is closed */}
      {!panelOpen && (
        <motion.button
          className="version-toggle-btn"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          onClick={() => setPanelOpen(true)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <Palette size={18} />
        </motion.button>
      )}
    </div>
  );
}
