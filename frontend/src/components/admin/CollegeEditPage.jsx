import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2 } from 'lucide-react';
import { getCollege, createCollege, updateCollege } from '../../api';
import './CollegeEditPage.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
};

const EMPTY_FORM = {
  college_id: '',
  college_name: '',
  institute_type: '',
  state: '',
  city: '',
  zone: '',
  location_type: '',
  entrance_exams: [],
  annual_tuition_lakh: '',
  annual_hostel_lakh: '',
  total_annual_cost_lakh: '',
  hostel_available: true,
  scholarship_notes: '',
  official_source_urls: [],
  tags: [],
  branch_cutoffs: [],
};

export default function CollegeEditPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isNew = id === 'new';

  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isNew) {
      getCollege(id).then(data => {
        setForm({
          ...EMPTY_FORM,
          ...data,
          annual_tuition_lakh: data.annual_tuition_lakh || '',
          annual_hostel_lakh: data.annual_hostel_lakh || '',
          total_annual_cost_lakh: data.total_annual_cost_lakh || '',
          branch_cutoffs: data.branch_cutoffs || [],
        });
      }).catch(err => setError(err.message)).finally(() => setLoading(false));
    }
  }, [id, isNew]);

  const updateField = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const handleTagAdd = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault();
      const tag = e.target.value.trim();
      if (!form.tags.includes(tag)) {
        updateField('tags', [...form.tags, tag]);
      }
      e.target.value = '';
    }
  };

  const handleTagRemove = (tag) => updateField('tags', form.tags.filter(t => t !== tag));

  const handleUrlAdd = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault();
      const url = e.target.value.trim();
      if (!form.official_source_urls.includes(url)) {
        updateField('official_source_urls', [...form.official_source_urls, url]);
      }
      e.target.value = '';
    }
  };

  const handleUrlRemove = (url) => updateField('official_source_urls', form.official_source_urls.filter(u => u !== url));

  const handleEntranceExamToggle = (exam) => {
    const exams = form.entrance_exams.includes(exam)
      ? form.entrance_exams.filter(e => e !== exam)
      : [...form.entrance_exams, exam];
    updateField('entrance_exams', exams);
  };

  const handleBranchChange = (index, field, value) => {
    const updated = [...form.branch_cutoffs];
    updated[index] = { ...updated[index], [field]: value };
    updateField('branch_cutoffs', updated);
  };

  const handleBranchAdd = () => {
    updateField('branch_cutoffs', [...form.branch_cutoffs, { branch: '', closing_rank: '', year: new Date().getFullYear() }]);
  };

  const handleBranchRemove = (index) => {
    updateField('branch_cutoffs', form.branch_cutoffs.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.college_id || !form.college_name) {
      setError('College ID and Name are required.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        annual_tuition_lakh: parseFloat(form.annual_tuition_lakh) || 0,
        annual_hostel_lakh: parseFloat(form.annual_hostel_lakh) || 0,
        total_annual_cost_lakh: parseFloat(form.total_annual_cost_lakh) || 0,
      };
      if (isNew) {
        await createCollege(payload);
      } else {
        await updateCollege(id, payload);
      }
      navigate('/admin/colleges');
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  if (loading) return <div className="admin-loading">Loading…</div>;

  return (
    <div className="admin-page">
      <motion.div className="admin-page-header" {...fadeUp}>
        <button className="btn btn-ghost" onClick={() => navigate('/admin/colleges')}>
          <ArrowLeft size={16} /> Back
        </button>
        <h1 className="admin-page-title">{isNew ? 'Add College' : `Edit: ${form.college_name}`}</h1>
      </motion.div>

      {error && <div className="admin-error">{error}</div>}

      <motion.form className="college-form" onSubmit={handleSubmit} {...fadeUp} transition={{ delay: 0.05 }}>
        <div className="form-section">
          <h3 className="form-section-title">Basic Info</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">College ID <span className="required">*</span></label>
              <input className="input" value={form.college_id} onChange={e => updateField('college_id', e.target.value)} placeholder="e.g. IIT-BOMBAY" disabled={!isNew} />
            </div>
            <div className="form-group">
              <label className="form-label">College Name <span className="required">*</span></label>
              <input className="input" value={form.college_name} onChange={e => updateField('college_name', e.target.value)} placeholder="e.g. IIT Bombay" />
            </div>
            <div className="form-group">
              <label className="form-label">Type</label>
              <select className="select" value={form.institute_type} onChange={e => updateField('institute_type', e.target.value)}>
                <option value="">Select type</option>
                <option value="IIT">IIT</option>
                <option value="NIT">NIT</option>
                <option value="IIIT">IIIT</option>
                <option value="GFTI">GFTI</option>
                <option value="State Govt">State Govt</option>
                <option value="Private">Private</option>
                <option value="Deemed University">Deemed University</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Location Type</label>
              <select className="select" value={form.location_type} onChange={e => updateField('location_type', e.target.value)}>
                <option value="">Select</option>
                <option value="Metro">Metro</option>
                <option value="Urban">Urban</option>
                <option value="Semi-Urban">Semi-Urban</option>
                <option value="Rural">Rural</option>
              </select>
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">State</label>
              <input className="input" value={form.state} onChange={e => updateField('state', e.target.value)} placeholder="e.g. Maharashtra" />
            </div>
            <div className="form-group">
              <label className="form-label">City</label>
              <input className="input" value={form.city} onChange={e => updateField('city', e.target.value)} placeholder="e.g. Mumbai" />
            </div>
            <div className="form-group">
              <label className="form-label">Zone</label>
              <select className="select" value={form.zone} onChange={e => updateField('zone', e.target.value)}>
                <option value="">Select zone</option>
                <option value="North">North</option>
                <option value="South">South</option>
                <option value="East">East</option>
                <option value="West">West</option>
                <option value="Central">Central</option>
                <option value="Northeast">Northeast</option>
              </select>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Cost & Hostel</h3>
          <div className="form-grid form-grid-3">
            <div className="form-group">
              <label className="form-label">Annual Tuition (₹ Lakh)</label>
              <input type="number" className="input" value={form.annual_tuition_lakh} onChange={e => updateField('annual_tuition_lakh', e.target.value)} step="0.1" />
            </div>
            <div className="form-group">
              <label className="form-label">Annual Hostel (₹ Lakh)</label>
              <input type="number" className="input" value={form.annual_hostel_lakh} onChange={e => updateField('annual_hostel_lakh', e.target.value)} step="0.1" />
            </div>
            <div className="form-group">
              <label className="form-label">Total Annual Cost (₹ Lakh)</label>
              <input type="number" className="input" value={form.total_annual_cost_lakh} onChange={e => updateField('total_annual_cost_lakh', e.target.value)} step="0.1" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Hostel Available</label>
            <div className="toggle-group" style={{ maxWidth: 200 }}>
              <button type="button" className={`toggle-item ${form.hostel_available ? 'active' : ''}`} onClick={() => updateField('hostel_available', true)}>Available</button>
              <button type="button" className={`toggle-item ${!form.hostel_available ? 'active' : ''}`} onClick={() => updateField('hostel_available', false)}>Not Available</button>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Scholarship Notes</label>
            <textarea className="textarea" value={form.scholarship_notes} onChange={e => updateField('scholarship_notes', e.target.value)} rows={2} placeholder="Any scholarship information…" />
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Entrance Exams</h3>
          <div className="chip-grid">
            {['JEE Main', 'JEE Advanced', 'GATE', 'CAT', 'MAT', 'COMEDK', 'WBJEE', 'MHT-CET', 'UPSEE', 'KEAM'].map(exam => (
              <button key={exam} type="button" className={`chip ${form.entrance_exams.includes(exam) ? 'selected' : ''}`} onClick={() => handleEntranceExamToggle(exam)}>{exam}</button>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Branch Cutoffs</h3>
          <div className="branch-cutoff-list">
            {form.branch_cutoffs.map((bc, i) => (
              <div key={i} className="branch-cutoff-row">
                <input className="input" value={bc.branch} onChange={e => handleBranchChange(i, 'branch', e.target.value)} placeholder="Branch (e.g. Computer Science)" />
                <input type="number" className="input" value={bc.closing_rank} onChange={e => handleBranchChange(i, 'closing_rank', parseInt(e.target.value))} placeholder="Closing Rank" style={{ width: 120 }} />
                <input type="number" className="input" value={bc.year || new Date().getFullYear()} onChange={e => handleBranchChange(i, 'year', parseInt(e.target.value))} placeholder="Year" style={{ width: 80 }} />
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => handleBranchRemove(i)}><Trash2 size={14} /></button>
              </div>
            ))}
            <button type="button" className="btn btn-ghost" onClick={handleBranchAdd}><Plus size={14} /> Add Branch</button>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Tags</h3>
          <div className="tag-input-container">
            <div className="tag-chips">
              {form.tags.map(tag => (
                <span key={tag} className="chip selected">
                  {tag} <button type="button" onClick={() => handleTagRemove(tag)}>×</button>
                </span>
              ))}
            </div>
            <input className="input" onKeyDown={handleTagAdd} placeholder="Type and press Enter to add tags…" />
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Official Source URLs</h3>
          <div className="url-input-container">
            <div className="url-list">
              {form.official_source_urls.map(url => (
                <div key={url} className="url-item">
                  <span>{url}</span>
                  <button type="button" onClick={() => handleUrlRemove(url)}>×</button>
                </div>
              ))}
            </div>
            <input className="input" onKeyDown={handleUrlAdd} placeholder="Type URL and press Enter…" />
          </div>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={() => navigate('/admin/colleges')}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            <Save size={16} /> {saving ? 'Saving…' : (isNew ? 'Create College' : 'Save Changes')}
          </button>
        </div>
      </motion.form>
    </div>
  );
}