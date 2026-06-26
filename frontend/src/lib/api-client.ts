export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/+$/, '')

export async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const base = API_BASE_URL
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${base}${normalizedPath}`

  const headers = {
    ...(init && init.headers ? (init.headers as Record<string, string>) : {}),
  }

  if (init && init.body && !('Content-Type' in headers)) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    ...init,
    headers,
  })

  if (!response.ok) {
    throw new Error(`API request failed with ${response.status}`)
  }

  // assume JSON responses for API endpoints used by the frontend
  return response.json() as Promise<T>
}
