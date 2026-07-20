import { cn } from '../../lib/cn'

type AuthPasswordFieldProps = {
  id: string
  label: string
  name: string
  value: string
  onChange: (value: string) => void
  autoComplete?: string
  required?: boolean
  disabled?: boolean
}

export function AuthPasswordField({
  id,
  label,
  name,
  value,
  onChange,
  autoComplete = 'current-password',
  required = true,
  disabled = false,
}: AuthPasswordFieldProps) {
  return (
    <div className={cn('book-demo-field')}>
      <label className="book-demo-field__label" htmlFor={id}>
        {label}
      </label>
      <div className="book-demo-control">
        <input
          id={id}
          type="password"
          name={name}
          autoComplete={autoComplete}
          required={required}
          className="book-demo-input"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </div>
  )
}
