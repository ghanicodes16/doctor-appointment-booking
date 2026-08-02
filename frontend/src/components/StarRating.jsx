// components/StarRating.jsx - visual 5-star rating (display + interactive).
import { StarIcon } from './icons.jsx'

export default function StarRating({ value = 0, onChange, size = 'sm' }) {
  const stars = [1, 2, 3, 4, 5]
  return (
    <div className={`stars ${onChange ? 'stars-interactive' : ''}`} role={onChange ? 'radiogroup' : undefined}>
      {stars.map((n) => (
        <span
          key={n}
          className={`star ${n <= Math.round(value) ? 'star-filled' : ''}`}
          onClick={onChange ? () => onChange(n) : undefined}
          role={onChange ? 'radio' : undefined}
          aria-checked={onChange ? n <= Math.round(value) : undefined}
          aria-label={onChange ? `${n} star` : undefined}
        >
          <StarIcon size={size === 'lg' ? 'lg' : 'sm'} />
        </span>
      ))}
    </div>
  )
}
