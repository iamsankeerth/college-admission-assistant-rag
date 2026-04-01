import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, ArrowLeft, Building2, MapPin, IndianRupee, GraduationCap,
  ExternalLink, ShieldCheck, AlertTriangle, Briefcase, BookOpen,
  Star, Zap, MessageCircle, Send, ChevronRight, Loader2, XCircle
} from 'lucide-react';
import { COLLEGE_NAMES } from '../data';
import { generateMockExplore } from '../data';
import { useMouseSpotlight } from '../hooks/useMouseSpotlight';
import './ExplorePage.css';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
};

export default function ExplorePage({ initialCollege, onBack }) {
  const { name: urlName } = useParams();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollege, setSelectedCollege] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [followUpQ, setFollowUpQ] = useState('');
  const [followUpAnswer, setFollowUpAnswer] = useState(null);
  const [followUpLoading, setFollowUpLoading] = useState(false);
  const [showSignals, setShowSignals] = useState(false);
  const [signalsData, setSignalsData] = useState(null);
  const [signalsLoading, setSignalsLoading] = useState(false);

  const collegeName = urlName || initialCollege;

  const filtered = COLLEGE_NAMES.filter(c =>
    c.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 8);

  useEffect(() => {
    if (collegeName) {
      handleExplore(collegeName);
    }
  }, [collegeName]);

  const handleExplore = async (name) => {
    setSelectedCollege(name);
    setSearchQuery(name);
    setShowSuggestions(false);
    setLoading(true);
    setError(null);
    setFollowUpQ('');
    setFollowUpAnswer(null);
    setShowSignals(false);
    setSignalsData(null);

    try {
      const { exploreCollege } = await import('../api');
      const result = await exploreCollege({ college_name: name, include_public_signals: false });
      setData(result);
    } catch (err) {
      const mockData = generateMockExplore(name);
      setData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUpSubmit = async () => {
    if (!followUpQ.trim()) return;
    setFollowUpLoading(true);
    try {
      const { queryCollege } = await import('../api');
      const result = await queryCollege({
        question: followUpQ,
        college_name: selectedCollege,
        include_public_signals: false,
      });
      setFollowUpAnswer(result);
    } catch (err) {
      setFollowUpAnswer({ error: 'Could not get an answer. Please try again.' });
    } finally {
      setFollowUpLoading(false);
    }
  };

  const handleToggleSignals = async (show) => {
    setShowSignals(show);
    if (show && !signalsData) {
      setSignalsLoading(true);
      try {
        const { getCollegeSignals } = await import('../api');
        const result = await getCollegeSignals({ college_name: selectedCollege });
        setSignalsData(result);
      } catch (err) {
        setSignalsData({ error: 'Could not load student signals.' });
      } finally {
        setSignalsLoading(false);
      }
    }
  };

  return (
    <section className="explore-section">
      <div className="container">
        <motion.div className="explore-header" {...fadeUp}>
          {onBack && (
            <button className="btn btn-ghost" onClick={onBack}>
              <ArrowLeft size={16} /> Back
            </button>
          )}
          <h2 className="gradient-text">Explore a College</h2>
          <p>Search for any college to see official evidence, admissions, placements, and more.</p>
        </motion.div>

        <motion.div
          className="explore-search-container"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="explore-search-wrapper">
            <Search size={18} className="explore-search-icon" />
            <input
              id="college-search"
              className="explore-search-input"
              type="text"
              placeholder="Search for a college — e.g. IIT Hyderabad, NIT Trichy, BITS Pilani…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            />
            {searchQuery && (
              <button
                className="explore-search-clear"
                onClick={() => { setSearchQuery(''); setData(null); setSelectedCollege(''); setFollowUpAnswer(null); setSignalsData(null); }}
              >
                <XCircle size={16} />
              </button>
            )}
          </div>

          <AnimatePresence>
            {showSuggestions && searchQuery && filtered.length > 0 && (
              <motion.div
                className="explore-suggestions"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              >
                {filtered.map(name => (
                  <button
                    key={name}
                    className="explore-suggestion-item"
                    onMouseDown={() => handleExplore(name)}
                  >
                    <Building2 size={14} />
                    <span>{name}</span>
                    <ChevronRight size={14} style={{ marginLeft: 'auto', color: 'var(--fg-dim)' }} />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {loading && (
          <motion.div className="explore-loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Loader2 size={24} className="spin-icon" style={{ color: 'var(--accent)' }} />
            <span>Loading official evidence for {selectedCollege}…</span>
          </motion.div>
        )}

        {error && (
          <motion.div className="explore-error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </motion.div>
        )}

        {!loading && !data && !error && (
          <motion.div
            className="explore-empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="explore-empty-icon">
              <Building2 size={32} />
            </div>
            <h3>Select a college to explore</h3>
            <p>Type a college name above to view its official summary, admissions, fees, placements, and more.</p>
            <div className="explore-empty-suggestions">
              <span className="label">Popular</span>
              <div className="explore-empty-chips">
                {['IIT Hyderabad', 'NIT Trichy', 'BITS Pilani', 'IIIT Hyderabad'].map(name => (
                  <button key={name} className="chip" onClick={() => handleExplore(name)}>{name}</button>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {!loading && data && (
          <ExploreDetail
            data={data}
            showSignals={showSignals}
            signalsData={signalsData}
            signalsLoading={signalsLoading}
            onToggleSignals={handleToggleSignals}
            followUpQ={followUpQ}
            setFollowUpQ={setFollowUpQ}
            followUpAnswer={followUpAnswer}
            followUpLoading={followUpLoading}
            onFollowUpSubmit={handleFollowUpSubmit}
          />
        )}
      </div>
    </section>
  );
}

function ExploreDetail({
  data,
  showSignals,
  signalsData,
  signalsLoading,
  onToggleSignals,
  followUpQ,
  setFollowUpQ,
  followUpAnswer,
  followUpLoading,
  onFollowUpSubmit,
}) {
  const enrichment = data.enrichment;
  const { onMouseMove, spotlightStyle } = useMouseSpotlight();

  return (
    <motion.div
      className="explore-detail"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="ed-hero">
        <div className="ed-hero-content">
          <h2>{data.college_name}</h2>
          <div className="ed-hero-badges">
            <span className="badge badge-official"><ShieldCheck size={11} /> Official Evidence</span>
            {data.enrichment_status === 'hydrated' && (
              <span className="badge badge-accent">Enriched</span>
            )}
          </div>
        </div>
      </div>

      <div className="ed-section" onMouseMove={onMouseMove}>
        <div className="card-spotlight" style={spotlightStyle} />
        <div className="ed-section-header">
          <div className="ed-section-title">
            <BookOpen size={18} />
            <span>Official Summary</span>
          </div>
          <span className="badge badge-official" style={{ fontSize: '0.5625rem' }}>Verified</span>
        </div>
        <div className="citation-block official">
          <p>{data.official_summary}</p>
        </div>
      </div>

      {enrichment?.cost_and_admissions && (
        <div className="ed-section">
          <div className="ed-section-header">
            <div className="ed-section-title">
              <IndianRupee size={18} />
              <span>Admissions & Fees</span>
            </div>
            <span className="badge badge-official" style={{ fontSize: '0.5625rem' }}>Official</span>
          </div>
          <div className="ed-grid">
            <div className="ed-stat-card">
              <span className="ed-stat-label">Annual Cost</span>
              <span className="ed-stat-value">₹{enrichment.cost_and_admissions.annual_cost_lakh}L/year</span>
            </div>
            <div className="ed-stat-card">
              <span className="ed-stat-label">Counselling</span>
              <span className="ed-stat-value">{enrichment.cost_and_admissions.counselling_body}</span>
            </div>
            <div className="ed-stat-card">
              <span className="ed-stat-label">Hostel</span>
              <span className="ed-stat-value">{enrichment.cost_and_admissions.hostel_available ? 'Available' : 'Not Available'}</span>
            </div>
          </div>
          {enrichment.cost_and_admissions.admission_process && (
            <p className="ed-body-text">{enrichment.cost_and_admissions.admission_process}</p>
          )}
          {enrichment.cost_and_admissions.scholarship_notes && (
            <div className="ed-note-box">
              <Star size={14} />
              <span>{enrichment.cost_and_admissions.scholarship_notes}</span>
            </div>
          )}
        </div>
      )}

      {enrichment?.outcomes_and_campus && (
        <div className="ed-section">
          <div className="ed-section-header">
            <div className="ed-section-title">
              <Briefcase size={18} />
              <span>Placements & Campus</span>
            </div>
            <span className="badge badge-official" style={{ fontSize: '0.5625rem' }}>Official</span>
          </div>
          {enrichment.outcomes_and_campus.placement_summary && (
            <div className="ed-highlight-box">
              <div className="ed-highlight-label label"><Briefcase size={12} /> Placement Highlights</div>
              <p className="ed-body-text">{enrichment.outcomes_and_campus.placement_summary}</p>
            </div>
          )}
          {enrichment.outcomes_and_campus.roi_indicator && (
            <div className="ed-stat-card" style={{ display: 'inline-flex', gap: 'var(--space-3)' }}>
              <span className="ed-stat-label">ROI Indicator</span>
              <span className="ed-stat-value" style={{ color: 'var(--trust-official)' }}>{enrichment.outcomes_and_campus.roi_indicator}</span>
            </div>
          )}
          <div className="ed-campus-grid">
            {enrichment.outcomes_and_campus.lab_facilities && (
              <CampusCard icon={<BookOpen size={15} />} title="Labs & Facilities" text={enrichment.outcomes_and_campus.lab_facilities} />
            )}
            {enrichment.outcomes_and_campus.startup_culture && (
              <CampusCard icon={<Zap size={15} />} title="Startup Culture" text={enrichment.outcomes_and_campus.startup_culture} />
            )}
            {enrichment.outcomes_and_campus.extracurriculars && (
              <CampusCard icon={<Star size={15} />} title="Student Life" text={enrichment.outcomes_and_campus.extracurriculars} />
            )}
          </div>
        </div>
      )}

      {data.citations?.length > 0 && (
        <div className="ed-section">
          <div className="ed-section-header">
            <div className="ed-section-title">
              <ShieldCheck size={18} />
              <span>Citations & Evidence</span>
            </div>
          </div>
          <div className="ed-citations">
            {data.citations.map((cite, i) => (
              <div key={i} className="citation-block official">
                <div className="ed-cite-header">
                  <span className="ed-cite-title">{cite.title}</span>
                  <a href={cite.url} target="_blank" rel="noopener noreferrer" className="ed-cite-link">
                    <ExternalLink size={12} />
                  </a>
                </div>
                <p className="ed-cite-text">{cite.supporting_text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="ed-section ed-signals-section">
        <button
          className="ed-signals-toggle"
          onClick={() => onToggleSignals(!showSignals)}
        >
          <MessageCircle size={16} />
          <span>{showSignals ? 'Hide' : 'Show'} Student Signals</span>
          <span className="badge badge-student" style={{ fontSize: '0.5625rem' }}>Unverified · Opt-in</span>
        </button>

        <AnimatePresence>
          {showSignals && (
            <motion.div
              className="ed-signals-content"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="ed-signals-disclaimer">
                <AlertTriangle size={14} />
                <span>{data.public_signals_disclaimer || 'Student signals are crowdsourced and unverified. Treat as directional only.'}</span>
              </div>

              {signalsLoading && (
                <div className="ed-loading-inline">
                  <Loader2 size={16} className="spin-icon" style={{ color: 'var(--accent)' }} />
                  <span>Loading student signals…</span>
                </div>
              )}

              {signalsData && !signalsData.error && (
                <>
                  {signalsData.reddit_signals?.length > 0 && (
                    <div className="ed-signals-group">
                      <div className="ed-signals-group-label label">Reddit Discussions</div>
                      {signalsData.reddit_signals.map((sig, i) => (
                        <div key={i} className="ed-signal-item">
                          <div className="ed-signal-title">{sig.title}</div>
                          <div className="ed-signal-meta">{sig.subreddit} · {sig.upvotes} upvotes</div>
                          <p className="ed-signal-text">{sig.summary}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {signalsData.youtube_signals?.length > 0 && (
                    <div className="ed-signals-group">
                      <div className="ed-signals-group-label label">YouTube Videos</div>
                      {signalsData.youtube_signals.map((sig, i) => (
                        <div key={i} className="ed-signal-item">
                          <div className="ed-signal-title">{sig.title}</div>
                          <div className="ed-signal-meta">{sig.channel} · {sig.views} views</div>
                          <p className="ed-signal-text">{sig.summary}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {(!signalsData.reddit_signals?.length && !signalsData.youtube_signals?.length) && (
                    <p className="ed-body-text" style={{ color: 'var(--fg-dim)' }}>
                      No student signals found for this college yet.
                    </p>
                  )}
                </>
              )}

              {signalsData?.error && (
                <p className="ed-body-text" style={{ color: 'var(--trust-caution)' }}>
                  {signalsData.error}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="ed-section">
        <div className="ed-section-header">
          <div className="ed-section-title">
            <MessageCircle size={18} />
            <span>Ask a follow-up</span>
          </div>
        </div>
        <div className="ed-followup-form">
          <input
            id="followup-input"
            className="input"
            type="text"
            placeholder={`Ask about ${data.college_name} — e.g. "What are the hostel fees?"`}
            value={followUpQ}
            onChange={(e) => setFollowUpQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && followUpQ.trim() && handleFollowUpKeyDown(e)}
            disabled={followUpLoading}
          />
          <button
            className="btn btn-primary"
            disabled={!followUpQ.trim() || followUpLoading}
            onClick={onFollowUpSubmit}
          >
            {followUpLoading ? <Loader2 size={16} className="spin-icon" /> : <Send size={16} />}
          </button>
        </div>

        {followUpAnswer && (
          <motion.div
            className="ed-followup-answer"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {followUpAnswer.error ? (
              <div className="ed-followup-error">
                <AlertTriangle size={14} />
                <span>{followUpAnswer.error}</span>
              </div>
            ) : (
              <>
                <div className="ed-followup-label label">Answer</div>
                <div className="citation-block official">
                  <p>{followUpAnswer.answer || followUpAnswer.official_summary}</p>
                </div>
                {followUpAnswer.citations?.length > 0 && (
                  <div className="ed-followup-citations">
                    <span className="label" style={{ marginBottom: 8, display: 'block' }}>Sources</span>
                    {followUpAnswer.citations.map((c, i) => (
                      <a key={i} href={c.url} target="_blank" rel="noopener noreferrer" className="ed-cite-link">
                        <ExternalLink size={11} /> {c.title || new URL(c.url).hostname}
                      </a>
                    ))}
                  </div>
                )}
              </>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

function handleFollowUpKeyDown(e) {
}

function CampusCard({ icon, title, text }) {
  return (
    <div className="ed-campus-card">
      <div className="ed-campus-card-header">
        {icon}
        <span>{title}</span>
      </div>
      <p>{text}</p>
    </div>
  );
}