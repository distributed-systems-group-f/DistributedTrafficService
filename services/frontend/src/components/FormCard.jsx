import './FormCard.css'

export default function FormCard({ title, children }) {
  return (
    <div className="form-card-wrapper">
      <div className="form-card">
        <h2 className="form-card-title">{title}</h2>
        {children}
      </div>
    </div>
  )
}
