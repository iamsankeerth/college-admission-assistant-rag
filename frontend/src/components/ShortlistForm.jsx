import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronDown, ChevronUp, MapPin, IndianRupee, Building2, GraduationCap, Hash, Home } from 'lucide-react';
import { EXAM_OPTIONS, BRANCH_OPTIONS, STATE_OPTIONS, ZONE_OPTIONS } from '../data';
import './ShortlistForm.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
};

export default function ShortlistForm({ onSubmit, isLoading }) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [form, setForm] = useState({
    entrance_exam: '',
    rank: '',
    preferred_branches: [],
    budget_lakh: '',
    preferred_states: [],
    preferred_zones: [],
    hostel_required: false,
    max_results: 5,
    include_rag_summary: true,
    include_public_signals: false,
  });

  const updateField = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const toggleArrayItem = (field, item) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(item)
        ? prev[field].filter(i => i !== item)
        : [...prev[field], item],
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.entrance_exam || !form.rank || !form.budget_lakh) return;
    onSubmit({
      ...form,
      rank: parseInt(form.rank, 10),
      budget_lakh: parseFloat(form.budget_lakh),
    });
  };

  const isValid = form.entrance_exam && form.rank && form.budget_lakh;

  return (
    <motion.section
      className="shortlist-form-section"
      variants={fadeUp}
      initial="initial"
      animate="animate"
    >
      <div className="container">
        <div className="form-header">
          <h2 className="gradient-text">Build Your Shortlist</h2>
          <p>Tell us about your profile. We'll find colleges that match — ranked by evidence.</p>
        </div>

        <form className="shortlist-form glass-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            {/* Exam */}
            <div className="form-group">
              <label className="form-label">
                <GraduationCap size={14} />
                Entrance Exam
                <span className="required">*</span>
              </label>
              <select
                id="entrance-exam"
                className="select"
                value={form.entrance_exam}
                onChange={(e) => updateField('entrance_exam', e.target.value)}
              >
                <option value="">Select your exam</option>
                {EXAM_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            {/* Rank */}
            <div className="form-group">
              <label className="form-label">
                <Hash size={14} />
                Your Rank
                <span className="required">*</span>
              </label>
              <input
                id="rank-input"
                type="number"
                className="input"
                placeholder="e.g. 4500"
                value={form.rank}
                onChange={(e) => updateField('rank', e.target.value)}
                min="1"
              />
            </div>

            {/* Budget */}
            <div className="form-group">
              <label className="form-label">
                <IndianRupee size={14} />
                Max Annual Budget (₹ Lakh)
                <span className="required">*</span>
              </label>
              <input
                id="budget-input"
                type="number"
                className="input"
                placeholder="e.g. 8"
                value={form.budget_lakh}
                onChange={(e) => updateField('budget_lakh', e.target.value)}
                min="0.5"
                step="0.5"
              />
            </div>

            {/* Results count */}
            <div className="form-group">
              <label className="form-label">
                <Building2 size={14} />
                Max Colleges to Show
              </label>
              <select
                id="max-results"
                className="select"
                value={form.max_results}
                onChange={(e) => updateField('max_results', parseInt(e.target.value))}
              >
                {[3, 5, 7, 10, 15].map(n => (
                  <option key={n} value={n}>{n} colleges</option>
                ))}
              </select>
            </div>
          </div>

          {/* Preferred Branches */}
          <div className="form-group form-full">
            <label className="form-label">
              <GraduationCap size={14} />
              Preferred Branches
              <span className="form-hint">(select all that apply)</span>
            </label>
            <div className="chip-grid">
              {BRANCH_OPTIONS.map(branch => (
                <button
                  key={branch}
                  type="button"
                  className={`chip ${form.preferred_branches.includes(branch) ? 'selected' : ''}`}
                  onClick={() => toggleArrayItem('preferred_branches', branch)}
                >
                  {branch}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Section */}
          <button
            type="button"
            className="advanced-toggle"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {showAdvanced ? 'Hide' : 'Show'} Location & Hostel Preferences
          </button>

          {showAdvanced && (
            <motion.div
              className="advanced-section"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            >
              {/* States */}
              <div className="form-group form-full">
                <label className="form-label">
                  <MapPin size={14} />
                  Preferred States
                </label>
                <div className="chip-grid">
                  {STATE_OPTIONS.map(state => (
                    <button
                      key={state}
                      type="button"
                      className={`chip ${form.preferred_states.includes(state) ? 'selected' : ''}`}
                      onClick={() => toggleArrayItem('preferred_states', state)}
                    >
                      {state}
                    </button>
                  ))}
                </div>
              </div>

              {/* Zones */}
              <div className="form-group form-full">
                <label className="form-label">
                  <MapPin size={14} />
                  Preferred Zones
                </label>
                <div className="chip-grid">
                  {ZONE_OPTIONS.map(zone => (
                    <button
                      key={zone}
                      type="button"
                      className={`chip ${form.preferred_zones.includes(zone) ? 'selected' : ''}`}
                      onClick={() => toggleArrayItem('preferred_zones', zone)}
                    >
                      {zone}
                    </button>
                  ))}
                </div>
              </div>

              {/* Hostel */}
              <div className="form-group">
                <label className="form-label">
                  <Home size={14} />
                  Hostel Required
                </label>
                <div className="toggle-group" style={{ maxWidth: 200 }}>
                  <button
                    type="button"
                    className={`toggle-item ${!form.hostel_required ? 'active' : ''}`}
                    onClick={() => updateField('hostel_required', false)}
                  >
                    Optional
                  </button>
                  <button
                    type="button"
                    className={`toggle-item ${form.hostel_required ? 'active' : ''}`}
                    onClick={() => updateField('hostel_required', true)}
                  >
                    Required
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          <hr className="divider-gradient" style={{ margin: 'var(--space-6) 0' }} />

          <div className="form-footer">
            <div className="form-footer-note">
              <span className="badge badge-official" style={{ fontSize: '0.625rem' }}>Official Data</span>
              <span className="form-footer-text">Results ranked using verified admission data</span>
            </div>
            <button
              id="shortlist-submit"
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={!isValid || isLoading}
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  Finding Colleges…
                </>
              ) : (
                <>
                  <Search size={18} />
                  Find My Colleges
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </motion.section>
  );
}
