import { motion } from 'framer-motion';
import { ArrowLeft, Filter, RefreshCw, ChevronDown } from 'lucide-react';
import CollegeCard from './CollegeCard';
import './ShortlistResults.css';

export default function ShortlistResults({ data, profile, onBack, onExplore }) {
  const recs = data?.recommendations || [];

  return (
    <section className="results-section">
      <div className="container">
        {/* Results Header */}
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

          <div className="results-profile-summary">
            <span className="badge badge-neutral">{profile?.entrance_exam}</span>
            <span className="badge badge-neutral">Rank {profile?.rank?.toLocaleString()}</span>
            <span className="badge badge-neutral">≤₹{profile?.budget_lakh}L</span>
          </div>
        </motion.div>

        {/* Legend */}
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
        </motion.div>

        {/* Cards */}
        <div className="results-cards">
          {recs.map((college, i) => (
            <CollegeCard
              key={college.college_id}
              college={college}
              rank={i}
              onExplore={onExplore}
            />
          ))}
        </div>

        {/* Notes */}
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
