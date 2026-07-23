import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import DicomViewer from '../components/DicomViewer';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const parseFile = useCallback(async (selectedFile) => {
    setFile(selectedFile);
    setError(null);
    setUploadResult(null);
    try {
      const buffer = await selectedFile.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      // Generate a grayscale preview from the raw bytes
      const size = Math.floor(Math.sqrt(bytes.length));
      const width = Math.min(size, 512);
      const height = Math.min(size, 512);
      const pixelData = new Uint8Array(width * height);
      for (let i = 0; i < width * height && i < bytes.length; i++) {
        pixelData[i] = bytes[i % bytes.length];
      }
      setImageData({ width, height, pixelData });
    } catch (err) {
      console.warn('Could not parse file for preview:', err);
    }
  }, []);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      if (e.dataTransfer.files?.[0]) parseFile(e.dataTransfer.files[0]);
    },
    [parseFile]
  );

  const handleFileSelect = (e) => {
    if (e.target.files?.[0]) parseFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/scans', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!uploadResult) return;
    setAnalyzing(true);
    setError(null);
    try {
      const res = await api.post('/analyze', {
        scan_id: uploadResult.scan_id || `scan-${Date.now()}`,
        findings: uploadResult.findings || [],
        metadata: uploadResult.metadata || {},
      });
      navigate('/report', {
        state: {
          analysisResult: res.data,
          imageData,
          scanId: uploadResult.scan_id || `scan-${Date.now()}`,
        },
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <h2>Upload Scan</h2>
        <p className="text-muted">
          Upload a DICOM file for AI-powered second opinion analysis
        </p>
      </div>

      <div className="upload-grid">
        <div className="upload-left">
          {/* Drop zone */}
          <div
            className={`drop-zone glass-card ${dragActive ? 'drop-zone--active' : ''} ${file ? 'drop-zone--loaded' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              className="drop-zone-input"
              accept=".dcm,.dicom,application/dicom"
              onChange={handleFileSelect}
            />
            {file ? (
              <div className="drop-zone-loaded">
                <span className="drop-zone-icon">✓</span>
                <p className="drop-zone-filename">{file.name}</p>
                <p className="text-muted text-sm">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="drop-zone-empty">
                <span className="drop-zone-icon">⬆</span>
                <p>Drop DICOM file here</p>
                <p className="text-muted text-sm">or click to browse</p>
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="upload-actions">
            <button
              className="btn btn--primary"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? (
                <span className="btn-loading">
                  <span className="spinner" /> Uploading...
                </span>
              ) : (
                '📤 Upload Scan'
              )}
            </button>

            {uploadResult && (
              <button
                className="btn btn--accent"
                onClick={handleAnalyze}
                disabled={analyzing}
              >
                {analyzing ? (
                  <span className="btn-loading">
                    <span className="spinner" /> Analyzing...
                  </span>
                ) : (
                  '🧠 Run Analysis'
                )}
              </button>
            )}
          </div>

          {error && <div className="alert alert--error">{error}</div>}

          {uploadResult && (
            <div className="upload-result glass-card">
              <h4>Upload Successful</h4>
              <div className="result-details">
                <div className="result-row">
                  <span className="text-muted">Scan ID</span>
                  <span className="badge badge--info">
                    {uploadResult.scan_id || 'N/A'}
                  </span>
                </div>
                {uploadResult.metadata && (
                  <>
                    <div className="result-row">
                      <span className="text-muted">Patient</span>
                      <span>
                        {uploadResult.metadata.patient_name || 'Anonymous'}
                      </span>
                    </div>
                    <div className="result-row">
                      <span className="text-muted">Modality</span>
                      <span>{uploadResult.metadata.modality || 'CR'}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="upload-right">
          <DicomViewer imageData={imageData} />
        </div>
      </div>
    </div>
  );
}
