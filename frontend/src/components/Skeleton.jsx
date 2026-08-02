// components/Skeleton.jsx - shimmering placeholder while content loads.
export default function Skeleton({ className = '', variant = 'text', width, height }) {
  const style = { width, height }
  return <div className={`skeleton skeleton-${variant} ${className}`} style={style} />
}
