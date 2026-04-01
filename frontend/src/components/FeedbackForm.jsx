import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThumbsUp, ThumbsDown, MessageSquare, Send, CheckCircle } from 'lucide-react';
import { submitFeedback } from '../api';
import './FeedbackForm.css';

export default function FeedbackForm({ query, collegeName, recommendedColleges = [], onClose }) {
  const [helpful, setHelpful] = useState(null);
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (helpful === null) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback({
        query: query || '',
        college_name: collegeName || null,
        recommended_colleges: recommendedColleges,
        helpful,
        comments,
      });
      setSubmitted(true);
    } catch (err) {
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <motion.div
        className="feedback-success"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <CheckCircle size={20} style={{ color: 'var(--trust-official)' }} />
        <div>
          <p className="feedback-success-title">Thanks for your feedback!</p>
          <p className="feedback-success-note">It helps us improve CollegeCompass.</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="feedback-widget"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="feedback-header">
        <MessageSquare size={16} style={{ color: 'var(--accent)' }} />
        <span className="feedback-title">Was this helpful?</span>
        {onClose && (
          <button className="feedback-close" onClick={onClose}>×</button>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="feedback-buttons">
          <button
            type="button"
            className={`feedback-btn ${helpful === true ? 'active' : ''}`}
            onClick={() => setHelpful(true)}
          >
            <ThumbsUp size={16} />
            Yes, helpful
          </button>
          <button
            type="button"
            className={`feedback-btn ${helpful === false ? 'active' : ''}`}
            onClick={() => setHelpful(false)}
          >
            <ThumbsDown size={16} />
            Not helpful
          </button>
        </div>

        <AnimatePresence>
          {helpful !== null && (
            <motion.div
              className="feedback-comment-section"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
            >
              <textarea
                className="textarea feedback-textarea"
                placeholder="Any comments? (optional)"
                value={comments}
                onChange={e => setComments(e.target.value)}
                rows={3}
              />
              {error && <p className="feedback-error">{error}</p>}
              <button
                type="submit"
                className="btn btn-primary btn-sm"
                disabled={submitting}
              >
                <Send size={13} />
                {submitting ? 'Submitting…' : 'Submit Feedback'}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </motion.div>
  );
}
