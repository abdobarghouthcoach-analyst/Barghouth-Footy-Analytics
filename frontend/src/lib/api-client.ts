export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/+$/, '')

type ApiErrorBody = {
  detail?: unknown
  message?: unknown
  error?: unknown
}

export async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const base = API_BASE_URL
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${base}${normalizedPath}`

  const headers = {
    ...(init && init.headers ? (init.headers as Record<string, string>) : {}),
  }

  if (init && init.body && !(init.body instanceof FormData) && !('Content-Type' in headers)) {
    headers['Content-Type'] = 'application/json'
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...init,
      headers,
    })
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('API network error', {
        url,
        method: init?.method ?? 'GET',
        error,
      })
    }
    throw new Error(`Unable to reach the API at ${url}. Check that the backend is running and CORS is configured.`)
  }

  if (!response.ok) {
    const body = await readErrorBody(response)
    const message = errorMessageFromBody(body) ?? `API request failed with ${response.status}`
    if (import.meta.env.DEV) {
      console.error('API request failed', {
        url,
        method: init?.method ?? 'GET',
        status: response.status,
        body,
      })
    }
    throw new Error(message)
  }

  // assume JSON responses for API endpoints used by the frontend
  return response.json() as Promise<T>
}

async function readErrorBody(response: Response): Promise<ApiErrorBody | string | null> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as ApiErrorBody
  } catch {
    return text
  }
}

function errorMessageFromBody(body: ApiErrorBody | string | null): string | null {
  if (!body) return null
  if (typeof body === 'string') return body
  return stringifyDetail(body.detail ?? body.message ?? body.error)
}

function stringifyDetail(detail: unknown): string | null {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => stringifyDetailItem(item)).filter(Boolean).join('; ') || null
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return null
}

function stringifyDetailItem(item: unknown): string | null {
  if (item && typeof item === 'object' && 'msg' in item) {
    const record = item as { loc?: unknown; msg?: unknown }
    const location = Array.isArray(record.loc) ? record.loc.join('.') : null
    return `${location ? `${location}: ` : ''}${String(record.msg)}`
  }
  return stringifyDetail(item)
}
