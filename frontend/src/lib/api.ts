import { fetcher } from './api-client'

export type IdObject = { id: string }

export type Competition = {
  id: string
  name: string
  country: string
  level?: 'first' | 'second' | 'youth'
  competition_type?: 'league' | 'cup' | 'international'
}

export type Season = {
  id: string
  name: string
  competition_id: string
  start_date?: string
  end_date?: string
  is_active?: boolean
}

export type Team = {
  id: string
  name: string
  short_name?: string | null
  city?: string | null
  country?: string | null
  stadium?: string | null
  colours?: string | null
  badge_url?: string | null
  club_id?: string | null
}

export type Match = {
  id: string
  competition_id: string
  season_id: string
  home_team_id: string
  away_team_id: string
  home_team_name?: string | null
  away_team_name?: string | null
  kickoff_datetime: string
  venue: string
  status?: 'scheduled' | 'live' | 'finished' | 'cancelled' | 'postponed'
  analyst_notes?: string | null
  created_at?: string
  updated_at?: string
}

export type Event = {
  id: string
  match_id: string
  import_job_id?: string | null
  team_id?: string | null
  player_id?: string | null
  event_type: string
  minute: number
  second: number
  period?: string | null
  source?: 'manual' | 'import'
  provider?: 'veo' | 'other' | null
  provider_event_id?: string | null
  notes?: string | null
  raw_payload?: Record<string, unknown> | null
  created_at?: string
  edited_at?: string | null
}

export type CreateEventPayload = {
  match_id: string
  team_id: string
  player_id?: string | null
  event_type: string
  minute: number
  second: number
  period: string
  notes?: string | null
}

export type ImportJob = {
  id: string
  match_id: string
  provider: 'veo' | 'csv' | 'other'
  status: 'created' | 'uploaded' | 'extracting' | 'parsing' | 'normalizing' | 'persisting' | 'completed' | 'failed'
  original_filename: string
  filename?: string
  stored_file_path?: string | null
  file_size_bytes?: number | null
  checksum_sha256?: string | null
  raw_metadata?: Record<string, unknown> | null
  summary?: Record<string, unknown> | null
  error_message?: string | null
  completed_at?: string | null
  imported_events_count: number
  warnings_count: number
  created_at: string
  updated_at: string
}

export async function getCompetitions(): Promise<Competition[]> {
  return fetcher('/competitions/')
}

export type UpdateEventPayload = {
  team_id?: string | null
  event_type?: string
  minute?: number
  second?: number
  notes?: string | null
}

export type CreateCompetitionPayload = {
  name: string
  country: string
  level: 'first' | 'second' | 'youth'
  competition_type: 'league' | 'cup' | 'international'
}

export async function createCompetition(payload: CreateCompetitionPayload): Promise<Competition> {
  return fetcher('/competitions/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getSeasons(): Promise<Season[]> {
  return fetcher('/seasons/')
}

export type CreateSeasonPayload = {
  name: string
  start_date: string
  end_date: string
  competition_id: string
  is_active: boolean
}

export async function createSeason(payload: CreateSeasonPayload): Promise<Season> {
  return fetcher('/seasons/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getTeams(): Promise<Team[]> {
  return fetcher('/teams/')
}

export type CreateTeamPayload = {
  name: string
  short_name?: string | null
}

export async function createTeam(payload: CreateTeamPayload): Promise<Team> {
  return fetcher('/teams/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getMatches(): Promise<Match[]> {
  return fetcher('/matches/')
}

export async function getMatch(matchId: string): Promise<Match> {
  return fetcher(`/matches/${matchId}`)
}

export type CreateMatchPayload = {
  competition_id: string
  season_id: string
  home_team_id: string
  away_team_id: string
  kickoff_datetime: string
  venue: string
  analyst_notes?: string | null
}

export type UpdateMatchPayload = Partial<CreateMatchPayload>

export async function createMatch(payload: CreateMatchPayload): Promise<Match> {
  return fetcher('/matches/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateMatch(matchId: string, payload: UpdateMatchPayload): Promise<Match> {
  return fetcher(`/matches/${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function getEvents(matchId: string): Promise<Event[]> {
  // backend supports filtering by match_id query param
  return fetcher(`/events/?match_id=${encodeURIComponent(matchId)}`)
}

export async function createEvent(payload: CreateEventPayload): Promise<Event> {
  return fetcher('/events/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateEvent(eventId: string, payload: UpdateEventPayload): Promise<Event> {
  return fetcher(`/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function getMatchImports(matchId: string): Promise<ImportJob[]> {
  return fetcher(`/matches/${matchId}/imports`)
}

export async function uploadVeoHighlightsImport(matchId: string, file: File): Promise<ImportJob> {
  const body = new FormData()
  body.append('file', file)
  return fetcher(`/matches/${matchId}/imports/veo-highlights`, {
    method: 'POST',
    body,
  })
}
