import './FormCard.css'

export default function FormCard({ eyebrow, title, subtitle, children, maxWidth }) {
  return (
    <div className="form-card-wrapper">
      <div className="form-card" style={maxWidth ? { maxWidth } : {}}>
        {eyebrow && <p className="form-card-eyebrow">{eyebrow}</p>}
        {title && <h1 className="form-card-title">{title}</h1>}
        {subtitle && <p className="form-card-subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>
  )
}
