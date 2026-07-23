import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  LineChart, Line, Legend, AreaChart, Area,
} from 'recharts';

// Mock model performance data
const PATHOLOGY_METRICS = [
  { pathology: 'Consolidation', auc: 0.94, sensitivity: 0.89, specificity: 0.96 },
  { pathology: 'Pleural Effusion', auc: 0.97, sensitivity: 0.93, specificity: 0.98 },
  { pathology: 'Cardiomegaly', auc: 0.92, sensitivity: 0.87, specificity: 0.94 },
  { pathology: 'Pneumothorax', auc: 0.96, sensitivity: 0.91, specificity: 0.97 },
  { pathology: 'Atelectasis', auc: 0.88, sensitivity: 0.82, specificity: 0.91 },
  { pathology: 'Edema', auc: 0.91, sensitivity: 0.86, specificity: 0.93 },
  { pathology: 'Nodule', auc: 0.85, sensitivity: 0.79, specificity: 0.89 },
];

const CALIBRATION_DATA = [
  { predicted: 0.1, actual: 0.08, ideal: 0.1 },
  { predicted: 0.2, actual: 0.18, ideal: 0.2 },
  { predicted: 0.3, actual: 0.32, ideal: 0.3 },
  { predicted: 0.4, actual: 0.38, ideal: 0.4 },
  { predicted: 0.5, actual: 0.52, ideal: 0.5 },
  { predicted: 0.6, actual: 0.57, ideal: 0.6 },
  { predicted: 0.7, actual: 0.71, ideal: 0.7 },
  { predicted: 0.8, actual: 0.78, ideal: 0.8 },
  { predicted: 0.9, actual: 0.92, ideal: 0.9 },
];

const PIPELINE_STATS = [
  { label: 'Total Analyses', value: '1,247', icon: '🔬' },
  { label: 'Avg. Time', value: '3.2s', icon: '⏱' },
  { label: 'Success Rate', value: '98.4%', icon: '✓' },
  { label: 'Feedback Count', value: '312', icon: '📝' },
];

const WEEKLY_VOLUME = [
  { week: 'W1', scans: 142, analyses: 138 },
  { week: 'W2', scans: 168, analyses: 165 },
  { week: 'W3', scans: 195, analyses: 191 },
  { week: 'W4', scans: 203, analyses: 198 },
  { week: 'W5', scans: 187, analyses: 184 },
  { week: 'W6', scans: 221, analyses: 218 },
  { week: 'W7', scans: 234, analyses: 229 },
];

const REPORT_QUALITY = [
  { metric: 'Completeness', score: 92 },
  { metric: 'Clinical Accuracy', score: 88 },
  { metric: 'Clarity', score: 95 },
  { metric: 'Evidence Cited', score: 84 },
  { metric: 'Guideline Adherence', score: 90 },
];

const chartTheme = {
  bg: '#1a1f2e',
  grid: '#2a3040',
  text: '#94a3b8',
  primary: '#0ea5e9',
  secondary: '#06b6d4',
  accent: '#8b5cf6',
  success: '#22c55e',
};

export default function DashboardPage() {
  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h2>Evaluation Dashboard</h2>
        <p className="text-muted">
          Model performance, report quality, and pipeline statistics
        </p>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid">
        {PIPELINE_STATS.map((stat) => (
          <div key={stat.label} className="stat-card glass-card">
            <span className="stat-icon">{stat.icon}</span>
            <div className="stat-content">
              <span className="stat-value">{stat.value}</span>
              <span className="stat-label">{stat.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* AUC by Pathology */}
        <div className="chart-card glass-card">
          <h3>AUC by Pathology</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={PATHOLOGY_METRICS}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
              <XAxis
                dataKey="pathology"
                stroke={chartTheme.text}
                tick={{ fontSize: 11 }}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis stroke={chartTheme.text} domain={[0.7, 1]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartTheme.bg,
                  border: `1px solid ${chartTheme.grid}`,
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="auc" fill={chartTheme.primary} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sensitivity vs Specificity Radar */}
        <div className="chart-card glass-card">
          <h3>Sensitivity vs Specificity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={PATHOLOGY_METRICS}>
              <PolarGrid stroke={chartTheme.grid} />
              <PolarAngleAxis
                dataKey="pathology"
                stroke={chartTheme.text}
                tick={{ fontSize: 10 }}
              />
              <PolarRadiusAxis domain={[0.7, 1]} stroke={chartTheme.grid} />
              <Radar
                name="Sensitivity"
                dataKey="sensitivity"
                stroke={chartTheme.primary}
                fill={chartTheme.primary}
                fillOpacity={0.3}
              />
              <Radar
                name="Specificity"
                dataKey="specificity"
                stroke={chartTheme.secondary}
                fill={chartTheme.secondary}
                fillOpacity={0.3}
              />
              <Legend />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartTheme.bg,
                  border: `1px solid ${chartTheme.grid}`,
                  borderRadius: 8,
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Calibration Curve */}
        <div className="chart-card glass-card">
          <h3>Confidence Calibration</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={CALIBRATION_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
              <XAxis
                dataKey="predicted"
                stroke={chartTheme.text}
                label={{
                  value: 'Predicted',
                  position: 'bottom',
                  fill: chartTheme.text,
                }}
              />
              <YAxis
                stroke={chartTheme.text}
                label={{
                  value: 'Actual',
                  angle: -90,
                  position: 'insideLeft',
                  fill: chartTheme.text,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartTheme.bg,
                  border: `1px solid ${chartTheme.grid}`,
                  borderRadius: 8,
                }}
              />
              <Line
                type="monotone"
                dataKey="ideal"
                stroke={chartTheme.grid}
                strokeDasharray="5 5"
                name="Perfect Calibration"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke={chartTheme.primary}
                strokeWidth={2}
                name="Model"
                dot={{ fill: chartTheme.primary }}
              />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Volume */}
        <div className="chart-card glass-card">
          <h3>Weekly Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={WEEKLY_VOLUME}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
              <XAxis dataKey="week" stroke={chartTheme.text} />
              <YAxis stroke={chartTheme.text} />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartTheme.bg,
                  border: `1px solid ${chartTheme.grid}`,
                  borderRadius: 8,
                }}
              />
              <Area
                type="monotone"
                dataKey="scans"
                stroke={chartTheme.primary}
                fill={chartTheme.primary}
                fillOpacity={0.2}
                name="Scans Uploaded"
              />
              <Area
                type="monotone"
                dataKey="analyses"
                stroke={chartTheme.secondary}
                fill={chartTheme.secondary}
                fillOpacity={0.2}
                name="Analyses Run"
              />
              <Legend />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Report Quality */}
      <div className="chart-card glass-card report-quality-section">
        <h3>Report Quality Metrics</h3>
        <div className="quality-bars">
          {REPORT_QUALITY.map((item) => (
            <div key={item.metric} className="quality-row">
              <span className="quality-label">{item.metric}</span>
              <div className="quality-bar-track">
                <div
                  className="quality-bar-fill"
                  style={{
                    width: `${item.score}%`,
                    backgroundColor:
                      item.score >= 90 ? chartTheme.success : chartTheme.primary,
                  }}
                />
              </div>
              <span className="quality-score">{item.score}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-footer text-muted text-sm">
        <p>
          📊 All metrics shown are based on mock evaluation data. Connect to
          live pipeline for real-time monitoring.
        </p>
      </div>
    </div>
  );
}
