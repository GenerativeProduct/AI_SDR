import { useLayoutEffect, useRef, type RefObject } from 'react'

function observerOptionsKey(options?: IntersectionObserverInit): string {
  if (!options) return ''
  const threshold = options.threshold
  const thresholdKey = Array.isArray(threshold)
    ? threshold.join(',')
    : threshold ?? ''
  return `${options.rootMargin ?? ''}|${thresholdKey}`
}

function isAlreadyInView(el: HTMLElement, rootMargin = '0px 0px -8% 0px'): boolean {
  const rect = el.getBoundingClientRect()
  const vh = window.innerHeight || document.documentElement.clientHeight

  let topInset = 0
  let bottomInset = 0
  const parts = rootMargin.trim().split(/\s+/)
  if (parts.length === 4) {
    const parseInset = (value: string, axisSize: number) => {
      if (value.endsWith('%')) return (parseFloat(value) / 100) * axisSize
      if (value.endsWith('px')) return parseFloat(value)
      return parseFloat(value) || 0
    }
    topInset = parseInset(parts[0], vh)
    bottomInset = parseInset(parts[2], vh)
  }

  return rect.top < vh - bottomInset && rect.bottom > topInset
}

export function useScrollReveal<T extends HTMLElement>(
  options?: IntersectionObserverInit,
): RefObject<T | null> {
  const ref = useRef<T>(null)
  const optionsKey = observerOptionsKey(options)
  const optionsRef = useRef(options)
  optionsRef.current = options

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReduced) {
      el.classList.add('is-visible')
      return
    }

    const merged: IntersectionObserverInit = {
      threshold: 0.12,
      rootMargin: '0px 0px -8% 0px',
      ...optionsRef.current,
    }

    if (isAlreadyInView(el, merged.rootMargin ?? '0px 0px -8% 0px')) {
      el.classList.add('is-visible')
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('is-visible')
          observer.disconnect()
        }
      },
      merged,
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [optionsKey])

  return ref
}
