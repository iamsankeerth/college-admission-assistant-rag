import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight, Search, Compass, ShieldCheck, BookOpen,
  TrendingUp, Crown, GraduationCap,
  ChevronRight, Award, Landmark, ScrollText, Scale, RefreshCw
} from 'lucide-react';
import './IvoryTowerLanding.css';

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94], delay },
});

export default function IvoryTowerLanding({ onNavigate, restoredShortlist }) {
  const [showRestore, setShowRestore] = useState(false);

  useEffect(() => {
    if (restoredShortlist) {
      setShowRestore(true);
    }
  }, [restoredShortlist]);

  const handleContinue = () => {
    setShowRestore(false);
    onNavigate('shortlist-results');
  };

  const handleStartFresh = () => {
    setShowRestore(false);
    onNavigate('shortlist');
  };

  return (
    <div className="ivory">
      <div className="ivory-bg">
        <div className="ivory-vignette" />
        <div className="ivory-gold-line top" />
        <div className="ivory-pattern" />
      </div>

      {showRestore && (
        <motion.div
          className="ivory-restore-banner"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="ivory-container">
            <div className="ivory-restore-inner">
              <div className="ivory-restore-icon">
                <RefreshCw size={18} />
              </div>
              <div className="ivory-restore-text">
                <strong>Welcome back!</strong>
                <span>We found your previous shortlist. Continue where you left off?</span>
              </div>
              <div className="ivory-restore-actions">
                <button className="ivory-btn-gold small" onClick={handleContinue}>
                  Continue
                </button>
                <button className="ivory-btn-subtle small" onClick={handleStartFresh}>
                  Start Fresh
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <nav className="ivory-nav">
        <div className="ivory-container">
          <div className="ivory-nav-inner">
            <div className="ivory-brand">
              <div className="ivory-logo-crest">
                <GraduationCap size={16} strokeWidth={1.6} />
              </div>
              <span className="ivory-brand-text">CollegeCompass</span>
            </div>
            <div className="ivory-nav-center">
              <button className="ivory-nav-link" onClick={() => onNavigate('shortlist')}>Shortlist</button>
              <span className="ivory-nav-dot">·</span>
              <button className="ivory-nav-link" onClick={() => onNavigate('explore')}>Explore</button>
            </div>
            <div className="ivory-nav-right">
              <span className="ivory-crest-badge">
                <Crown size={12} />
                Evidence-First
              </span>
            </div>
          </div>
        </div>
      </nav>

      <section className="ivory-hero">
        <div className="ivory-container">
          <motion.div className="ivory-hero-inner" initial="initial" animate="animate">
            <motion.div className="ivory-hero-ornament" {...fadeUp(0)}>
              <div className="ivory-ornament-line" />
              <span className="ivory-ornament-text">EST. BY EVIDENCE</span>
              <div className="ivory-ornament-line" />
            </motion.div>

            <motion.h1 className="ivory-hero-title" {...fadeUp(0.1)}>
              The Art of
              <br />
              <span className="ivory-gold">Choosing Well.</span>
            </motion.h1>

            <motion.p className="ivory-hero-subtitle" {...fadeUp(0.2)}>
              CollegeCompass is a decision-support instrument for Indian engineering admissions.
              Curated shortlists built on official data — because your college choice
              deserves the care of a considered judgment, not a lucky guess.
            </motion.p>

            <motion.div className="ivory-hero-actions" {...fadeUp(0.3)}>
              <button className="ivory-btn-gold" onClick={() => onNavigate('shortlist')}>
                <Search size={16} />
                Begin Your Shortlist
                <ArrowRight size={14} />
              </button>
              <button className="ivory-btn-subtle" onClick={() => onNavigate('explore')}>
                <Compass size={16} />
                Explore a College
              </button>
            </motion.div>

            <motion.div className="ivory-hero-insignia" {...fadeUp(0.4)}>
              <div className="ivory-insignia-item">
                <ShieldCheck size={14} />
                <span>Official Sources</span>
              </div>
              <div className="ivory-insignia-sep">◆</div>
              <div className="ivory-insignia-item">
                <BookOpen size={14} />
                <span>Cited Evidence</span>
              </div>
              <div className="ivory-insignia-sep">◆</div>
              <div className="ivory-insignia-item">
                <Scale size={14} />
                <span>Honest Assessment</span>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section className="ivory-showcase">
        <div className="ivory-container">
          <motion.div className="ivory-showcase-card" {...fadeUp(0.2)}>
            <div className="ivory-showcase-header">
              <div className="ivory-showcase-label">
                <Landmark size={14} />
                Exemplar Shortlist Card
              </div>
              <span className="ivory-badge-official">VERIFIED</span>
            </div>
            <div className="ivory-showcase-body">
              <div className="ivory-showcase-college">
                <div className="ivory-college-crest">
                  <Award size={20} />
                </div>
                <div className="ivory-college-info">
                  <h3>IIT Hyderabad</h3>
                  <p>Computer Science & Engineering · Telangana, South India</p>
                </div>
                <div className="ivory-fit-label safe">Safe Fit</div>
              </div>
              <div className="ivory-showcase-stats">
                <div className="ivory-stat">
                  <div className="ivory-stat-label">COMPOSITE SCORE</div>
                  <div className="ivory-stat-value">0.95</div>
                </div>
                <div className="ivory-stat">
                  <div className="ivory-stat-label">ANNUAL COST</div>
                  <div className="ivory-stat-value">₹4.5L</div>
                </div>
                <div className="ivory-stat">
                  <div className="ivory-stat-label">CLOSING RANK</div>
                  <div className="ivory-stat-value">~5,200</div>
                </div>
                <div className="ivory-stat">
                  <div className="ivory-stat-label">MEDIAN CTC</div>
                  <div className="ivory-stat-value">₹22 LPA</div>
                </div>
              </div>
              <div className="ivory-showcase-evidence">
                <div className="ivory-evidence-accent" />
                <blockquote>
                  "Rank comfortably within closing cutoff range. Strong CSE program with AI/ML research focus.
                  Annual cost within budget at ₹4.5L/year. Located in preferred zone — South."
                </blockquote>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="ivory-paths">
        <div className="ivory-container">
          <motion.div className="ivory-paths-header" {...fadeUp(0)}>
            <div className="ivory-ornament-line short" />
            <h2>Two Considered Paths</h2>
            <p>Whether charting broad options or studying one institution deeply</p>
          </motion.div>

          <div className="ivory-paths-grid">
            <motion.div className="ivory-path-card primary" {...fadeUp(0.1)}>
              <div className="ivory-path-emblem">
                <ScrollText size={24} />
              </div>
              <div className="ivory-path-type">PRIMARY JOURNEY</div>
              <h3>Shortlist Colleges</h3>
              <p>
                Provide your entrance exam, rank, preferred branches, budget, location,
                and hostel requirement. Receive a curated, ranked shortlist that progressively
                enriches with official fit, cost, outcome, and campus data.
              </p>
              <ul>
                <li><ChevronRight size={12} /> Rank-based matching algorithm</li>
                <li><ChevronRight size={12} /> Budget and location optimization</li>
                <li><ChevronRight size={12} /> Progressive data enrichment</li>
                <li><ChevronRight size={12} /> Full official citation</li>
              </ul>
              <button className="ivory-btn-gold" onClick={() => onNavigate('shortlist')}>
                Begin Shortlisting <ArrowRight size={14} />
              </button>
            </motion.div>

            <motion.div className="ivory-path-card" {...fadeUp(0.2)}>
              <div className="ivory-path-emblem">
                <Landmark size={24} />
              </div>
              <div className="ivory-path-type">DEEP EXPLORATION</div>
              <h3>Explore One College</h3>
              <p>
                Select any institution to view its official summary, admissions process,
                fee structure, hostel availability, placement record, and campus culture —
                all sourced from verified data with follow-up questions available.
              </p>
              <ul>
                <li><ChevronRight size={12} /> Official institutional summary</li>
                <li><ChevronRight size={12} /> Admissions & counselling detail</li>
                <li><ChevronRight size={12} /> Fee, scholarship & hostel data</li>
                <li><ChevronRight size={12} /> Placement & campus insights</li>
              </ul>
              <button className="ivory-btn-subtle" onClick={() => onNavigate('explore')}>
                Start Exploring <ArrowRight size={14} />
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="ivory-principles">
        <div className="ivory-container">
          <motion.div className="ivory-principles-header" {...fadeUp(0)}>
            <h2>Built on Principle</h2>
          </motion.div>
          <div className="ivory-principle-grid">
            {[
              { icon: <ShieldCheck size={20} />, title: 'Official Truth', desc: 'Every recommendation is grounded in data from official college websites, NIRF rankings, and JoSAA records.' },
              { icon: <TrendingUp size={20} />, title: 'Opt-In Signals', desc: 'Student opinions from Reddit and YouTube are available but secondary — never mixed with official evidence.' },
              { icon: <Scale size={20} />, title: 'Honest Limits', desc: 'When evidence is insufficient, we abstain. Uncertain data is flagged transparently — no false confidence.' },
              { icon: <Award size={20} />, title: 'Earned Trust', desc: 'Citations for every claim. Source links for verification. Your decision is only as good as the evidence behind it.' },
            ].map((p, i) => (
              <motion.div className="ivory-principle" key={i} {...fadeUp(0.08 * i)}>
                <div className="ivory-principle-icon">{p.icon}</div>
                <h4>{p.title}</h4>
                <p>{p.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="ivory-cta-section">
        <div className="ivory-container">
          <motion.div className="ivory-cta-box" {...fadeUp(0)}>
            <div className="ivory-cta-ornament">
              <div className="ivory-ornament-line" />
              <Crown size={20} className="ivory-cta-crown" />
              <div className="ivory-ornament-line" />
            </div>
            <h2>Begin your college journey</h2>
            <p>Decisions of consequence deserve evidence of quality.</p>
            <button className="ivory-btn-gold" onClick={() => onNavigate('shortlist')}>
              Start Your Shortlist <ArrowRight size={14} />
            </button>
          </motion.div>
        </div>
      </section>

      <footer className="ivory-footer">
        <div className="ivory-container">
          <div className="ivory-footer-line" />
          <p className="ivory-footer-brand">CollegeCompass</p>
          <p className="ivory-footer-note">
            Data sourced from official college websites. Cutoff ranks are indicative and may vary.
            Always verify with official counselling portals before making decisions.
          </p>
        </div>
      </footer>
    </div>
  );
}
