import React from 'react'
import { motion } from 'framer-motion'
import { Button } from './Button'

interface PremiumEmptyStateProps {
  icon: React.ElementType
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export function PremiumEmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: PremiumEmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--color-border-strong)] bg-zinc-900/30 p-12 text-center backdrop-blur-sm"
    >
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.15)]">
        <Icon className="h-8 w-8" />
      </div>
      <h3 className="mb-2 text-xl font-semibold tracking-tight text-zinc-100">{title}</h3>
      <p className="mb-8 max-w-sm text-sm leading-relaxed text-zinc-400">{description}</p>
      
      {actionLabel && onAction && (
        <Button onClick={onAction} className="bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)] cursor-pointer transition-colors">
          {actionLabel}
        </Button>
      )}
    </motion.div>
  )
}
