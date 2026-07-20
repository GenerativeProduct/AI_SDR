import { useMemo } from 'react'
import { WsControlField } from './WsControlField'
import { WsInput } from './WsInput'

type WsCommaFieldProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  hint?: string
  error?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
}

function parseTags(value: string) {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

export function WsCommaField({
  id,
  label,
  value,
  onChange,
  hint,
  error,
  placeholder,
  disabled,
  required,
}: WsCommaFieldProps) {
  const tags = useMemo(() => parseTags(value), [value])

  return (
    <WsControlField id={id} label={label} hint={hint} error={error} required={required}>
      <WsInput
        id={id}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        invalid={Boolean(error)}
        onChange={(e) => onChange(e.target.value)}
      />
      {tags.length > 0 ? (
        <ul className="ws-control-tags" aria-label={`${label} tags`}>
          {tags.map((tag) => (
            <li key={tag}>
              <span className="ws-control-tag">{tag}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </WsControlField>
  )
}
