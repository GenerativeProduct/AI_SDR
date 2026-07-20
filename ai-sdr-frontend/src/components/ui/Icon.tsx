import type { LucideIcon, LucideProps } from 'lucide-react'
import { cn } from '../../lib/cn'

const sizeClass = {
  xs: 'h-3 w-3',
  sm: 'h-3.5 w-3.5',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
  xl: 'h-7 w-7',
} as const

export type IconSize = keyof typeof sizeClass

type IconProps = {
  icon: LucideIcon
  size?: IconSize
  className?: string
  strokeWidth?: number
} & Omit<LucideProps, 'ref'>

export function Icon({
  icon: IconComponent,
  size = 'md',
  className,
  strokeWidth = 1.75,
  ...props
}: IconProps) {
  return (
    <IconComponent
      className={cn(sizeClass[size], 'shrink-0', className)}
      strokeWidth={strokeWidth}
      aria-hidden
      {...props}
    />
  )
}
