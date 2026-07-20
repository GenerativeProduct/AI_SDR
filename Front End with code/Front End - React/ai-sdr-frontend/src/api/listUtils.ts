import type { ListResponse } from './types'

/** Unwrap list endpoints that return either a raw array or `{ items, total }`. */
export function unwrapListItems<T>(data: T[] | ListResponse<T> | undefined | null): T[] {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (typeof data === 'object' && Array.isArray((data as ListResponse<T>).items)) {
    return (data as ListResponse<T>).items
  }
  return []
}
