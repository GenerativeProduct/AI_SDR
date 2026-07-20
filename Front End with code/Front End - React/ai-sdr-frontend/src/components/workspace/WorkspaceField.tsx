import { cn } from '../../lib/cn'
import { WsControlField } from './controls/WsControlField'
import { WsInput } from './controls/WsInput'
import { WsTextarea } from './controls/WsTextarea'

type WorkspaceFieldProps = {
  id: string
  label: string
  name?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'textarea'
  value: string
  onChange: (value: string) => void
  onBlur?: () => void
  error?: string
  hint?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  rows?: number
  className?: string
}

export function WorkspaceField({
  id,
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  hint,
  placeholder,
  required,
  disabled,
  rows = 4,
  className,
}: WorkspaceFieldProps) {
  return (
    <WsControlField
      id={id}
      label={label}
      hint={hint}
      error={error}
      required={required}
      className={cn('ws-field', className)}
    >
      {type === 'textarea' ? (
        <WsTextarea
          id={id}
          name={name ?? id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={rows}
          invalid={Boolean(error)}
        />
      ) : (
        <WsInput
          id={id}
          name={name ?? id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          invalid={Boolean(error)}
        />
      )}
    </WsControlField>
  )
}
