import type { Variants } from 'framer-motion'

export const pageVariants: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.35, ease: [0, 0, 0.2, 1] },
  },
}

export const listVariants: Variants = {
  animate: { transition: { staggerChildren: 0.04 } },
}

export const listItemVariants: Variants = {
  initial: { opacity: 0, x: -8 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.18 } },
}
