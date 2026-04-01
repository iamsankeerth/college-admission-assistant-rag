import { motion } from 'framer-motion';
import { ArrowRight, Search, Compass, ShieldCheck, BookOpen, TrendingUp } from 'lucide-react';
import './Hero.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.08 } },
};

export default function Hero({ onNavigate }) {
  return (
    <section className="hero">
      <div className="container">
        <motion.div
          className="hero-content"
          variants={stagger}
          initial="initial"
          animate="animate"
        >
          <motion.div className="hero-label" variants={fadeUp}>
            <span className="badge badge-accent">
              <ShieldCheck size={12} />
              Official Evidence First
            </span>
          </motion.div>

          <motion.h1 className="hero-title" variants={fadeUp}>
            <span className="gradient-text">Make smarter</span>
            <br />
            <span className="accent-gradient-text">college decisions</span>
          </motion.h1>

          <motion.p className="hero-description" variants={fadeUp}>
            Shortlist engineering colleges based on your rank, exam, branch,
            budget, and location — backed by official evidence, not hearsay.
          </motion.p>

          <motion.div className="hero-actions" variants={fadeUp}>
            <button className="btn btn-primary btn-lg" onClick={() => onNavigate('shortlist')}>
              <Search size={18} />
              Start Shortlisting
              <ArrowRight size={16} />
            </button>
            <button className="btn btn-secondary btn-lg" onClick={() => onNavigate('explore')}>
              <Compass size={18} />
              Explore a College
            </button>
          </motion.div>

          <motion.div className="hero-trust-signals" variants={fadeUp}>
            <div className="trust-signal">
              <BookOpen size={14} />
              <span>Grounded in official sources</span>
            </div>
            <div className="trust-signal-divider" />
            <div className="trust-signal">
              <TrendingUp size={14} />
              <span>Student signals are opt-in</span>
            </div>
            <div className="trust-signal-divider" />
            <div className="trust-signal">
              <ShieldCheck size={14} />
              <span>Abstains when evidence is weak</span>
            </div>
          </motion.div>
        </motion.div>

        <motion.div
          className="hero-features"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
        >
          <FeatureCard
            icon={<Search size={20} />}
            title="Structured Shortlisting"
            description="Enter your exam, rank, branches, budget, and location. Get a ranked shortlist — not a vague chatbot response."
          />
          <FeatureCard
            icon={<ShieldCheck size={20} />}
            title="Trust-First Design"
            description="Official evidence is primary. Reddit and YouTube signals are secondary, clearly labeled, and always opt-in."
          />
          <FeatureCard
            icon={<TrendingUp size={20} />}
            title="Progressive Enrichment"
            description="Fast results first, then each card enriches with fit snapshot, cost details, outcomes, and campus insights."
          />
        </motion.div>
      </div>
    </section>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="feature-card card">
      <div className="card-edge-highlight" />
      <div className="feature-icon">{icon}</div>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-desc">{description}</p>
    </div>
  );
}
