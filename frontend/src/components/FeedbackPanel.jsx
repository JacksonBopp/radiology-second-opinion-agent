import { useState, useEffect } from 'react';
import api from '../api/client';

export default function FeedbackPanel({ scanId, originalFindings }) {
  const [notes, setNotes] = useState('');
  const [correctedFindings, setCorrectedFindings] = useState([]);
  const [history, setHistory] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (scanId) loadHistory();
  }, [scanId]);

  useEffect(() => {
    if (originalFindings?.length) {
      setCorrectedFindings(
        originalFindings.map((f) => ({ ...f, corrected: false }))
      );
    }
  }, [originalFindings]);

  const loadHistory = async () => {
    try {
      const res = await api.get(`/feedback?scan_id=${scanId}`);
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load feedback history:', err);
    }
  };

  const handleFindingChange = (index, field, value) => {
    setCorrectedFindings((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value, corrected: true };
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/feedback', {
        scan_id: scanId,
        original_findings: originalFindings || [],
        corrected_findings: correctedFindings.filter((f) => f.corrected),
        notes: notes || null,
      });
      setSubmitted(true);
      setNotes('');
      loadHistory();
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="feedback-panel glass-card">
      <div className="feedback-header">
        <h3>Radiologist Feedback</h3>
        <button
          className="btn btn--sm btn--ghost"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? 'Hide' : 'Show'} History ({history.length})
        </button>
      </div>

      {showHistory && history.length > 0 && (
        <div className="feedback-history">
          {history.map((entry) => (
            <div key={entry.id} className="feedback-history-item">
              <div className="feedback-history-meta">
                <span className="badge badge--subtle">{entry.reviewer}</span>
                <span className="text-muted text-sm">{entry.timestamp}</span>
              </div>
              {entry.notes && <p className="text-sm">{entry.notes}</p>}
              {entry.corrected_findings?.length > 0 && (
                <p className="text-sm text-muted">
                  {entry.corrected_findings.length} finding(s) corrected
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <form className="feedback-form" onSubmit={handleSubmit}>
        {correctedFindings.length > 0 && (
          <div className="feedback-findings">
            <h4>Review Findings</h4>
            {correctedFindings.map((finding, idx) => (
              <div key={idx} className="feedback-finding-row">
                <span className="finding-label">{finding.label}</span>
                <select
                  className="form-select form-select--sm"
                  value={finding.severity_override || ''}
                  onChange={(e) =>
                    handleFindingChange(idx, 'severity_override', e.target.value)
                  }
                >
                  <option value="">No change</option>
                  <option value="normal">Normal</option>
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                  <option value="false_positive">False Positive</option>
                </select>
              </div>
            ))}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="feedback-notes">Clinical Notes</label>
          <textarea
            id="feedback-notes"
            className="form-textarea"
            placeholder="Additional observations, corrections, or recommendations..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
          />
        </div>

        <button
          type="submit"
          className="btn btn--primary"
          disabled={
            submitting ||
            (!notes.trim() && !correctedFindings.some((f) => f.corrected))
          }
        >
          {submitting ? 'Submitting...' : submitted ? '✓ Submitted' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  );
}
