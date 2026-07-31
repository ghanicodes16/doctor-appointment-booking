// components/Spinner.jsx - a simple loading indicator.
// Shown while the app is waiting for data from the backend.
export default function Spinner() {
  return (
    <div className="spinner-wrap" role="status" aria-label="Loading">
      <div className="spinner"></div>
    </div>
  )
}
