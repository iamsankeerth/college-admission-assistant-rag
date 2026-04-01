import { motion, useMotionValue, useTransform } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import {
  ArrowRight, Search, Compass, ShieldCheck, BookOpen,
  TrendingUp, Sparkles, Zap, Target, GraduationCap,
  Star, Globe, Lock
} from 'lucide-react';
import './AstraLanding.css';

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1], delay },
});

function OrbitRing({ radius, duration, children, reverse = false }) {
  return (
    <div className="astra-orbit" style={{ width: radius * 2, height: radius * 2 }}>
      <div
        className="astra-orbit-ring"
        style={{
          width: '100%', height: '100%',
          animation: `astra-spin ${duration}s linear infinite ${reverse ? 'reverse' : ''}`,
        }}
      >
        {children}
      </div>
    </div>
  );
}

function FloatingParticle({ delay, x, y, size }) {
  return (
    <motion.div
      className="astra-particle"
      style={{ left: `${x}%`, top: `${y}%`, width: size, height: size }}
      animate={{ opacity: [0, 1, 0], scale: [0.5, 1, 0.5] }}
      transition={{ duration: 3 + Math.random() * 2, repeat: Infinity, delay, ease: 'easeInOut' }}
    />
  );
}

export default function AstraLanding({ onNavigate }) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => {
      setMousePos({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return (
    <div className="astra">
      {/* Background Effects */}
      <div className="astra-bg">
        <div className="astra-gradient-1" style={{
          transform: `translate(${mousePos.x * 30}px, ${mousePos.y * 20}px)`
        }} />
        <div className="astra-gradient-2" style={{
          transform: `translate(${-mousePos.x * 20}px, ${-mousePos.y * 15}px)`
        }} />
        <div className="astra-stars">
          {Array.from({ length: 60 }).map((_, i) => (
            <FloatingParticle
              key={i}
              delay={i * 0.15}
              x={Math.random() * 100}
              y={Math.random() * 100}
              size={Math.random() * 3 + 1}
            />
          ))}
        </div>
        <div className="astra-grid-overlay" />
      </div>

      {/* Navigation */}
      <nav className="astra-nav">
        <div className="astra-container">
          <div className="astra-nav-inner">
            <div className="astra-brand">
              <div className="astra-logo-orb">
                <GraduationCap size={16} strokeWidth={2} />
              </div>
              <span className="astra-logo-text">CollegeCompass</span>
            </div>
            <div className="astra-nav-links">
              <button className="astra-nav-link" onClick={() => onNavigate('shortlist')}>
                <Search size={14} /> Shortlist
              </button>
              <button className="astra-nav-link" onClick={() => onNavigate('explore')}>
                <Compass size={14} /> Explore
              </button>
            </div>
            <div className="astra-nav-status">
              <Lock size={12} />
              <span>Evidence-First</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="astra-hero">
        <div className="astra-container">
          <div className="astra-hero-layout">
            <div className="astra-hero-content">
              <motion.div className="astra-hero-badge" {...fadeUp(0)}>
                <Sparkles size={13} />
                Intelligent College Matching
              </motion.div>

              <motion.h1 className="astra-hero-title" {...fadeUp(0.1)}>
                Navigate your
                <span className="astra-glow-text"> college universe</span>
                <br />with precision.
              </motion.h1>

              <motion.p className="astra-hero-desc" {...fadeUp(0.2)}>
                Stop guessing. CollegeCompass matches your exam rank, branch preference,
                budget, and location with official admission data to create your
                perfect college shortlist.
              </motion.p>

              <motion.div className="astra-hero-actions" {...fadeUp(0.3)}>
                <button className="astra-btn-glow" onClick={() => onNavigate('shortlist')}>
                  <Zap size={16} />
                  Build Your Shortlist
                  <ArrowRight size={14} />
                </button>
                <button className="astra-btn-ghost" onClick={() => onNavigate('explore')}>
                  <Globe size={16} />
                  Explore College
                </button>
              </motion.div>

              <motion.div className="astra-trust-row" {...fadeUp(0.4)}>
                <div className="astra-trust-chip">
                  <ShieldCheck size={13} />
                  Official Data
                </div>
                <div className="astra-trust-chip">
                  <Target size={13} />
                  Rank-Personalized
                </div>
                <div className="astra-trust-chip">
                  <BookOpen size={13} />
                  Cited Sources
                </div>
              </motion.div>
            </div>

            {/* Orbital Visualization */}
            <motion.div className="astra-hero-visual" {...fadeUp(0.3)}>
              <div className="astra-orbit-system">
                <div className="astra-center-node">
                  <span>You</span>
                </div>
                <OrbitRing radius={100} duration={20}>
                  <div className="astra-orbit-dot safe" style={{ top: 0, left: '50%' }}>IIT</div>
                </OrbitRing>
                <OrbitRing radius={150} duration={30} reverse>
                  <div className="astra-orbit-dot moderate" style={{ top: 0, left: '50%' }}>NIT</div>
                </OrbitRing>
                <OrbitRing radius={200} duration={40}>
                  <div className="astra-orbit-dot ambitious" style={{ top: 0, left: '50%' }}>BITS</div>
                </OrbitRing>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="astra-features">
        <div className="astra-container">
          <motion.h2 className="astra-section-title" {...fadeUp(0)}>
            Built for <span className="astra-glow-text">serious decisions</span>
          </motion.h2>
          <div className="astra-feature-grid">
            {[
              {
                icon: <Target size={24} />,
                title: 'Structured Shortlisting',
                desc: 'Input your exam, rank, branches, budget, and location preferences. Receive a ranked shortlist — not a vague chatbot response.',
                color: '#6366F1',
              },
              {
                icon: <ShieldCheck size={24} />,
                title: 'Evidence First, Always',
                desc: 'Every recommendation cites official college sources. Reddit and YouTube signals are secondary, clearly labeled, and always opt-in.',
                color: '#10B981',
              },
              {
                icon: <TrendingUp size={24} />,
                title: 'Progressive Enrichment',
                desc: 'Fast results first. Each card then enriches with fit snapshot, cost breakdowns, placement outcomes, and campus insights.',
                color: '#F59E0B',
              },
              {
                icon: <Star size={24} />,
                title: 'Honest Confidence',
                desc: 'We tell you when evidence is weak. Uncertain data gets flagged. No false promises — only transparent guidance.',
                color: '#EC4899',
              },
            ].map((f, i) => (
              <motion.div className="astra-feature-card" key={i} {...fadeUp(0.1 * i)}>
                <div className="astra-feature-glow" style={{ background: `radial-gradient(circle at center, ${f.color}15, transparent 70%)` }} />
                <div className="astra-feature-icon" style={{ color: f.color, background: `${f.color}12` }}>
                  {f.icon}
                </div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="astra-cta">
        <div className="astra-container">
          <motion.div className="astra-cta-card" {...fadeUp(0)}>
            <div className="astra-cta-glow" />
            <h2>Ready to find your best-fit colleges?</h2>
            <p>Join thousands of students making data-driven college decisions.</p>
            <div className="astra-cta-actions">
              <button className="astra-btn-glow" onClick={() => onNavigate('shortlist')}>
                <Search size={16} /> Start Shortlisting <ArrowRight size={14} />
              </button>
              <button className="astra-btn-ghost" onClick={() => onNavigate('explore')}>
                Or explore a specific college
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="astra-footer">
        <div className="astra-container">
          <p className="astra-footer-brand">CollegeCompass</p>
          <p className="astra-footer-note">
            Data sourced from official college websites. Cutoff ranks are indicative.
            Always verify with official counselling portals.
          </p>
        </div>
      </footer>
    </div>
  );
}
