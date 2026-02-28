import { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  List,
  Key,
  HelpCircle,
  Layers,
  BarChart,
  Download,
  Loader2,
  AlertCircle,
  FileAudio,
  Cpu,
  Clock,
  ArrowRight,
} from 'lucide-react';
import './App.css';

// Use relative paths — Vite proxy forwards /api to the FastAPI backend
const API_URL = '/api';

function App() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [step, setStep] = useState(null);
  const [errorStatus, setErrorStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('transcript');
  const fileInputRef = useRef(null);

  // Poll for status when processing
  useEffect(() => {
    let interval;
    if (jobId && status === 'processing') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/status/${jobId}`);
          if (!res.ok) throw new Error('Failed to fetch status');
          const data = await res.json();

          if (data.status === 'done') {
            setStatus('done');
            fetchResults(jobId);
          } else if (data.status === 'error') {
            setStatus('error');
            setErrorStatus(data.error || 'An error occurred during processing.');
          } else {
            setStep(data.step || 'Processing...');
          }
        } catch (err) {
          console.error(err);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [jobId, status]);

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    setErrorStatus(null);
    setStep('Uploading file...');

    const formData = new FormData();
    formData.append('audio_file', file);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed. Please try again.');
      const data = await res.json();
      setJobId(data.job_id);
      setStatus('processing');
    } catch (err) {
      console.error(err);
      setStatus('error');
      setErrorStatus(err.message);
    }
  };

  const fetchResults = async (id) => {
    try {
      const res = await fetch(`${API_URL}/results/${id}`);
      if (!res.ok) throw new Error('Failed to fetch results');
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
      setStatus('error');
      setErrorStatus('Could not load final results.');
    }
  };

  const downloadPDF = () => {
    if (!jobId) return;
    window.open(`${API_URL}/export/${jobId}`, '_blank');
  };

  const resetState = () => {
    setFile(null);
    setJobId(null);
    setStatus('idle');
    setStep(null);
    setErrorStatus(null);
    setResults(null);
    setActiveTab('transcript');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="app-container">
      {/* ── Top Navigation Bar ─────────────────────── */}
      <nav className="app-nav">
        <div className="nav-brand">
          <div className="nav-logo">IL</div>
          <div>
            <div className="nav-title">IntelliLecture</div>
            <div className="nav-subtitle">AI-Powered Lecture Notes</div>
          </div>
        </div>
        <div className="nav-actions">
          {status === 'done' && (
            <button onClick={resetState}>New Upload</button>
          )}
        </div>
      </nav>

      {/* ── Accent Strip ──────────────────────────── */}
      <div className="accent-strip" />

      {/* ── Main Content ──────────────────────────── */}
      <main className="app-main">

        {/* ── IDLE: Upload View ───────────────────── */}
        {status === 'idle' && (
          <div className="upload-view">
            <span className="upload-badge">Upload Lecture</span>

            <h1 className="upload-heading">
              Transform Your Lectures Into Smart Study Notes
            </h1>

            <p className="upload-subtext">
              Upload an audio recording and our AI pipeline will generate
              transcripts, summaries, quizzes, flashcards, and more.
            </p>

            <div className="upload-meta-pills">
              <span className="meta-pill"><FileAudio size={14} /> MP3, WAV supported</span>
              <span className="meta-pill"><Cpu size={14} /> 7-step AI pipeline</span>
              <span className="meta-pill"><Clock size={14} /> ~10-25 min processing</span>
            </div>

            <div
              className="drop-zone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="drop-zone-inner">
                <div className="upload-icon-wrap">
                  <UploadCloud size={28} />
                </div>
                <h3>Drop your audio file here</h3>
                <p>or click to browse files</p>
              </div>
              <input
                type="file"
                accept="audio/*"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden-input"
              />
            </div>

            {file && (
              <div className="file-selected">
                <FileText size={18} />
                <span>{file.name}</span>
                <button className="btn-primary" onClick={handleUpload}>
                  Process Lecture <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Processing View ─────────────────────── */}
        {(status === 'uploading' || status === 'processing') && (
          <div className="processing-view">
            <Loader2 size={48} className="spinner" />
            <h2>Processing Your Lecture</h2>
            <p className="step-text">{step}</p>
            <div className="progress-bar-container">
              <div className="progress-bar-indeterminate" />
            </div>
          </div>
        )}

        {/* ── Error View ──────────────────────────── */}
        {status === 'error' && (
          <div className="error-view">
            <AlertCircle size={48} className="error-icon" />
            <h2>Something went wrong</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{errorStatus}</p>
            <button className="btn-primary" onClick={resetState}>
              Try Again <ArrowRight size={16} />
            </button>
          </div>
        )}

        {/* ── Dashboard View ──────────────────────── */}
        {status === 'done' && results && (
          <div className="dashboard-view">
            <div className="dashboard-header">
              <div className="dashboard-title">
                <h2>{results.filename}</h2>
                <div className="dashboard-actions">
                  {/* --- TEMPORARILY DISABLED ---
                  <button className="btn-outline" onClick={downloadPDF}>
                    <Download size={15} /> Export PDF
                  </button>
                  ---------------------------- */}
                  <button className="btn-secondary" onClick={resetState}>
                    New Upload
                  </button>
                </div>
              </div>

              <div className="tabs">
                {[
                  { id: 'transcript', label: 'Transcript', icon: <FileText size={15} /> },
                  { id: 'summary', label: 'Summary', icon: <List size={15} /> },
                  // --- TEMPORARILY DISABLED ---
                  // { id: 'keywords', label: 'Keywords', icon: <Key size={15} /> },
                  // { id: 'quiz', label: 'Quiz', icon: <HelpCircle size={15} /> },
                  // { id: 'flashcards', label: 'Flashcards', icon: <Layers size={15} /> },
                  // { id: 'metrics', label: 'Metrics', icon: <BarChart size={15} /> },
                  // ----------------------------
                ].map((t) => (
                  <button
                    key={t.id}
                    className={`tab ${activeTab === t.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(t.id)}
                  >
                    {t.icon} {t.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="tab-content">
              {activeTab === 'transcript' && (
                <div className="content-card">
                  <h3>Full Transcript</h3>
                  <div className="scrollable-content">
                    {results.cleaned_text || results.transcript?.text || 'No transcript generated.'}
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="grid-2">
                  <div className="content-card">
                    <h3>Executive Overview</h3>
                    <p>{results.summary?.overview || 'No overview generated.'}</p>
                  </div>
                  <div className="content-card">
                    <h3>Key Points</h3>
                    <ul className="bulled-list">
                      {results.summary?.key_points?.map((pt, idx) => (
                        <li key={idx}>{pt}</li>
                      )) || <li>No key points generated.</li>}
                    </ul>
                  </div>
                </div>
              )}

              {/* --- TEMPORARILY DISABLED --- */}
              {/* {activeTab === 'keywords' && (
                <div className="content-card">
                  <h3>Top Keyphrases</h3>
                  <div className="tags-container">
                    {results.keywords && results.keywords.length > 0 ? (
                      results.keywords.map((kw, idx) => (
                        <span className="tag" key={idx}>{kw[0]}</span>
                      ))
                    ) : (
                      <p>No keywords extracted.</p>
                    )}
                  </div>

                  <h3 className="mt-6">Topic Segments</h3>
                  {results.segments && results.segments.length > 0 ? (
                    <div className="timeline">
                      {results.segments.map((seg, idx) => (
                        <div className="timeline-item" key={idx}>
                          <p>{seg}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No topic segments identified.</p>
                  )}
                </div>
              )} */}

              {/* {activeTab === 'quiz' && (
                <div className="content-card">
                  <h3>Generated Quiz</h3>
                  {results.quiz ? (
                    <div className="pre-formatted">{results.quiz}</div>
                  ) : (
                    <p>No quiz generated.</p>
                  )}
                </div>
              )} */}

              {/* {activeTab === 'flashcards' && (
                <div className="content-card">
                  <h3>Flashcards</h3>
                  {results.flashcards ? (
                    <div className="pre-formatted">{results.flashcards}</div>
                  ) : (
                    <p>No flashcards generated.</p>
                  )}
                </div>
              )} */}

              {/* {activeTab === 'metrics' && (
                <div className="content-card">
                  <h3>Evaluation Metrics</h3>
                  <div className="metrics-grid">
                    <div className="metric-box">
                      <span className="metric-label">Word Error Rate (WER)</span>
                      <span className="metric-value">
                        {results.metrics?.wer !== undefined
                          ? results.metrics.wer.toFixed(4)
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label">ROUGE-1-F</span>
                      <span className="metric-value">
                        {results.metrics?.rouge1_f !== undefined
                          ? results.metrics.rouge1_f.toFixed(4)
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="metric-box">
                      <span className="metric-label">ROUGE-L-F</span>
                      <span className="metric-value">
                        {results.metrics?.rougel_f !== undefined
                          ? results.metrics.rougel_f.toFixed(4)
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              )} */}
              {/* ---------------------------- */}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
