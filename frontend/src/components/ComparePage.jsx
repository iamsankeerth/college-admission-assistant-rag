import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, GitCompare, IndianRupee, GraduationCap,
  MapPin, TrendingUp, Home, Award, ShieldCheck
} from 'lucide-react';
import './ComparePage.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
};

const COMPARE_FIELDS = [
  { key: 'institute_type', label: 'Type', icon: null, highlight: null },
  { key: 'city', label: 'City', icon: <MapPin size={13} />, highlight: null },
  { key: 'zone', label: 'Zone', icon: <MapPin size={13} />, highlight: null },
  { key: 'annual_cost_lakh', label: 'Annual Cost', icon: <IndianRupee size={13} />, highlight: 'lowest', prefix: '₹', suffix: 'L' },
  { key: 'hostel_available', label: 'Hostel', icon: <Home size={13} />, highlight: null, bool: true },
  {
    key: 'matched_branch', label: 'Branch', icon: <GraduationCap size={13} />, highlight: null,
  },
  {
    key: 'closing_rank', label: 'Closing Rank', icon: <Award size={13} />, highlight: 'lowest',
  },
  {
    key: 'median_ctc', label: 'Median CTC', icon: <TrendingUp size={13} />, highlight: 'highest',
  },
  { key: 'roi', label: 'ROI', icon: <TrendingUp size={13} />, highlight: null },
  { key: 'placement_pct', label: 'Placement %', icon: <ShieldCheck size={13} />, highlight: 'highest' },
  { key: 'fit_bucket', label: 'Fit', icon: null, highlight: null },
];

export default function ComparePage({ colleges, profile, onBack }) {
  const recs = colleges || [];

  if (recs.length === 0) {
    return (
      <section className="compare-section">
        <div className="ivory-container">
          <motion.div className="compare-empty" {...fadeUp}>
            <GitCompare size={40} style={{ color: 'var(--fg-dim)' }} />
            <h2>No colleges to compare</h2>
            <p>Select colleges from your shortlist to compare them side by side.</p>
            <button className="btn btn-primary" onClick={onBack}>
              <ArrowLeft size={16} /> Back to Shortlist
            </button>
          </motion.div>
        </div>
      </section>
    );
  }

  const collegesToCompare = recs.slice(0, 3);

  const getValue = (college, key) => {
    const enrichment = college.enrichment || {};
    switch (key) {
      case 'annual_cost_lakh': return college.annual_cost_lakh ?? enrichment.cost_and_admissions?.annual_cost_lakh ?? null;
      case 'hostel_available': return college.hostel_available ?? enrichment.cost_and_admissions?.hostel_available ?? null;
      case 'matched_branch': return college.matched_branch || '—';
      case 'closing_rank': return enrichment.fit_snapshot?.closing_rank || null;
      case 'median_ctc': return extractMedianCTC(enrichment.outcomes_and_campus?.placement_summary);
      case 'roi': return enrichment.outcomes_and_campus?.roi_indicator || '—';
      case 'placement_pct': return extractPlacementPct(enrichment.outcomes_and_campus?.placement_summary);
      case 'fit_bucket': return college.fit_bucket || '—';
      default: return college[key] || '—';
    }
  };

  const getNumeric = (college, key) => {
    const val = getValue(college, key);
    if (typeof val === 'number') return val;
    if (typeof val === 'string') return parseFloat(val.replace(/[^0-9.]/g, '')) || null;
    return null;
  };

  const findHighlight = (key, highlight) => {
    if (!highlight || !['lowest', 'highest'].includes(highlight)) return null;
    const vals = collegesToCompare.map(c => ({ c, v: getNumeric(c, key) })).filter(x => x.v !== null);
    if (vals.length < 2) return null;
    const target = highlight === 'lowest' ? Math.min(...vals.map(x => x.v)) : Math.max(...vals.map(x => x.v));
    return target;
  };

  const FIT_COLORS = {
    safe: 'var(--fit-safe)',
    moderate: 'var(--fit-moderate)',
    ambitious: 'var(--fit-ambitious)',
    stretch: 'var(--fit-stretch)',
  };

  const formatVal = (college, key, val) => {
    if (val === null || val === undefined || val === '—') return '—';
    if (key === 'annual_cost_lakh') return `₹${val}L`;
    if (key === 'closing_rank') return `~${val.toLocaleString()}`;
    if (key === 'median_ctc') return typeof val === 'string' ? val : `₹${val} LPA`;
    if (key === 'placement_pct') return typeof val === 'string' ? val : `${val}%`;
    if (key === 'hostel_available') return val ? 'Yes' : 'No';
    if (key === 'fit_bucket') {
      const color = FIT_COLORS[val] || 'var(--fg-muted)';
      return val.charAt(0).toUpperCase() + val.slice(1);
    }
    return String(val);
  };

  return (
    <section className="compare-section">
      <div className="ivory-container">
        {/* Header */}
        <motion.div className="compare-header" {...fadeUp}>
          {onBack && (
            <button className="btn btn-ghost" onClick={onBack}>
              <ArrowLeft size={16} /> Back
            </button>
          )}
          <div className="compare-title-row">
            <GitCompare size={22} style={{ color: 'var(--accent)' }} />
            <h2>Compare Colleges</h2>
          </div>
          {profile && (
            <p className="compare-profile-note">
              Comparing top {collegesToCompare.length} matches for {profile.entrance_exam} rank {profile.rank?.toLocaleString()}
            </p>
          )}
        </motion.div>

        {/* Comparison Table */}
        <motion.div className="compare-table-wrapper" {...fadeUp} transition={{ delay: 0.1 }}>
          <table className="compare-table">
            <thead>
              <tr>
                <th className="compare-th-label">Criterion</th>
                {collegesToCompare.map((c) => (
                  <th key={c.college_id} className="compare-th-college">
                    <div className="compare-college-name">{c.college_name}</div>
                    <div className="compare-college-type">{c.institute_type}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPARE_FIELDS.map(({ key, label, icon, highlight, bool }) => {
                const targetVal = findHighlight(key, highlight);
                return (
                  <tr key={key} className="compare-row">
                    <td className="compare-td-label">
                      {icon && <span className="compare-label-icon">{icon}</span>}
                      {label}
                    </td>
                    {collegesToCompare.map((college) => {
                      const rawVal = getValue(college, key);
                      const numVal = getNumeric(college, key);
                      const isHighlighted = targetVal !== null && numVal !== null && numVal === targetVal;
                      const isFit = key === 'fit_bucket';
                      return (
                        <td
                          key={college.college_id}
                          className={`compare-td-value ${isHighlighted ? 'compare-highlighted' : ''} ${isFit ? 'compare-fit-cell' : ''}`}
                          style={isFit ? { color: FIT_COLORS[rawVal] || 'var(--fg)' } : {}}
                        >
                          {formatVal(college, key, rawVal)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </motion.div>

        {/* Fit Legend */}
        <motion.div className="compare-legend" {...fadeUp} transition={{ delay: 0.2 }}>
          <div className="compare-legend-title label">Fit Categories</div>
          <div className="compare-legend-items">
            {Object.entries(FIT_COLORS).map(([fit, color]) => (
              <div key={fit} className="compare-legend-item">
                <span className="compare-legend-dot" style={{ background: color }} />
                <span>{fit.charAt(0).toUpperCase() + fit.slice(1)}</span>
              </div>
            ))}
            <div className="compare-legend-note">Green = best value in category</div>
          </div>
        </motion.div>

        {/* Disclaimer */}
        <motion.div className="compare-disclaimer" {...fadeUp} transition={{ delay: 0.3 }}>
          <p>Data sourced from official college websites. Figures are indicative and may vary by year, category, and round. Always verify with official counselling portals.</p>
        </motion.div>
      </div>
    </section>
  );
}

function extractMedianCTC(text) {
  if (!text) return null;
  const match = text.match(/median CTC [:₹]?\s*([\d.]+)\s*LPA/i);
  return match ? parseFloat(match[1]) : null;
}

function extractPlacementPct(text) {
  if (!text) return null;
  const match = text.match(/(\d+)%\s*placement/i);
  return match ? parseInt(match[1]) : null;
}
