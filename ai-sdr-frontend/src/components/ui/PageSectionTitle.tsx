import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

export function PageSectionTitle({
  children,
  className,
  as: Tag = 'h2',
  ...props
}: HTMLAttributes<HTMLElement> & {
  children: ReactNode
  as?: 'h2' | 'h3' | 'p'
}) {
  return (
    <Tag
      className={cn(
        'text-xl font-semibold leading-tight tracking-tight text-text-primary',
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  )
}
