import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Database, RefreshCw, CheckCircle, AlertTriangle, Clock, Layers, Building2, FileText } from 'lucide-react';
import { getCorpusStatus, refreshCorpus } from '../../api';
import './CorpusStatusPage.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
};

export default function CorpusStatusPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    try {
      setLoading(true);
      const data = await getCorpusStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    if (refreshing) return;
    try {
      setRefreshing(true);
      setRefreshResult(null);
      const result = await refreshCorpus();
      setRefreshResult(result);
      await loadStatus();
    } catch (err) {
      setError(`Refresh failed: ${err.message}`);
    } finally {
      setRefreshing(false);
    }
  }

  if (loading) return <div className="admin-loading">Loading corpus status…</div>;

  return (
    <div className="admin-page">
      <motion.div className="admin-page-header" {...fadeUp}>
        <div>
          <h1 className="admin-page-title">Corpus Status</h1>
          <p className="admin-page-subtitle">Vector store and evidence index information</p>
        </div>
        <button className="btn btn-primary" onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
          {refreshing ? 'Refreshing…' : 'Refresh Corpus'}
        </button>
      </motion.div>

      {error && <div className="admin-error">{error}</div>}

      {refreshResult && (
        <motion.div className="refresh-result" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <CheckCircle size={16} style={{ color: 'var(--trust-official)' }} />
          <span>Corpus refreshed — version {refreshResult.new_version}, {refreshResult.chunk_count} chunks</span>
        </motion.div>
      )}

      <motion.div className="corpus-stats-grid" {...fadeUp} transition={{ delay: 0.05 }}>
        <StatCard icon={<Layers size={20} />} label="Schema Version" value={status?.schema_version || '—'} />
        <StatCard icon={<Layers size={20} />} label="Corpus Version" value={status?.version || '—'} />
        <StatCard icon={<Database size={20} />} label="Total Chunks" value={status?.chunk_count?.toLocaleString() || '0'} />
        <StatCard icon={<Building2 size={20} />} label="Colleges Indexed" value={status?.college_count?.toLocaleString() || '0'} />
        <StatCard icon={<FileText size={20} />} label="Documents" value={status?.document_count?.toLocaleString() || '0'} />
        <StatCard icon={<Clock size={20} />} label="Last Updated" value={status?.updated_at ? new Date(status.updated_at).toLocaleString() : '—'} />
      </motion.div>

      <motion.div className="corpus-status-card" {...fadeUp} transition={{ delay: 0.1 }}>
        <div className="corpus-status-row">
          <span className="corpus-status-label">Stale Status</span>
          {status?.is_stale ? (
            <span className="badge badge-warning">
              <AlertTriangle size={12} /> Stale — re-ingest recommended
            </span>
          ) : (
            <span className="badge badge-official">
              <CheckCircle size={12} /> Up to date
            </span>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-content">
        <div className="stat-card-value">{value}</div>
        <div className="stat-card-label">{label}</div>
      </div>
    </div>
  );
}