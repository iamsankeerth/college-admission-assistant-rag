import { motion } from 'framer-motion';
import { Loader2, Search, Database, Brain, CheckCircle2 } from 'lucide-react';
import './LoadingState.css';

const STEPS = [
  { icon: <Search size={16} />, label: 'Analyzing your profile', description: 'Matching exam, rank, and preferences' },
  { icon: <Database size={16} />, label: 'Querying official records', description: 'Retrieving verified admission data' },
  { icon: <Brain size={16} />, label: 'Scoring and ranking', description: 'Computing fit, cost, and location scores' },
  { icon: <CheckCircle2 size={16} />, label: 'Preparing your shortlist', description: 'Building enriched college cards' },
];

export default function LoadingState({ progress = 0 }) {
  const activeStep = Math.min(Math.floor(progress / 25), 3);

  return (
    <section className="loading-section">
      <div className="container">
        <motion.div
          className="loading-container glass-panel"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="loading-header">
            <div className="loading-spinner">
              <Loader2 size={24} className="spin-icon" />
            </div>
            <h3>Finding your colleges…</h3>
            <p>This usually takes a few seconds</p>
          </div>

          <div className="progress-bar" style={{ maxWidth: 400, margin: '0 auto' }}>
            <motion.div
              className="progress-bar-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>

          <div className="loading-steps">
            {STEPS.map((step, i) => (
              <motion.div
                key={i}
                className={`loading-step ${i < activeStep ? 'done' : i === activeStep ? 'active' : 'pending'}`}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="loading-step-icon">
                  {i < activeStep ? <CheckCircle2 size={16} /> : step.icon}
                </div>
                <div className="loading-step-text">
                  <span className="loading-step-label">{step.label}</span>
                  <span className="loading-step-desc">{step.description}</span>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Skeleton Cards Preview */}
          <div className="loading-skeletons">
            {[0, 1, 2].map(i => (
              <motion.div
                key={i}
                className="skeleton-card"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 + i * 0.1, duration: 0.4 }}
              >
                <div className="skeleton-header">
                  <div className="skeleton" style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)' }} />
                  <div style={{ flex: 1 }}>
                    <div className="skeleton" style={{ width: '60%', height: 16, marginBottom: 8 }} />
                    <div className="skeleton" style={{ width: '40%', height: 12 }} />
                  </div>
                  <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)' }} />
                </div>
                <div className="skeleton" style={{ width: '100%', height: 8, marginTop: 16 }} />
                <div className="skeleton" style={{ width: '80%', height: 8, marginTop: 8 }} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
