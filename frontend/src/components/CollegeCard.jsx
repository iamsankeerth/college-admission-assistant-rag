import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, IndianRupee, GraduationCap, ChevronDown, ChevronUp,
  ExternalLink, ShieldCheck, AlertTriangle, TrendingUp,
  Building2, BookOpen, Briefcase, Home, Star, Target, Zap, MessageCircle
} from 'lucide-react';
import { useMouseSpotlight } from '../hooks/useMouseSpotlight';
import './CollegeCard.css';

const FIT_CONFIG = {
  safe: { color: 'var(--fit-safe)', label: 'Safe', icon: <ShieldCheck size={14} /> },
  moderate: { color: 'var(--fit-moderate)', label: 'Moderate', icon: <Target size={14} /> },
  ambitious: { color: 'var(--fit-ambitious)', label: 'Ambitious', icon: <TrendingUp size={14} /> },
  stretch: { color: 'var(--fit-stretch)', label: 'Stretch', icon: <Zap size={14} /> },
};

export default function CollegeCard({ college, rank: cardRank, onExplore }) {
  const [expanded, setExpanded] = useState(false);
  const [showSignals, setShowSignals] = useState(false);
  const { onMouseMove, spotlightStyle } = useMouseSpotlight();
  const fit = FIT_CONFIG[college.fit_bucket] || FIT_CONFIG.moderate;
  const enrichment = college.enrichment;

  return (
    <motion.div
      className="college-card card"
      onMouseMove={onMouseMove}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: cardRank * 0.08 }}
    >
      {/* Spotlight overlay */}
      <div className="card-spotlight" style={spotlightStyle} />
      <div className="card-edge-highlight" />

      {/* Header */}
      <div className="cc-header">
        <div className="cc-rank-badge">#{cardRank + 1}</div>
        <div className="cc-header-info">
          <div className="cc-title-row">
            <h3 className="cc-name">{college.college_name}</h3>
            <span className="badge badge-neutral">{college.institute_type}</span>
          </div>
          <div className="cc-meta">
            <span className="cc-meta-item">
              <MapPin size={13} /> {college.city}, {college.state}
            </span>
            {college.matched_branch && (
              <span className="cc-meta-item">
                <GraduationCap size={13} /> {college.matched_branch}
              </span>
            )}
          </div>
        </div>
        <div className="cc-score-block">
          <div className="cc-score" style={{ color: fit.color }}>{(college.final_score * 100).toFixed(0)}</div>
          <div className="cc-score-label label">Score</div>
        </div>
      </div>

      {/* Fit & Cost Row */}
      <div className="cc-fit-row">
        <div className="cc-fit-badge" style={{ '--fit-color': fit.color }}>
          {fit.icon}
          <span>{fit.label} Fit</span>
        </div>
        <div className="cc-cost">
          <IndianRupee size={13} />
          <span>₹{college.annual_cost_lakh}L/year</span>
        </div>
        {college.hostel_available && (
          <div className="cc-hostel-badge">
            <Home size={13} />
            <span>Hostel</span>
          </div>
        )}
      </div>

      {/* Reasons */}
      <div className="cc-reasons">
        {college.reasons.slice(0, expanded ? undefined : 2).map((reason, i) => (
          <div key={i} className="cc-reason">
            <span className="cc-reason-dot" style={{ background: fit.color }} />
            <span>{reason}</span>
          </div>
        ))}
      </div>

      {/* Score Breakdown Mini */}
      {college.score_breakdown && (
        <div className="cc-score-bars">
          <ScoreBar label="Rank Fit" value={college.score_breakdown.rank_score} color={fit.color} />
          <ScoreBar label="Affordability" value={college.score_breakdown.affordability_score} color="var(--trust-official)" />
          <ScoreBar label="Location" value={college.score_breakdown.location_score} color="var(--accent)" />
        </div>
      )}

      {/* Expand Toggle */}
      <button className="cc-expand-toggle" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        {expanded ? 'Show Less' : 'View Details'}
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && enrichment && (
          <motion.div
            className="cc-expanded"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <hr className="divider-gradient" />

            {/* Fit Snapshot */}
            {enrichment.fit_snapshot && (
              <EnrichmentSection
                icon={<Target size={16} />}
                title="Fit Snapshot"
                badge={<span className="badge badge-official">Official</span>}
              >
                {enrichment.fit_snapshot.closing_rank && (
                  <div className="cc-stat-row">
                    <span className="cc-stat-label">Closing Rank</span>
                    <span className="cc-stat-value">{enrichment.fit_snapshot.closing_rank.toLocaleString()}</span>
                  </div>
                )}
                {enrichment.fit_snapshot.fit_notes?.map((note, i) => (
                  <div key={i} className="cc-fit-note">
                    {note.toLowerCase().includes('evidence confidence') || note.toLowerCase().includes('edge') ? (
                      <AlertTriangle size={13} style={{ color: 'var(--trust-student)', flexShrink: 0 }} />
                    ) : (
                      <ShieldCheck size={13} style={{ color: 'var(--trust-official)', flexShrink: 0 }} />
                    )}
                    <span>{note}</span>
                  </div>
                ))}
              </EnrichmentSection>
            )}

            {/* Cost & Admissions */}
            {enrichment.cost_and_admissions && (
              <EnrichmentSection
                icon={<IndianRupee size={16} />}
                title="Cost & Admissions"
                badge={<span className="badge badge-official">Official</span>}
              >
                <div className="cc-stats-grid">
                  <div className="cc-stat-row">
                    <span className="cc-stat-label">Annual Cost</span>
                    <span className="cc-stat-value">₹{enrichment.cost_and_admissions.annual_cost_lakh}L</span>
                  </div>
                  <div className="cc-stat-row">
                    <span className="cc-stat-label">Counselling</span>
                    <span className="cc-stat-value">{enrichment.cost_and_admissions.counselling_body}</span>
                  </div>
                </div>
                {enrichment.cost_and_admissions.admission_process && (
                  <p className="cc-enrichment-text">{enrichment.cost_and_admissions.admission_process}</p>
                )}
                {enrichment.cost_and_admissions.scholarship_notes && (
                  <div className="cc-scholarship-note">
                    <Star size={13} style={{ color: 'var(--trust-student)', flexShrink: 0 }} />
                    <span>{enrichment.cost_and_admissions.scholarship_notes}</span>
                  </div>
                )}
                {enrichment.cost_and_admissions.official_source_url && (
                  <a href={enrichment.cost_and_admissions.official_source_url} target="_blank" rel="noopener noreferrer" className="cc-source-link">
                    <ExternalLink size={13} />
                    Official Admissions Page
                  </a>
                )}
              </EnrichmentSection>
            )}

            {/* Outcomes & Campus */}
            {enrichment.outcomes_and_campus && (
              <EnrichmentSection
                icon={<Briefcase size={16} />}
                title="Outcomes & Campus"
                badge={<span className="badge badge-official">Official</span>}
              >
                {enrichment.outcomes_and_campus.placement_summary && (
                  <div className="cc-enrichment-block">
                    <div className="cc-enrichment-block-label label">
                      <TrendingUp size={12} /> Placements
                    </div>
                    <p className="cc-enrichment-text">{enrichment.outcomes_and_campus.placement_summary}</p>
                  </div>
                )}
                {enrichment.outcomes_and_campus.roi_indicator && (
                  <div className="cc-stat-row">
                    <span className="cc-stat-label">ROI</span>
                    <span className="cc-stat-value cc-roi-value">{enrichment.outcomes_and_campus.roi_indicator}</span>
                  </div>
                )}
                <div className="cc-campus-grid">
                  {enrichment.outcomes_and_campus.lab_facilities && (
                    <CampusItem icon={<BookOpen size={13} />} label="Labs" value={enrichment.outcomes_and_campus.lab_facilities} />
                  )}
                  {enrichment.outcomes_and_campus.startup_culture && (
                    <CampusItem icon={<Zap size={13} />} label="Startups" value={enrichment.outcomes_and_campus.startup_culture} />
                  )}
                  {enrichment.outcomes_and_campus.extracurriculars && (
                    <CampusItem icon={<Star size={13} />} label="Activities" value={enrichment.outcomes_and_campus.extracurriculars} />
                  )}
                </div>
              </EnrichmentSection>
            )}

            {/* Official Sources */}
            {college.official_source_urls?.length > 0 && (
              <div className="cc-sources">
                <div className="cc-sources-label label">
                  <ShieldCheck size={12} /> Official Sources
                </div>
                {college.official_source_urls.map((url, i) => (
                  <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="cc-source-link">
                    <ExternalLink size={13} />
                    {new URL(url).hostname.replace('www.', '')}
                  </a>
                ))}
              </div>
            )}

            {/* Public Signals Toggle */}
            <div className="cc-signals-section">
              <button
                className="cc-signals-toggle"
                onClick={() => setShowSignals(!showSignals)}
              >
                <MessageCircle size={14} />
                {showSignals ? 'Hide' : 'Show'} Student Signals
                <span className="badge badge-student" style={{ fontSize: '0.5625rem' }}>
                  Unverified
                </span>
              </button>
              {showSignals && (
                <motion.div
                  className="cc-signals-content"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="cc-signals-disclaimer">
                    <AlertTriangle size={14} />
                    <span>{college.public_signals_disclaimer || 'Student signals are crowdsourced and unverified. Treat as directional only.'}</span>
                  </div>
                  <p className="cc-enrichment-text" style={{ color: 'var(--fg-dim)' }}>
                    Public signals from Reddit and YouTube will appear here when available. Click "Explore" for a deeper dive.
                  </p>
                </motion.div>
              )}
            </div>

            {/* Explore CTA */}
            <button
              className="btn btn-secondary cc-explore-btn"
              onClick={() => onExplore?.(college.college_name)}
            >
              <Building2 size={16} />
              Explore {college.college_name} in Detail
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function EnrichmentSection({ icon, title, badge, children }) {
  return (
    <div className="cc-enrichment-section">
      <div className="cc-enrichment-header">
        <div className="cc-enrichment-title">
          {icon}
          <span>{title}</span>
        </div>
        {badge}
      </div>
      <div className="cc-enrichment-body">{children}</div>
    </div>
  );
}

function ScoreBar({ label, value, color }) {
  return (
    <div className="cc-score-bar-item">
      <div className="cc-score-bar-label">{label}</div>
      <div className="cc-score-bar-track">
        <motion.div
          className="cc-score-bar-fill"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(value * 100)}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
        />
      </div>
      <div className="cc-score-bar-value">{Math.round(value * 100)}</div>
    </div>
  );
}

function CampusItem({ icon, label, value }) {
  return (
    <div className="cc-campus-item">
      <div className="cc-campus-item-label">
        {icon} {label}
      </div>
      <p className="cc-campus-item-value">{value}</p>
    </div>
  );
}
