import { motion } from 'framer-motion';
import {
  ArrowRight, Search, Compass, ShieldCheck, BookOpen,
  TrendingUp, Leaf, TreePine, Mountain,
  GraduationCap, CheckCircle2, ChevronRight, Eye
} from 'lucide-react';
import './SageLanding.css';

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94], delay },
});

export default function SageLanding({ onNavigate }) {
  return (
    <div className="sage">
      {/* Organic bg shapes */}
      <div className="sage-bg">
        <div className="sage-blob-1" />
        <div className="sage-blob-2" />
        <div className="sage-dot-grid" />
      </div>

      {/* Nav */}
      <nav className="sage-nav">
        <div className="sage-container">
          <div className="sage-nav-inner">
            <div className="sage-brand">
              <div className="sage-logo-leaf">
                <GraduationCap size={17} strokeWidth={1.8} />
              </div>
              <span className="sage-brand-text">CollegeCompass</span>
            </div>
            <div className="sage-nav-center">
              <button className="sage-nav-link" onClick={() => onNavigate('shortlist')}>Shortlist</button>
              <button className="sage-nav-link" onClick={() => onNavigate('explore')}>Explore</button>
            </div>
            <div className="sage-nav-right">
              <span className="sage-trust-pill">
                <Leaf size={12} />
                Evidence-First
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="sage-hero">
        <div className="sage-container">
          <motion.div className="sage-hero-center" initial="initial" animate="animate">
            <motion.div className="sage-hero-chip" {...fadeUp(0)}>
              <ShieldCheck size={13} />
              Grounded in official data
            </motion.div>

            <motion.h1 className="sage-hero-title" {...fadeUp(0.1)}>
              Find your college,
              <br />
              <span className="sage-accent">naturally.</span>
            </motion.h1>

            <motion.p className="sage-hero-sub" {...fadeUp(0.2)}>
              CollegeCompass helps you navigate Indian engineering admissions with
              calm clarity. Enter your profile, receive a curated shortlist backed
              by official evidence — not noise.
            </motion.p>

            <motion.div className="sage-hero-btns" {...fadeUp(0.3)}>
              <button className="sage-btn-primary" onClick={() => onNavigate('shortlist')}>
                <Search size={16} />
                Start Shortlisting
                <ArrowRight size={14} />
              </button>
              <button className="sage-btn-outline" onClick={() => onNavigate('explore')}>
                <Compass size={16} />
                Explore a College
              </button>
            </motion.div>
          </motion.div>

          {/* Illustration: Three Pillars */}
          <motion.div className="sage-pillars" {...fadeUp(0.4)}>
            {[
              { icon: <ShieldCheck size={20} />, label: 'Official Sources', detail: 'Every fact cited from college data' },
              { icon: <Eye size={20} />, label: 'Transparent Signals', detail: 'Student opinions clearly labeled' },
              { icon: <CheckCircle2 size={20} />, label: 'Honest Limits', detail: 'Abstains when evidence is weak' },
            ].map((p, i) => (
              <div className="sage-pillar" key={i}>
                <div className="sage-pillar-icon">{p.icon}</div>
                <strong>{p.label}</strong>
                <span>{p.detail}</span>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Journey Cards */}
      <section className="sage-journeys">
        <div className="sage-container">
          <motion.h2 className="sage-section-title" {...fadeUp(0)}>
            Two paths, one goal
          </motion.h2>
          <motion.p className="sage-section-sub" {...fadeUp(0.05)}>
            Whether you're starting from scratch or researching one college deep, we've got you.
          </motion.p>

          <div className="sage-journey-grid">
            <motion.div className="sage-journey shortlist" {...fadeUp(0.1)}>
              <div className="sage-journey-top">
                <div className="sage-journey-tag">Primary</div>
                <TreePine size={28} className="sage-journey-deco" />
              </div>
              <h3>Shortlist Colleges</h3>
              <p>Enter your exam, rank, preferred branches, budget, location, and hostel preference. Get a ranked list — progressively enriched with official data.</p>
              <ul>
                <li><ChevronRight size={12} /> Rank-fit matching</li>
                <li><ChevronRight size={12} /> Budget filtering</li>
                <li><ChevronRight size={12} /> Progressive enrichment</li>
                <li><ChevronRight size={12} /> Cited evidence</li>
              </ul>
              <button className="sage-btn-primary" onClick={() => onNavigate('shortlist')}>
                Build Shortlist <ArrowRight size={14} />
              </button>
            </motion.div>

            <motion.div className="sage-journey explore" {...fadeUp(0.2)}>
              <div className="sage-journey-top">
                <div className="sage-journey-tag">Exploration</div>
                <Mountain size={28} className="sage-journey-deco" />
              </div>
              <h3>Explore a College</h3>
              <p>Search for any college to see official summaries, admissions, fees, placements, and campus life. Ask follow-up questions for deeper insights.</p>
              <ul>
                <li><ChevronRight size={12} /> Official summaries</li>
                <li><ChevronRight size={12} /> Admissions & fees</li>
                <li><ChevronRight size={12} /> Placement data</li>
                <li><ChevronRight size={12} /> Campus & outcomes</li>
              </ul>
              <button className="sage-btn-outline" onClick={() => onNavigate('explore')}>
                Explore Now <ArrowRight size={14} />
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="sage-process">
        <div className="sage-container">
          <motion.h2 className="sage-section-title" {...fadeUp(0)}>How it works</motion.h2>
          <div className="sage-process-steps">
            {[
              { num: '01', title: 'Share your profile', desc: 'Entrance exam, rank, branches, budget, states, hostel preference.' },
              { num: '02', title: 'We match & rank', desc: 'Fast first-pass ranking. Then each college enriches with fit, cost, and outcomes.' },
              { num: '03', title: 'Decide confidently', desc: 'Every claim is cited. Uncertain data is flagged. You always know what\'s official.' },
            ].map((s, i) => (
              <motion.div className="sage-step" key={i} {...fadeUp(0.1 * i)}>
                <div className="sage-step-num">{s.num}</div>
                <div className="sage-step-line" />
                <h4>{s.title}</h4>
                <p>{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="sage-cta-section">
        <div className="sage-container">
          <motion.div className="sage-cta-box" {...fadeUp(0)}>
            <Leaf size={28} className="sage-cta-icon" />
            <h2>Ready to begin?</h2>
            <p>Start with evidence. End with confidence.</p>
            <div className="sage-cta-btns">
              <button className="sage-btn-primary" onClick={() => onNavigate('shortlist')}>
                Start Shortlisting <ArrowRight size={14} />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="sage-footer">
        <div className="sage-container sage-footer-inner">
          <p className="sage-footer-brand">CollegeCompass</p>
          <p className="sage-footer-notice">
            Data sourced from official college websites. Cutoff ranks are indicative.
            Always verify with official counselling portals before making decisions.
          </p>
        </div>
      </footer>
    </div>
  );
}
