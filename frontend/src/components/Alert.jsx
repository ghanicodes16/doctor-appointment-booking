// components/Alert.jsx - a dismissible message banner.
// Used for success messages, error messages and information.
// The "type" prop controls the colour: success (green), error (red) or info (blue).
export default function Alert({ type = 'info', children, onClose }) {
  return (
    <div className={`alert alert-${type}`} role="alert">
      <span>{children}</span>
      {onClose && (
        <button className="alert-close" onClick={onClose} aria-label="Dismiss">
          &times;
        </button>
      )}
    </div>
  )
}
