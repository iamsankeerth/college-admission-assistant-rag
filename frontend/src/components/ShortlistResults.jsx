import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, GitCompare } from 'lucide-react';
import CollegeCard from './CollegeCard';
import FeedbackForm from './FeedbackForm';
import './ShortlistResults.css';

export default function ShortlistResults({ data, profile, onBack, onExplore, onCompare }) {
  const recs = data?.recommendations || [];
  const [selected, setSelected] = useState([]);

  useEffect(() => {
    if (data && profile) {
      import('../storage').then(m => m.saveShortlist(profile, data));
    }
  }, [data, profile]);

  const toggleSelect = (collegeId) => {
    setSelected(prev =>
      prev.includes(collegeId)
        ? prev.filter(id => id !== collegeId)
        : prev.length < 3
          ? [...prev, collegeId]
          : prev
    );
  };

  const selectedColleges = recs.filter(c => selected.includes(c.college_id));

  return (
    <section className="results-section">
      <div className="container">
        <motion.div
          className="results-header"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <button className="btn btn-ghost" onClick={onBack}>
            <ArrowLeft size={16} />
            Modify Search
          </button>

          <div className="results-summary">
            <h2 className="gradient-text">Your Shortlist</h2>
            <p className="results-meta">
              {recs.length} college{recs.length !== 1 ? 's' : ''} matched
              {data?.filtered_out_count > 0 && (
                <span className="results-filtered"> · {data.filtered_out_count} filtered out</span>
              )}
            </p>
          </div>

          <div className="results-header-actions">
            <div className="results-profile-summary">
              <span className="badge badge-neutral">{profile?.entrance_exam}</span>
              <span className="badge badge-neutral">Rank {profile?.rank?.toLocaleString()}</span>
              <span className="badge badge-neutral">≤₹{profile?.budget_lakh}L</span>
            </div>
            {selected.length >= 2 && (
              <motion.button
                className="btn btn-primary"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                onClick={() => onCompare?.(selectedColleges)}
              >
                <GitCompare size={16} />
                Compare {selected.length} Colleges
              </motion.button>
            )}
          </div>
        </motion.div>

        {selected.length > 0 && selected.length < 2 && (
          <motion.div
            className="compare-hint"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <span>Select at least {2 - selected.length} more college{2 - selected.length > 1 ? 's' : ''} to compare</span>
          </motion.div>
        )}

        <motion.div
          className="results-legend"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <div className="legend-title label">Fit Categories</div>
          <div className="legend-items">
            <LegendItem color="var(--fit-safe)" label="Safe — high chance" />
            <LegendItem color="var(--fit-moderate)" label="Moderate — competitive" />
            <LegendItem color="var(--fit-ambitious)" label="Ambitious — tight odds" />
            <LegendItem color="var(--fit-stretch)" label="Stretch — aspirational" />
          </div>
          {selected.length > 0 && (
            <div className="legend-selected-count">
              {selected.length}/3 selected for comparison
            </div>
          )}
        </motion.div>

        <div className="results-cards">
          {recs.map((college, i) => (
            <CollegeCard
              key={college.college_id}
              college={college}
              rank={i}
              onExplore={onExplore}
              selected={selected.includes(college.college_id)}
              onToggleSelect={() => toggleSelect(college.college_id)}
            />
          ))}
        </div>

        {data?.notes?.length > 0 && (
          <motion.div
            className="results-notes"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            {data.notes.map((note, i) => (
              <p key={i} className="results-note">{note}</p>
            ))}
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <FeedbackForm
            query={`${profile?.entrance_exam} rank ${profile?.rank} ≤₹${profile?.budget_lakh}L`}
            recommendedColleges={recs.map(c => c.college_name)}
          />
        </motion.div>
      </div>
    </section>
  );
}

function LegendItem({ color, label }) {
  return (
    <div className="legend-item">
      <span className="legend-dot" style={{ background: color }} />
      <span>{label}</span>
    </div>
  );
}
