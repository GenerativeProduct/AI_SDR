import { Toaster } from 'sonner'
import { useUiStore } from '../../stores/uiStore'

export function ThemedToaster() {
  const theme = useUiStore((s) => s.theme)
  return <Toaster theme={theme} position="top-right" richColors closeButton />
}
