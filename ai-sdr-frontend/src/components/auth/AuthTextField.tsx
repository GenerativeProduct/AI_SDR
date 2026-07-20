type AuthTextFieldProps = {
  id: string
  label: string
  name: string
  type?: 'text' | 'email'
  value: string
  onChange: (value: string) => void
  autoComplete?: string
  required?: boolean
  placeholder?: string
  disabled?: boolean
}

export function AuthTextField({
  id,
  label,
  name,
  type = 'text',
  value,
  onChange,
  autoComplete,
  required = true,
  placeholder,
  disabled = false,
}: AuthTextFieldProps) {
  return (
    <div className="book-demo-field">
      <label className="book-demo-field__label" htmlFor={id}>
        {label}
      </label>
      <div className="book-demo-control">
        <input
          id={id}
          type={type}
          name={name}
          autoComplete={autoComplete}
          required={required}
          placeholder={placeholder}
          className="book-demo-input"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </div>
  )
}
