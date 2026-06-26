import { fetcher } from './api-client'

export type IdObject = { id: string }

export type Competition = {
  id: string
  name: string
  country: string
}

export type Season = {
  id: string
  name: string
  competition_id: string
}

export type Team = {
  id: string
  name: string
  short_name: string
}

export type Match = {
  id: string
  competition_id: string
  season_id: string
  home_team_id: string
  away_team_id: string
  kickoff_datetime: string
  venue: string
  analyst_notes?: string | null
  created_at?: string
  updated_at?: string
}

export type Event = {
  id: string
  match_id: string
  team_id: string
  player_id?: string | null
  event_type: string
  minute: number
  second: number
  period: string
  notes?: string | null
  raw_payload?: Record<string, unknown> | null
  created_at?: string
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

export async function getCompetitions(): Promise<Competition[]> {
  return fetcher('/competitions')
}

export async function getSeasons(): Promise<Season[]> {
  return fetcher('/seasons')
}

export async function getTeams(): Promise<Team[]> {
  return fetcher('/teams')
}

export async function getMatches(): Promise<Match[]> {
  return fetcher('/matches')
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
  return fetcher('/matches', {
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
  return fetcher(`/events?match_id=${encodeURIComponent(matchId)}`)
}

export async function createEvent(payload: CreateEventPayload): Promise<Event> {
  return fetcher('/events', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
