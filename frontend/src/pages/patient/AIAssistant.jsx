// pages/patient/AIAssistant.jsx - ShifaBook AI Health Assistant.
//
// The patient can upload a medical document (JPG/JPEG/PNG/WEBP/PDF), get a
// real Groq analysis, chat about it, and jump straight to doctor search for
// the recommended specialty. All AI calls go through the backend - the Groq
// API key never touches the browser.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  getAIReports,
  getAIReport,
  getAIMessages,
  uploadAIReport,
  deleteAIReport,
  analyzeAIReport,
  chatAIReport,
} from '../../api/client.js'
import { useToast } from '../../context/ToastContext.jsx'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import Skeleton from '../../components/Skeleton.jsx'
import {
  SparklesIcon,
  UploadIcon,
  ChatIcon,
  SendIcon,
  FileIcon,
  TrashIcon,
  RobotIcon,
  ShieldIcon,
} from '../../components/icons.jsx'
import { formatDate } from '../../utils/format.js'
import { compressImage } from '../../utils/compressImage.js'

const ACCEPTED = ['jpg', 'jpeg', 'png', 'webp', 'pdf']
const MAX_SIZE = 10 * 1024 * 1024

const URGENCY = {
  green: { label: 'General Guidance', cls: 'urg-green', icon: '🟢' },
  orange: { label: 'Doctor Consultation Recommended', cls: 'urg-orange', icon: '🟠' },
  red: { label: 'Urgent Medical Attention', cls: 'urg-red', icon: '🔴' },
}

const formatSize = (bytes) =>
  bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`

export default function AIAssistant() {
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [reports, setReports] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [messages, setMessages] = useState([])

  const [loadingReports, setLoadingReports] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [sending, setSending] = useState(false)

  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(null) // null = idle, number = percent
  const [dragging, setDragging] = useState(false)
  const [input, setInput] = useState('')
  const fileInputRef = useRef(null)
  const chatBottomRef = useRef(null)

  const refreshReports = useCallback(async () => {
    try {
      const list = await getAIReports()
      setReports(list)
    } catch {
      /* keep old list */
    } finally {
      setLoadingReports(false)
    }
  }, [])

  const loadDetail = useCallback(
    async (id) => {
      setLoadingDetail(true)
      setDetail(null)
      try {
        setDetail(await getAIReport(id))
      } catch {
        /* handled by empty state */
      } finally {
        setLoadingDetail(false)
      }
    },
    []
  )

  useEffect(() => {
    refreshReports()
  }, [refreshReports])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setMessages([])
      return
    }
    loadDetail(selectedId)
    getAIMessages(selectedId)
      .then((r) => setMessages(r.messages))
      .catch(() => {})
  }, [selectedId, loadDetail])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages, sending])

  const pickFile = (file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!ACCEPTED.includes(ext)) {
      showToast({ type: 'error', message: 'Only JPG, JPEG, PNG, WEBP or PDF files are allowed.' })
      return
    }
    if (file.size > MAX_SIZE) {
      showToast({ type: 'error', message: 'File is too large. Maximum size is 10 MB.' })
      return
    }
    setSelectedFile(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  const handleUpload = async () => {
    if (!selectedFile || uploading !== null) return
    setUploading(0)
    try {
      const fileToUpload = selectedFile.type.startsWith('image/')
        ? await compressImage(selectedFile, 600, 0.5)
        : selectedFile // PDFs pass through untouched

      const created = await uploadAIReport(fileToUpload, setUploading)
      setSelectedFile(null)
      showToast({ type: 'success', message: 'Document uploaded' })
      await refreshReports()
      setSelectedId(created.id)
    } catch (err) {
      showToast({ type: 'error', message: err.message })
      setUploading(null)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedId || analyzing) return
    setAnalyzing(true)
    try {
      const updated = await analyzeAIReport(selectedId)
      setDetail(updated)
      showToast({ type: 'success', message: 'Analysis complete' })
      refreshReports()
    } catch (err) {
      showToast({ type: 'error', message: err.message })
      loadDetail(selectedId)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending || !selectedId) return
    setSending(true)
    setInput('')
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: 'user', message: text }])
    try {
      const res = await chatAIReport(selectedId, text)
      setMessages(res.messages)
    } catch (err) {
      showToast({ type: 'error', message: err.message })
      getAIMessages(selectedId)
        .then((r) => setMessages(r.messages))
        .catch(() => {})
    } finally {
      setSending(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document and its analysis?')) return
    try {
      await deleteAIReport(id)
      showToast({ type: 'success', message: 'Document deleted' })
      if (selectedId === id) setSelectedId(null)
      refreshReports()
    } catch (err) {
      showToast({ type: 'error', message: err.message })
    }
  }

  const urgency = detail?.analysis ? URGENCY[detail.analysis.urgency] : null

  return (
    <DashboardLayout title="ShifaBook AI Health Assistant">
      <section className="card ai-hero">
        <div className="ai-hero-head">
          <div className="ai-hero-icon">
            <SparklesIcon size="lg" />
          </div>
          <div>
            <h2 className="ai-hero-title">Understand your medical documents</h2>
            <p className="ai-hero-text">
              Upload a report, prescription or test result and the ShifaBook AI will explain it in simple
              language, highlight what to ask your doctor, and suggest the right specialist.
            </p>
          </div>
        </div>
        <div className="ai-safety">
          <ShieldIcon size="sm" />
          Educational tool only - the AI never diagnoses and never replaces a qualified doctor.
        </div>
      </section>

      <div className="ai-grid">
        <div className="ai-main">
          {/* Uploader */}
          <section className="card">
            <div className="card-head">
              <h2 className="card-title">
                <UploadIcon size="sm" /> Upload a document
              </h2>
            </div>

            {selectedFile ? (
              <div className="ai-file-card">
                {selectedFile.type.startsWith('image/') ? (
                  <img
                    className="ai-file-preview"
                    src={URL.createObjectURL(selectedFile)}
                    alt="Preview"
                    onLoad={(e) => URL.revokeObjectURL(e.target.src)}
                  />
                ) : (
                  <div className="ai-file-preview pdf">
                    <FileIcon size="lg" />
                    <span>PDF</span>
                  </div>
                )}
                <div className="ai-file-info">
                  <strong>{selectedFile.name}</strong>
                  <span>{formatSize(selectedFile.size)}</span>
                </div>
                {uploading === null ? (
                  <>
                    <button className="btn btn-ghost btn-sm" onClick={() => setSelectedFile(null)} disabled={uploading !== null}>
                      Remove
                    </button>
                    <button className="btn btn-primary btn-sm" onClick={handleUpload}>
                      Upload
                    </button>
                  </>
                ) : (
                  <div className="ai-progress-wrap">
                    <div className="ai-progress">
                      <div className="ai-progress-bar" style={{ width: `${uploading}%` }} />
                    </div>
                    <span className="ai-progress-label">{uploading}%</span>
                  </div>
                )}
              </div>
            ) : (
              <div
                className={`ai-dropzone${dragging ? ' dragging' : ''}`}
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragging(true)
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp,.pdf"
                  hidden
                  onChange={(e) => {
                    pickFile(e.target.files?.[0])
                    e.target.value = ''
                  }}
                />
                <UploadIcon size="lg" />
                <strong>Drag & drop your document here</strong>
                <span>or click to browse · JPG, PNG, WEBP or PDF · max 10 MB</span>
              </div>
            )}
          </section>

          {/* Selected report + analysis */}
          {selectedId ? (
            <section className="card">
              {loadingDetail ? (
                <Skeleton height="180px" />
              ) : detail ? (
                <>
                  <div className="ai-report-head">
                    <div className="ai-report-name">
                      <FileIcon size="sm" />
                      <div>
                        <strong>{detail.original_filename}</strong>
                        <span>
                          {detail.file_type.toUpperCase()} · {formatSize(detail.file_size)} · {formatDate(detail.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="ai-report-actions">
                      <span className={`status-pill ${detail.analysis_status === 'analyzed' ? 'status-on' : detail.analysis_status === 'failed' ? 'status-off' : 'status-pend'}`}>
                        {detail.analysis_status === 'analyzed' ? 'Analyzed' : detail.analysis_status === 'failed' ? 'Failed' : 'Pending'}
                      </span>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(detail.id)} title="Delete">
                        <TrashIcon size="sm" />
                      </button>
                    </div>
                  </div>

                  {detail.analysis ? (
                    <div className="ai-analysis">
                      {urgency && (
                        <div className={`ai-urgency ${urgency.cls}`}>
                          <span className="ai-urgency-icon">{urgency.icon}</span>
                          <div>
                            <strong>{urgency.label}</strong>
                            <span>{detail.analysis.safety_message}</span>
                          </div>
                        </div>
                      )}

                      <h3 className="ai-section-title">{detail.analysis.report_type}</h3>
                      <p className="ai-summary">{detail.analysis.summary}</p>

                      {detail.analysis.important_findings?.length > 0 && (
                        <div className="ai-findings">
                          <h4>Important findings</h4>
                          <ul className="ai-list warn">
                            {detail.analysis.important_findings.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {detail.analysis.normal_findings?.length > 0 && (
                        <div className="ai-findings">
                          <h4>Normal findings</h4>
                          <ul className="ai-list ok">
                            {detail.analysis.normal_findings.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {detail.analysis.possible_explanations?.length > 0 && (
                        <div className="ai-findings">
                          <h4>Possible explanations</h4>
                          <ul className="ai-list">
                            {detail.analysis.possible_explanations.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {detail.analysis.questions_for_doctor?.length > 0 && (
                        <div className="ai-findings">
                          <h4>Questions to ask your doctor</h4>
                          <ul className="ai-list q">
                            {detail.analysis.questions_for_doctor.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {detail.analysis.recommended_specialty && (
                        <div className="ai-doctor-rec">
                          <div>
                            <strong>Recommended specialist</strong>
                            <span>{detail.analysis.recommended_specialty}</span>
                          </div>
                          <button
                            className="btn btn-primary"
                            onClick={() =>
                              navigate(`/search?specialization=${encodeURIComponent(detail.analysis.recommended_specialty)}`)
                            }
                          >
                            Find {detail.analysis.recommended_specialty} doctors
                          </button>
                        </div>
                      )}
                    </div>
                  ) : detail.analysis_status === 'failed' ? (
                    <div className="ai-error">
                      <p>{detail.error_message || 'Analysis failed. Please try again.'}</p>
                      <button className="btn btn-primary btn-sm" onClick={handleAnalyze} disabled={analyzing}>
                        Try again
                      </button>
                    </div>
                  ) : (
                    <div className="ai-analyze-cta">
                      <RobotIcon size="lg" />
                      <p>Your document is ready. Run the AI analysis to get a simple explanation.</p>
                      <button className="btn btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                        {analyzing ? 'Analyzing…' : 'Analyze my report'}
                      </button>
                    </div>
                  )}
                </>
              ) : null}
            </section>
          ) : null}

          {/* Chat */}
          {selectedId ? (
            <section className="card ai-chat-card">
              <div className="card-head">
                <h2 className="card-title">
                  <ChatIcon size="sm" /> Ask ShifaBook AI
                </h2>
              </div>
              <div className="ai-chat-window">
                {messages.length === 0 && !sending ? (
                  <div className="ai-chat-empty">
                    <RobotIcon size="lg" />
                    <span>Ask anything about this document, e.g. “Is this concerning?”</span>
                  </div>
                ) : (
                  <>
                    {messages.map((m) => (
                      <div key={m.id} className={`chat-msg ${m.role}`}>
                        {m.role === 'assistant' && <RobotIcon size="xs" />}
                        {m.message}
                      </div>
                    ))}
                    {sending && (
                      <div className="chat-msg assistant">
                        <RobotIcon size="xs" />
                        ShifaBook AI is thinking…
                      </div>
                    )}
                    <div ref={chatBottomRef} />
                  </>
                )}
              </div>
              <form className="ai-chat-form" onSubmit={handleSend}>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about this report…"
                  disabled={sending}
                />
                <button type="submit" className="btn btn-primary" disabled={sending || !input.trim()} title="Send">
                  <SendIcon size="sm" />
                </button>
              </form>
            </section>
          ) : null}
        </div>

        {/* History */}
        <aside className="card ai-history">
          <div className="card-head">
            <h2 className="card-title">
              <FileIcon size="sm" /> Your documents
            </h2>
          </div>
          {loadingReports ? (
            <Skeleton height="120px" />
          ) : reports.length === 0 ? (
            <div className="ai-history-empty">No documents yet. Upload your first report to get started.</div>
          ) : (
            <ul className="ai-history-list">
              {reports.map((r) => (
                <li key={r.id} className={r.id === selectedId ? 'active' : ''}>
                  <button className="ai-history-item" onClick={() => setSelectedId(r.id)}>
                    <span className="ai-history-file">
                      <FileIcon size="sm" />
                      <span>
                        <strong>{r.original_filename}</strong>
                        <small>
                          {formatDate(r.created_at)} ·{' '}
                          {r.analysis_status === 'analyzed' ? r.report_type || 'Analyzed' : r.analysis_status}
                        </small>
                      </span>
                    </span>
                    {r.urgency_level && <span className={`status-pill ${URGENCY[r.urgency_level]?.cls || ''}`}>{URGENCY[r.urgency_level]?.label.split(' ')[0]}</span>}
                  </button>
                  <button className="ai-history-del" title="Delete" onClick={() => handleDelete(r.id)}>
                    <TrashIcon size="xs" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </DashboardLayout>
  )
}