import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Building2, Plus, Search, Pencil, Trash2 } from 'lucide-react';
import { getColleges, deleteCollege } from '../../api';
import './CollegeListPage.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
};

export default function CollegeListPage() {
  const navigate = useNavigate();
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    loadColleges();
  }, []);

  async function loadColleges() {
    try {
      setLoading(true);
      const data = await getColleges();
      setColleges(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(college) {
    if (!confirm(`Delete "${college.college_name}"? This cannot be undone.`)) return;
    try {
      setDeleting(college.college_id);
      await deleteCollege(college.college_id);
      setColleges(prev => prev.filter(c => c.college_id !== college.college_id));
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    } finally {
      setDeleting(null);
    }
  }

  const filtered = colleges.filter(c => {
    if (!search) return true;
    const q = search.toLowerCase();
    return c.college_name?.toLowerCase().includes(q) || c.city?.toLowerCase().includes(q) || c.state?.toLowerCase().includes(q);
  });

  return (
    <div className="admin-page">
      <motion.div className="admin-page-header" {...fadeUp}>
        <div>
          <h1 className="admin-page-title">Colleges</h1>
          <p className="admin-page-subtitle">{colleges.length} college{colleges.length !== 1 ? 's' : ''} in corpus</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/admin/colleges/new')}>
          <Plus size={16} /> Add College
        </button>
      </motion.div>

      <motion.div className="admin-search-bar" {...fadeUp} transition={{ delay: 0.05 }}>
        <Search size={16} className="admin-search-icon" />
        <input
          type="text"
          className="input"
          placeholder="Search colleges by name, city, or state…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </motion.div>

      {error && (
        <div className="admin-error">{error}</div>
      )}

      {loading ? (
        <div className="admin-loading">Loading colleges…</div>
      ) : (
        <motion.div className="college-table-wrapper" {...fadeUp} transition={{ delay: 0.1 }}>
          <table className="college-table">
            <thead>
              <tr>
                <th>College</th>
                <th>Type</th>
                <th>Location</th>
                <th>Annual Cost</th>
                <th>Hostel</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(college => (
                <tr key={college.college_id}>
                  <td>
                    <div className="college-name-cell">
                      <Building2 size={14} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                      <span className="college-name">{college.college_name}</span>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-neutral">{college.institute_type}</span>
                  </td>
                  <td className="td-muted">{college.city}, {college.state}</td>
                  <td className="td-muted">₹{college.total_annual_cost_lakh}L</td>
                  <td>
                    <span className={`badge ${college.hostel_available ? 'badge-official' : 'badge-neutral'}`}>
                      {college.hostel_available ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => navigate(`/admin/colleges/${college.college_id}`)}
                        title="Edit"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        className="btn btn-ghost btn-sm btn-danger"
                        onClick={() => handleDelete(college)}
                        disabled={deleting === college.college_id}
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-state">
                    {search ? 'No colleges match your search.' : 'No colleges yet. Add one to get started.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </motion.div>
      )}
    </div>
  );
}