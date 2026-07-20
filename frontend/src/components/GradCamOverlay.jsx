/**
 * GradCAM Overlay Controls
 *
 * Provides toggle and mock data generation for GradCAM heatmap visualization.
 * In production, this receives real GradCAM data from Nick's vision pipeline.
 * Currently generates synthetic Gaussian blobs positioned at finding locations.
 */

/**
 * Generate a mock GradCAM heatmap — a synthetic Gaussian blob.
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @param {string} location - Anatomical location of finding
 * @returns {{ heatmap: Float32Array, mapWidth: number, mapHeight: number }}
 */
export function generateMockGradcam(width = 256, height = 256, location = '') {
  const mapWidth = 64;
  const mapHeight = 64;
  const heatmap = new Float32Array(mapWidth * mapHeight);
  let cx = mapWidth / 2;
  let cy = mapHeight / 2;
  const loc = location.toLowerCase();

  if (loc.includes('right') && loc.includes('lower')) {
    cx = mapWidth * 0.35; cy = mapHeight * 0.7;
  } else if (loc.includes('right') && loc.includes('upper')) {
    cx = mapWidth * 0.35; cy = mapHeight * 0.3;
  } else if (loc.includes('left') && loc.includes('lower')) {
    cx = mapWidth * 0.65; cy = mapHeight * 0.7;
  } else if (loc.includes('left') && loc.includes('upper')) {
    cx = mapWidth * 0.65; cy = mapHeight * 0.3;
  } else if (loc.includes('right')) {
    cx = mapWidth * 0.35;
  } else if (loc.includes('left')) {
    cx = mapWidth * 0.65;
  } else if (loc.includes('bilateral') || loc.includes('diffuse')) {
    const sigma = mapWidth * 0.15;
    const centers = [
      [mapWidth * 0.35, mapHeight * 0.5],
      [mapWidth * 0.65, mapHeight * 0.5],
    ];
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        let maxVal = 0;
        for (const [ccx, ccy] of centers) {
          const dx = x - ccx;
          const dy = y - ccy;
          maxVal = Math.max(maxVal, Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma)));
        }
        heatmap[y * mapWidth + x] = maxVal;
      }
    }
    return { heatmap, mapWidth, mapHeight };
  }

  // Single Gaussian blob
  const sigma = mapWidth * 0.15;
  for (let y = 0; y < mapHeight; y++) {
    for (let x = 0; x < mapWidth; x++) {
      const dx = x - cx;
      const dy = y - cy;
      heatmap[y * mapWidth + x] = Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma));
    }
  }
  return { heatmap, mapWidth, mapHeight };
}

export default function GradCamControls({ showGradcam, onToggle, finding }) {
  return (
    <div className="gradcam-controls">
      <label className="toggle-label" htmlFor="gradcam-toggle">
        <input
          id="gradcam-toggle"
          type="checkbox"
          className="toggle-input"
          checked={showGradcam}
          onChange={(e) => onToggle(e.target.checked)}
        />
        <span className="toggle-slider" />
        <span>GradCAM Overlay</span>
      </label>
      {showGradcam && finding && (
        <span className="gradcam-label">
          Highlighting: {finding.label} ({finding.location || 'Unknown location'})
        </span>
      )}
      {showGradcam && (
        <span className="text-muted text-sm">Mock visualization — awaiting ML pipeline</span>
      )}
    </div>
  );
}
