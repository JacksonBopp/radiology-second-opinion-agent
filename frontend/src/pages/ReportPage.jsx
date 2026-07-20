import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useMemo } from 'react';
import DicomViewer from '../components/DicomViewer';
import GradCamControls, { generateMockGradcam } from '../components/GradCamOverlay';
import FeedbackPanel from '../components/FeedbackPanel';

const CONFIDENCE_COLORS = {
  very_low: '#ef4444',
  low: '#f97316',
  moderate: '#eab308',
  high: '#22c55e',
  very_high: '#06b6d4',
};

const CONFIDENCE_LABELS = {
  very_low: 'Very Low',
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  very_high: 'Very High',
};

// Mock report data for demonstration when no real analysis data is available
const MOCK_REPORT = {
  scan_id: 'demo-scan-001',
  generated_at: new Date().toISOString(),
  findings_summary: [
    {
      label: 'Consolidation',
      location: 'Right lower lobe',
      severity_descriptor: 'Moderate',
      confidence_phrase: 'Moderate confidence (68%)',
    },
    {
      label: 'Pleural Effusion',
      location: 'Right costophrenic angle',
      severity_descriptor: 'Mild',
      confidence_phrase: 'High confidence (82%)',
    },
  ],
  sections: [
    {
      heading: 'FINDINGS',
      body: 'There is an area of consolidation in the right lower lobe measuring approximately 4.2 cm in greatest dimension, with air bronchograms suggesting an infectious etiology. A small right-sided pleural effusion is noted, layering dependently. The cardiac silhouette is within normal limits. No pneumothorax is identified. The osseous structures are unremarkable.',
    },
    {
      heading: 'IMPRESSION',
      body: '1. Right lower lobe consolidation, most consistent with community-acquired pneumonia.\n2. Small right-sided pleural effusion, likely reactive/parapneumonic.\n3. No acute cardiopulmonary abnormality otherwise.',
    },
    {
      heading: 'RECOMMENDATION',
      body: 'Clinical correlation with symptom duration and laboratory findings (CBC, CRP, procalcitonin) is recommended. Follow-up imaging in 6-8 weeks to confirm resolution may be considered. If symptoms worsen or fail to improve, CT chest may provide additional characterization.',
    },
  ],
  differential_diagnoses: [
    {
      rank: 1,
      diagnosis: 'Community-acquired pneumonia',
      probability: 0.72,
      confidence_level: 'high',
      confidence_phrase: 'High confidence (~72%)',
      supporting_evidence: [
        'Right lower lobe consolidation with air bronchograms',
        'Reactive pleural effusion',
      ],
      contradicting_evidence: [],
      reasoning:
        'Classic presentation with lobar consolidation and parapneumonic effusion.',
    },
    {
      rank: 2,
      diagnosis: 'Aspiration pneumonia',
      probability: 0.15,
      confidence_level: 'low',
      confidence_phrase: 'Low confidence (~15%)',
      supporting_evidence: [
        'Right lower lobe involvement (dependent position)',
      ],
      contradicting_evidence: [
        'No history of aspiration risk factors provided',
      ],
      reasoning:
        'RLL is a common site for aspiration, but clinical correlation needed.',
    },
    {
      rank: 3,
      diagnosis: 'Pulmonary embolism with infarction',
      probability: 0.08,
      confidence_level: 'very_low',
      confidence_phrase: 'Very low confidence (~8%)',
      supporting_evidence: ['Pleural effusion'],
      contradicting_evidence: [
        'Consolidation pattern more typical of infection',
        'No Westermark sign',
      ],
      reasoning:
        'Less likely given consolidation pattern, but cannot be excluded without CT angiography.',
    },
  ],
  guideline_references: [
    {
      text: 'ATS/IDSA 2019 Guidelines for Community-Acquired Pneumonia',
      relevance:
        'Diagnostic criteria and management recommendations for CAP',
    },
    {
      text: 'Fleischner Society 2017 — Incidental Pulmonary Nodules',
      relevance: 'Follow-up imaging recommendations',
    },
  ],
  similar_case_ids: ['CASE-2024-0847', 'CASE-2024-1203'],
  overall_confidence_level: 'high',
  uncertainty_note:
    'This AI-generated second opinion is intended to supplement — not replace — radiologist interpretation. Clinical correlation is essential.',
  model_version: 'mock-v0',
};

export default function ReportPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [showGradcam, setShowGradcam] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

  // Use passed data or fall back to mock
  const { analysisResult, imageData, scanId } = location.state || {};
  const report = analysisResult?.result || MOCK_REPORT;
  const currentScanId = scanId || report.scan_id;

  // Generate mock GradCAM data based on selected finding
  const gradcamData = useMemo(() => {
    if (!showGradcam || !selectedFinding) return null;
    const width = imageData?.width || 256;
    const height = imageData?.height || 256;
    return generateMockGradcam(width, height, selectedFinding.location);
  }, [showGradcam, selectedFinding, imageData]);

  const findings = report.findings_summary || [];
  const currentFinding = selectedFinding || findings[0] || null;

  return (
    <div className="report-page">
      <div className="page-header">
        <div>
          <h2>Analysis Report</h2>
          <p className="text-muted">Scan: {currentScanId}</p>
        </div>
        <div className="page-header-actions">
          <button
            className="btn btn--ghost"
            onClick={() => setShowFeedback(!showFeedback)}
          >
            {showFeedback ? 'Hide' : '📝'} Feedback
          </button>
          <button className="btn btn--ghost" onClick={() => navigate('/upload')}>
            ← New Scan
          </button>
        </div>
      </div>

      <div className="report-layout">
        {/* Left: DICOM + GradCAM */}
        <div className="report-viewer-col">
          <DicomViewer
            imageData={imageData}
            gradcamData={gradcamData}
            showGradcam={showGradcam}
          />
          <GradCamControls
            showGradcam={showGradcam}
            onToggle={setShowGradcam}
            finding={currentFinding}
          />
        </div>

        {/* Right: Report */}
        <div className="report-content-col">
          {/* Confidence badge */}
          <div className="report-confidence glass-card">
            <div
              className="confidence-badge"
              style={{
                backgroundColor:
                  CONFIDENCE_COLORS[report.overall_confidence_level] + '22',
                borderColor:
                  CONFIDENCE_COLORS[report.overall_confidence_level],
              }}
            >
              <span
                className="confidence-dot"
                style={{
                  backgroundColor:
                    CONFIDENCE_COLORS[report.overall_confidence_level],
                }}
              />
              Overall: {CONFIDENCE_LABELS[report.overall_confidence_level]}{' '}
              Confidence
            </div>
            {report.uncertainty_note && (
              <p className="uncertainty-note">{report.uncertainty_note}</p>
            )}
          </div>

          {/* Findings summary */}
          {findings.length > 0 && (
            <div className="report-section glass-card">
              <h3>Findings</h3>
              <div className="findings-grid">
                {findings.map((finding, i) => (
                  <button
                    key={i}
                    className={`finding-card ${selectedFinding === finding ? 'finding-card--selected' : ''}`}
                    onClick={() => setSelectedFinding(finding)}
                  >
                    <div className="finding-card-header">
                      <span className="finding-label">{finding.label}</span>
                      <span
                        className={`badge badge--${finding.severity_descriptor?.toLowerCase() || 'info'}`}
                      >
                        {finding.severity_descriptor || 'N/A'}
                      </span>
                    </div>
                    <span className="finding-location">{finding.location}</span>
                    <span className="finding-confidence text-sm text-muted">
                      {finding.confidence_phrase}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Report sections */}
          {report.sections?.map((section, i) => (
            <div key={i} className="report-section glass-card">
              <h3>{section.heading}</h3>
              <p className="report-body">{section.body}</p>
            </div>
          ))}

          {/* Differential Diagnoses */}
          {report.differential_diagnoses?.length > 0 && (
            <div className="report-section glass-card">
              <h3>Differential Diagnoses</h3>
              <div className="differential-list">
                {report.differential_diagnoses.map((dx, i) => (
                  <div key={i} className="differential-item">
                    <div className="differential-header">
                      <span className="differential-rank">#{dx.rank}</span>
                      <span className="differential-name">{dx.diagnosis}</span>
                      <span className="differential-prob">
                        {(dx.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="differential-bar">
                      <div
                        className="differential-bar-fill"
                        style={{
                          width: `${dx.probability * 100}%`,
                          backgroundColor:
                            CONFIDENCE_COLORS[dx.confidence_level],
                        }}
                      />
                    </div>
                    <p className="differential-reasoning text-sm">
                      {dx.reasoning}
                    </p>
                    {dx.supporting_evidence?.length > 0 && (
                      <div className="differential-evidence">
                        <span className="evidence-label evidence-label--support">
                          Supporting:
                        </span>
                        <ul>
                          {dx.supporting_evidence.map((e, j) => (
                            <li key={j}>{e}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Guidelines */}
          {report.guideline_references?.length > 0 && (
            <div className="report-section glass-card">
              <h3>Referenced Guidelines</h3>
              <ul className="guidelines-list">
                {report.guideline_references.map((ref, i) => (
                  <li key={i}>
                    <strong>{ref.text}</strong>
                    {ref.relevance && (
                      <span className="text-muted"> — {ref.relevance}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Similar cases */}
          {report.similar_case_ids?.length > 0 && (
            <div className="report-section glass-card">
              <h3>Similar Historical Cases</h3>
              <div className="case-badges">
                {report.similar_case_ids.map((id) => (
                  <span key={id} className="badge badge--subtle">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Feedback panel */}
          {showFeedback && (
            <FeedbackPanel
              scanId={currentScanId}
              originalFindings={findings}
            />
          )}
        </div>
      </div>
    </div>
  );
}
