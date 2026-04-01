import { motion } from 'framer-motion';
import {
  ArrowRight, Search, Compass, ShieldCheck, BookOpen,
  TrendingUp, Award, Users, BarChart3, GraduationCap,
  ChevronRight, Star, MapPin, IndianRupee
} from 'lucide-react';
import './MeridianLanding.css';

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94], delay },
});

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } },
};

export default function MeridianLanding({ onNavigate }) {
  return (
    <div className="meridian">
      {/* Navigation */}
      <nav className="meridian-nav">
        <div className="meridian-container">
          <div className="meridian-nav-inner">
            <div className="meridian-brand">
              <div className="meridian-logo-mark">
                <GraduationCap size={18} strokeWidth={1.8} />
              </div>
              <span className="meridian-logo-text">
                College<span className="meridian-logo-accent">Compass</span>
              </span>
            </div>
            <div className="meridian-nav-links">
              <button className="meridian-nav-link" onClick={() => onNavigate('shortlist')}>
                Shortlist
              </button>
              <button className="meridian-nav-link" onClick={() => onNavigate('explore')}>
                Explore
              </button>
              <span className="meridian-nav-badge">
                <span className="meridian-badge-dot" />
                Evidence-First
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="meridian-hero">
        <div className="meridian-container">
          <motion.div className="meridian-hero-content" {...stagger} initial="initial" animate="animate">
            <motion.div className="meridian-hero-overline" {...fadeUp(0)}>
              <BookOpen size={14} />
              Backed by official college data — not opinions
            </motion.div>

            <motion.h1 className="meridian-hero-title" {...fadeUp(0.1)}>
              Your college decision
              <br />
              deserves <em>better evidence.</em>
            </motion.h1>

            <motion.p className="meridian-hero-subtitle" {...fadeUp(0.2)}>
              CollegeCompass helps you shortlist Indian engineering colleges based on
              your rank, exam, branch preference, budget, and location — with every recommendation
              grounded in verified official sources.
            </motion.p>

            <motion.div className="meridian-hero-ctas" {...fadeUp(0.3)}>
              <button className="meridian-btn-primary" onClick={() => onNavigate('shortlist')}>
                <Search size={16} />
                Start Shortlisting
                <ArrowRight size={14} />
              </button>
              <button className="meridian-btn-secondary" onClick={() => onNavigate('explore')}>
                <Compass size={16} />
                Explore a College
              </button>
            </motion.div>

            <motion.div className="meridian-hero-proof" {...fadeUp(0.4)}>
              <div className="meridian-proof-item">
                <ShieldCheck size={14} />
                <span>Official sources only</span>
              </div>
              <div className="meridian-proof-divider" />
              <div className="meridian-proof-item">
                <TrendingUp size={14} />
                <span>Student signals opt-in</span>
              </div>
              <div className="meridian-proof-divider" />
              <div className="meridian-proof-item">
                <Award size={14} />
                <span>Abstains on weak evidence</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Editorial Preview Card */}
          <motion.div className="meridian-preview" {...fadeUp(0.5)}>
            <div className="meridian-preview-header">
              <span className="meridian-preview-label">Sample Shortlist Result</span>
              <span className="meridian-preview-badge">OFFICIAL</span>
            </div>
            <div className="meridian-preview-college">
              <div className="meridian-preview-rank">1</div>
              <div className="meridian-preview-info">
                <h3>IIT Hyderabad</h3>
                <p>Computer Science & Engineering · Telangana</p>
              </div>
              <div className="meridian-preview-fit safe">Safe Fit</div>
            </div>
            <div className="meridian-preview-metrics">
              <div className="meridian-metric">
                <span className="meridian-metric-label">Score</span>
                <span className="meridian-metric-value">0.95</span>
              </div>
              <div className="meridian-metric">
                <span className="meridian-metric-label">Annual Cost</span>
                <span className="meridian-metric-value">₹4.5L</span>
              </div>
              <div className="meridian-metric">
                <span className="meridian-metric-label">Closing Rank</span>
                <span className="meridian-metric-value">~5,200</span>
              </div>
              <div className="meridian-metric">
                <span className="meridian-metric-label">Median CTC</span>
                <span className="meridian-metric-value">₹22 LPA</span>
              </div>
            </div>
            <div className="meridian-preview-evidence">
              <div className="meridian-evidence-bar" />
              <p>Rank comfortably within closing cutoff range. Strong CSE program with AI/ML research focus. Located in preferred zone.</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="meridian-how">
        <div className="meridian-container">
          <motion.div className="meridian-section-header" {...fadeUp(0)}>
            <h2>How CollegeCompass works</h2>
            <p>Three steps from confusion to clarity</p>
          </motion.div>

          <div className="meridian-steps">
            {[
              {
                num: '01',
                icon: <Users size={22} />,
                title: 'Tell us about yourself',
                desc: 'Enter your entrance exam, rank, preferred branches, budget, states, and hostel preference. We build your profile.'
              },
              {
                num: '02',
                icon: <BarChart3 size={22} />,
                title: 'We rank & enrich',
                desc: 'Fast first pass returns ranked colleges. Then progressive enrichment adds fit snapshot, cost, outcomes, and campus details.'
              },
              {
                num: '03',
                icon: <ShieldCheck size={22} />,
                title: 'You decide with evidence',
                desc: 'Every recommendation cites official sources. Student signals are secondary and opt-in. Uncertain data is flagged transparently.'
              }
            ].map((step, i) => (
              <motion.div className="meridian-step" key={i} {...fadeUp(0.1 * i)}>
                <div className="meridian-step-num">{step.num}</div>
                <div className="meridian-step-icon">{step.icon}</div>
                <h3>{step.title}</h3>
                <p>{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Two Journeys */}
      <section className="meridian-journeys">
        <div className="meridian-container">
          <div className="meridian-journey-grid">
            <motion.div className="meridian-journey-card primary" {...fadeUp(0)}>
              <div className="meridian-journey-label">Primary Journey</div>
              <Search size={28} />
              <h3>Shortlist Colleges</h3>
              <p>Enter your profile, get a ranked shortlist of engineering colleges optimized for your rank, budget, branch, and location. Each card enriches progressively with official data.</p>
              <ul className="meridian-journey-features">
                <li><ChevronRight size={12} /> Rank-based matching</li>
                <li><ChevronRight size={12} /> Budget & location filters</li>
                <li><ChevronRight size={12} /> Progressive enrichment</li>
                <li><ChevronRight size={12} /> Official evidence citations</li>
              </ul>
              <button className="meridian-btn-primary" onClick={() => onNavigate('shortlist')}>
                Start Shortlisting <ArrowRight size={14} />
              </button>
            </motion.div>

            <motion.div className="meridian-journey-card secondary" {...fadeUp(0.15)}>
              <div className="meridian-journey-label">Deep Dive</div>
              <Compass size={28} />
              <h3>Explore a College</h3>
              <p>Already have a college in mind? Search and explore official summaries, admissions, fees, placements, campus life, and ask follow-up questions.</p>
              <ul className="meridian-journey-features">
                <li><ChevronRight size={12} /> Official verified summary</li>
                <li><ChevronRight size={12} /> Admissions & counselling</li>
                <li><ChevronRight size={12} /> Fee & hostel details</li>
                <li><ChevronRight size={12} /> Placement & campus data</li>
              </ul>
              <button className="meridian-btn-secondary" onClick={() => onNavigate('explore')}>
                Explore Now <ArrowRight size={14} />
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="meridian-trust">
        <div className="meridian-container">
          <div className="meridian-trust-grid">
            {[
              { icon: <ShieldCheck size={20} />, label: 'Official', desc: 'College websites, NIRF, JoSAA data' },
              { icon: <Star size={20} />, label: 'Verified', desc: 'Every claim linked to its source' },
              { icon: <MapPin size={20} />, label: 'Personalized', desc: 'Results custom-fit to your rank & location' },
              { icon: <IndianRupee size={20} />, label: 'Transparent', desc: 'Full cost breakdown with scholarship info' },
            ].map((item, i) => (
              <div className="meridian-trust-item" key={i}>
                <div className="meridian-trust-icon">{item.icon}</div>
                <strong>{item.label}</strong>
                <span>{item.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="meridian-footer">
        <div className="meridian-container">
          <div className="meridian-footer-content">
            <p className="meridian-footer-brand">CollegeCompass</p>
            <p className="meridian-footer-note">
              Data sourced from official college websites. Cutoff ranks are indicative and may vary by year, category, and round.
              Always verify with official counselling portals before making decisions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
