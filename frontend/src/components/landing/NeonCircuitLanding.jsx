import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import {
  ArrowRight, Search, Compass, ShieldCheck, BookOpen,
  TrendingUp, Zap, Cpu, Binary, Database,
  GraduationCap, Hexagon, Activity, Terminal
} from 'lucide-react';
import './NeonCircuitLanding.css';

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1], delay },
});

function TypingText({ text, speed = 40 }) {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(timer);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed]);
  return <span>{displayed}<span className="neon-cursor">|</span></span>;
}

function MatrixRain() {
  return (
    <div className="neon-matrix">
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className="neon-matrix-col"
          style={{
            left: `${i * 5 + Math.random() * 3}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${8 + Math.random() * 8}s`,
          }}
        >
          {Array.from({ length: 12 }).map((_, j) => (
            <span key={j} style={{ opacity: 0.1 + Math.random() * 0.3 }}>
              {String.fromCharCode(0x30A0 + Math.random() * 96)}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function NeonCircuitLanding({ onNavigate }) {
  return (
    <div className="neon">
      {/* Background */}
      <div className="neon-bg">
        <div className="neon-gradient-green" />
        <div className="neon-gradient-blue" />
        <div className="neon-scanline" />
        <MatrixRain />
        <div className="neon-circuit-grid" />
      </div>

      {/* Nav */}
      <nav className="neon-nav">
        <div className="neon-container">
          <div className="neon-nav-inner">
            <div className="neon-brand">
              <div className="neon-logo-hex">
                <GraduationCap size={15} strokeWidth={2} />
              </div>
              <span className="neon-brand-text">COLLEGE<span className="neon-text-glow">COMPASS</span></span>
            </div>
            <div className="neon-nav-links">
              <button className="neon-nav-link" onClick={() => onNavigate('shortlist')}>
                <Terminal size={13} /> SHORTLIST
              </button>
              <button className="neon-nav-link" onClick={() => onNavigate('explore')}>
                <Database size={13} /> EXPLORE
              </button>
            </div>
            <div className="neon-nav-status">
              <Activity size={12} />
              <span>SYS_ACTIVE</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="neon-hero">
        <div className="neon-container">
          <div className="neon-hero-layout">
            <div className="neon-hero-content">
              <motion.div className="neon-hero-badge" {...fadeUp(0)}>
                <Cpu size={12} />
                EVIDENCE.MATCHING.ENGINE
              </motion.div>

              <motion.h1 className="neon-hero-title" {...fadeUp(0.1)}>
                <span className="neon-text-glow">DECODE</span> YOUR
                <br />COLLEGE MATRIX
              </motion.h1>

              <motion.p className="neon-hero-desc" {...fadeUp(0.2)}>
                An intelligent shortlisting engine that processes your rank, exam,
                branch preference, budget, and location against verified admission
                data to output your optimal college sequence.
              </motion.p>

              <motion.div className="neon-hero-actions" {...fadeUp(0.3)}>
                <button className="neon-btn-glow" onClick={() => onNavigate('shortlist')}>
                  <Zap size={16} />
                  INITIALIZE SHORTLIST
                  <ArrowRight size={14} />
                </button>
                <button className="neon-btn-outline" onClick={() => onNavigate('explore')}>
                  <Search size={16} />
                  QUERY COLLEGE
                </button>
              </motion.div>

              <motion.div className="neon-hero-tags" {...fadeUp(0.4)}>
                <span className="neon-tag verified"><ShieldCheck size={11} /> VERIFIED_DATA</span>
                <span className="neon-tag cited"><BookOpen size={11} /> CITED_SOURCES</span>
                <span className="neon-tag honest"><TrendingUp size={11} /> HONEST_LIMITS</span>
              </motion.div>
            </div>

            {/* Terminal Preview */}
            <motion.div className="neon-terminal" {...fadeUp(0.3)}>
              <div className="neon-terminal-header">
                <div className="neon-terminal-dots">
                  <span /><span /><span />
                </div>
                <span className="neon-terminal-title">compass://shortlist-engine</span>
              </div>
              <div className="neon-terminal-body">
                <div className="neon-term-line">
                  <span className="neon-term-prompt">$</span>
                  <span className="neon-term-cmd">compass.query(</span>
                </div>
                <div className="neon-term-line indent">
                  <span className="neon-term-key">exam:</span> <span className="neon-term-str">"JEE Advanced"</span>
                </div>
                <div className="neon-term-line indent">
                  <span className="neon-term-key">rank:</span> <span className="neon-term-num">4500</span>
                </div>
                <div className="neon-term-line indent">
                  <span className="neon-term-key">branch:</span> <span className="neon-term-str">"CSE"</span>
                </div>
                <div className="neon-term-line indent">
                  <span className="neon-term-key">budget:</span> <span className="neon-term-str">"8L/yr"</span>
                </div>
                <div className="neon-term-line">
                  <span className="neon-term-cmd">)</span>
                </div>
                <div className="neon-term-line output">
                  <span className="neon-term-arrow">→</span>
                  <span className="neon-term-result">Found 5 matches (3 safe, 1 moderate, 1 stretch)</span>
                </div>
                <div className="neon-term-line output">
                  <span className="neon-term-arrow">→</span>
                  <span className="neon-term-result">#1 IIT Hyderabad • CSE • Score: 0.95 ✓</span>
                </div>
                <div className="neon-term-line output">
                  <span className="neon-term-arrow">→</span>
                  <span className="neon-term-result">#2 NIT Trichy • CSE • Score: 0.90 ✓</span>
                </div>
                <div className="neon-term-line blink">
                  <span className="neon-term-prompt">$</span>
                  <TypingText text="compass.enrich(results)" speed={60} />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="neon-features">
        <div className="neon-container">
          <motion.h2 className="neon-section-title" {...fadeUp(0)}>
            <Hexagon size={18} className="neon-section-icon" />
            SYSTEM CAPABILITIES
          </motion.h2>
          <div className="neon-feature-grid">
            {[
              { icon: <Database size={22} />, title: 'STRUCTURED RANKING', desc: 'Multi-signal scoring: rank fit + affordability + location + hostel. Not a loose chatbot — a precision engine.' },
              { icon: <ShieldCheck size={22} />, title: 'EVIDENCE PROTOCOL', desc: 'Every claim traced to official college data. Reddit and YouTube are secondary — clearly marked and opt-in.' },
              { icon: <Activity size={22} />, title: 'PROGRESSIVE LOAD', desc: 'Fast initial ranking, then async enrichment. Each card hydrates with fit, cost, outcomes, and campus data.' },
              { icon: <Binary size={22} />, title: 'CONFIDENCE SCORING', desc: 'When evidence is weak, we say so. No hallucinated stats, no false precision. Clean abstention protocol.' },
            ].map((f, i) => (
              <motion.div className="neon-feature-card" key={i} {...fadeUp(0.08 * i)}>
                <div className="neon-feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
                <div className="neon-feature-border-glow" />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="neon-cta">
        <div className="neon-container">
          <motion.div className="neon-cta-card" {...fadeUp(0)}>
            <div className="neon-cta-glow" />
            <Zap size={24} className="neon-cta-icon" />
            <h2>READY TO INITIALIZE?</h2>
            <p>Boot your college shortlist engine with one click.</p>
            <button className="neon-btn-glow" onClick={() => onNavigate('shortlist')}>
              START ENGINE <ArrowRight size={14} />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="neon-footer">
        <div className="neon-container">
          <p className="neon-footer-brand">COLLEGECOMPASS</p>
          <p className="neon-footer-note">
            Data sourced from official college websites. Cutoffs are indicative. Verify with official portals.
          </p>
        </div>
      </footer>
    </div>
  );
}
