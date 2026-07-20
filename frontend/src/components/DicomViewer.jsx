import { useRef, useEffect, useState, useCallback } from 'react';

export default function DicomViewer({ imageData, gradcamData, showGradcam }) {
  const canvasRef = useRef(null);
  const overlayRef = useRef(null);
  const [windowCenter, setWindowCenter] = useState(127);
  const [windowWidth, setWindowWidth] = useState(256);
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // Render the image with window/level adjustments
  const renderImage = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageData) return;
    const ctx = canvas.getContext('2d');
    const { width, height, pixelData } = imageData;
    canvas.width = width;
    canvas.height = height;
    const imgData = ctx.createImageData(width, height);
    const minVal = windowCenter - windowWidth / 2;
    const maxVal = windowCenter + windowWidth / 2;
    for (let i = 0; i < pixelData.length; i++) {
      let val = pixelData[i];
      val = ((val - minVal) / (maxVal - minVal)) * 255;
      val = Math.max(0, Math.min(255, val));
      const idx = i * 4;
      imgData.data[idx] = val;
      imgData.data[idx + 1] = val;
      imgData.data[idx + 2] = val;
      imgData.data[idx + 3] = 255;
    }
    ctx.putImageData(imgData, 0, 0);
  }, [imageData, windowCenter, windowWidth]);

  // Render GradCAM heatmap overlay
  const renderGradcam = useCallback(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    const width = overlay.width;
    const height = overlay.height;
    ctx.clearRect(0, 0, width, height);
    if (!showGradcam || !gradcamData) return;
    const { heatmap, mapWidth, mapHeight } = gradcamData;
    const scaleX = width / mapWidth;
    const scaleY = height / mapHeight;
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const val = heatmap[y * mapWidth + x];
        if (val < 0.15) continue;
        // Jet colormap: blue → cyan → green → yellow → red
        let r, g, b;
        if (val < 0.25) { r = 0; g = Math.floor(val * 4 * 255); b = 255; }
        else if (val < 0.5) { r = 0; g = 255; b = Math.floor((1 - (val - 0.25) * 4) * 255); }
        else if (val < 0.75) { r = Math.floor((val - 0.5) * 4 * 255); g = 255; b = 0; }
        else { r = 255; g = Math.floor((1 - (val - 0.75) * 4) * 255); b = 0; }
        ctx.fillStyle = `rgba(${r},${g},${b},${val * 0.6})`;
        ctx.fillRect(x * scaleX, y * scaleY, scaleX + 1, scaleY + 1);
      }
    }
  }, [showGradcam, gradcamData]);

  useEffect(() => { renderImage(); }, [renderImage]);

  useEffect(() => {
    if (imageData && overlayRef.current) {
      overlayRef.current.width = imageData.width;
      overlayRef.current.height = imageData.height;
      renderGradcam();
    }
  }, [renderGradcam, imageData]);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    if (e.shiftKey) {
      setPan((prev) => ({
        x: prev.x + e.clientX - dragStart.x,
        y: prev.y + e.clientY - dragStart.y,
      }));
    } else {
      setWindowCenter((prev) => prev + (e.clientY - dragStart.y));
      setWindowWidth((prev) => Math.max(1, prev + (e.clientX - dragStart.x)));
    }
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e) => {
    e.preventDefault();
    setZoom((prev) => Math.max(0.2, Math.min(5, prev - e.deltaY * 0.001)));
  };

  const resetView = () => {
    setWindowCenter(127);
    setWindowWidth(256);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="dicom-viewer">
      <div className="dicom-toolbar">
        <div className="dicom-controls">
          <span className="dicom-info">W: {windowWidth} | L: {windowCenter}</span>
          <span className="dicom-info">Zoom: {(zoom * 100).toFixed(0)}%</span>
        </div>
        <div className="dicom-actions">
          <button className="btn btn--sm btn--ghost" onClick={() => setZoom((z) => Math.min(5, z + 0.25))}>🔍+</button>
          <button className="btn btn--sm btn--ghost" onClick={() => setZoom((z) => Math.max(0.2, z - 0.25))}>🔍−</button>
          <button className="btn btn--sm btn--ghost" onClick={resetView}>↻ Reset</button>
        </div>
      </div>
      <div
        className="dicom-canvas-container"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {imageData ? (
          <div
            className="dicom-canvas-wrapper"
            style={{
              transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
              transformOrigin: 'center center',
            }}
          >
            <canvas ref={canvasRef} className="dicom-canvas" />
            <canvas ref={overlayRef} className="dicom-overlay-canvas" />
          </div>
        ) : (
          <div className="dicom-placeholder">
            <span className="dicom-placeholder-icon">🩻</span>
            <p>No image loaded</p>
            <p className="text-muted">Upload a DICOM file to view</p>
          </div>
        )}
      </div>
      <div className="dicom-footer">
        <span className="text-muted">Drag: W/L adjust • Shift+Drag: Pan • Scroll: Zoom</span>
      </div>
    </div>
  );
}
