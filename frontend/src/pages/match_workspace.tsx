import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import {
  createEvent,
  deleteImportJob,
  getEvents,
  getMatch,
  getMatchImports,
  getMatchVideoClips,
  getVideoClipStreamUrl,
  getTeams,
  updateEvent,
  uploadVeoHighlightsImport,
  CreateEventPayload,
  Event,
  ImportJob,
  Match,
  MatchVideoClip,
  Team,
  UpdateEventPayload,
} from '../lib/api'

function StatusBadge({ status }: { status?: string }) {
  const mapping: Record<string, string> = {
    scheduled: 'bg-slate-600 text-white',
    live: 'bg-green-500 text-black',
    finished: 'bg-violet-600 text-white',
    cancelled: 'bg-red-600 text-white',
    postponed: 'bg-yellow-500 text-black',
  }

  const cls = mapping[status ?? 'scheduled'] ?? 'bg-slate-600 text-white'
  return <span className={`px-3 py-1 rounded-full text-sm font-medium ${cls}`}>{status ?? 'scheduled'}</span>
}

function TabContent({ tab, match }: { tab: string; match: Match | null }) {
  const title = `${tab} - Placeholder`
  const description = {
    Overview: 'High-level match metadata and quick insights will appear here.',
    Analysis: 'Tactical and statistical analysis tools and charts will be available here.',
    Report: 'Generate and manage coach-ready reports and exports from here.',
  }[tab]

  return (
    <div className="rounded border border-border p-6 bg-surface3">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="text-muted mt-2">{description}</p>
      {tab === 'Overview' && match && <div className="mt-4 text-sm text-muted">Created at: {match.created_at ?? '-'}</div>}
    </div>
  )
}

export function MatchWorkspacePage() {
  const { matchId } = useParams<{ matchId: string }>()
  const [active, setActive] = useState('Overview')
  const { data: match, isLoading } = useQuery<Match | null>({
    queryKey: ['match', matchId],
    queryFn: () => (matchId ? getMatch(matchId) : Promise.resolve(null)),
  })
  const { data: teams = [] } = useQuery<Team[]>({ queryKey: ['teams'], queryFn: getTeams })

  const teamMap = useMemo(() => {
    const map = new Map<string, Team>()
    teams.forEach((team) => map.set(team.id, team))
    return map
  }, [teams])

  if (!matchId) return <div className="text-muted">Missing match id</div>

  const home = match ? teamMap.get(match.home_team_id) : undefined
  const away = match ? teamMap.get(match.away_team_id) : undefined
  const tabs = ['Overview', 'Import', 'Events', 'Analysis', 'Report']

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface2 p-6 shadow-card">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="space-y-4">
            <Link to="/matches" className="text-sm text-accent hover:text-accent2">Back to Matches</Link>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Match workspace</p>
              <h1 className="mt-2 text-3xl font-semibold text-white">
                {home ? home.short_name || home.name : 'Home'} <span className="text-muted">vs</span> {away ? away.short_name || away.name : 'Away'}
              </h1>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <InfoTile label="Competition" value={match?.competition_id || '-'} />
              <InfoTile label="Season" value={match?.season_id || '-'} />
              <InfoTile label="Venue" value={match?.venue || '-'} />
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-surface3 p-5 shadow-card">
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Match status</p>
            <div className="mt-3 flex items-center gap-3">
              <StatusBadge status={match?.status} />
              <div className="text-sm text-muted">Kickoff: {match ? new Date(match.kickoff_datetime).toLocaleString() : '-'}</div>
            </div>
            <div className="mt-4 text-sm text-muted">Analyst notes provide context for this report and future exports.</div>
          </div>
        </div>

        <div className="mt-6 border-b border-border">
          <nav className="grid grid-cols-5 gap-2">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActive(tab)}
                className={`rounded-3xl px-4 py-3 text-sm font-semibold transition ${
                  active === tab ? 'bg-accent text-black shadow-card' : 'text-muted hover:bg-surface3 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {isLoading && <div className="text-muted">Loading match...</div>}
          {!isLoading && active !== 'Events' && active !== 'Import' && <TabContent tab={active} match={match ?? null} />}
          {!isLoading && active === 'Import' && <ImportTab matchId={matchId} onOpenEvents={() => setActive('Events')} />}
          {!isLoading && active === 'Events' && match && <TimelineTab match={match} teams={teams} />}
        </div>
      </div>
    </section>
  )
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-border bg-surface3 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-muted">{label}</p>
      <p className="mt-2 text-sm text-white">{value}</p>
    </div>
  )
}

function ImportTab({ matchId, onOpenEvents }: { matchId: string; onOpenEvents: () => void }) {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const { data: imports = [], isLoading } = useQuery<ImportJob[]>({
    queryKey: ['matches', matchId, 'imports'],
    queryFn: () => getMatchImports(matchId),
  })
  const latestImport = imports[0]
  const activeImport = latestImport
  const mutation = useMutation({
    mutationFn: (selectedFile: File) => uploadVeoHighlightsImport(matchId, selectedFile),
    onSuccess() {
      setFile(null)
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'video-clips'] })
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'imports'] })
    },
  })
  const deleteMutation = useMutation({
    mutationFn: (importJobId: string) => deleteImportJob(importJobId),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'video-clips'] })
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'imports'] })
    },
  })

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!file || mutation.isPending) return
    mutation.mutate(file)
  }

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-accent2">Veo Highlights ZIP</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Import Veo Highlights</h3>
            <p className="text-muted mt-3 max-w-3xl">
              BFA imports highlight metadata from a Veo ZIP and creates match events linked to this workspace. The provider is fixed to Veo Highlights ZIP for this slice.
            </p>
          </div>
          {activeImport && <ImportStatusBadge status={activeImport.status} />}
        </div>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            <span className="label">Select Veo ZIP</span>
            <input type="file" accept=".zip" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="input" />
          </label>
          <SelectedFileSummary file={file} />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button className="btn-primary" type="submit" disabled={!file || mutation.isPending}>
              {mutation.isPending ? 'Uploading and importing...' : 'Upload ZIP'}
            </button>
            {mutation.isPending && <span className="text-sm text-muted">Import is running. Keep this tab open while BFA stores and reads the ZIP.</span>}
          </div>
        </form>

        {mutation.error && <ImportApiError error={mutation.error as Error} />}
        {activeImport && <ImportSummary job={activeImport} onOpenEvents={onOpenEvents} />}
      </div>

      <div className="rounded-3xl border border-border p-6 bg-surface3 shadow-card">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h4 className="text-white font-medium">Import history</h4>
            <p className="mt-1 text-sm text-muted">Recent Veo import jobs for this match.</p>
          </div>
        </div>
        {isLoading && <div className="mt-4 text-muted">Loading imports...</div>}
        {!isLoading && imports.length === 0 && <div className="mt-4 text-muted">No imports for this match yet.</div>}
        {!isLoading && imports.length > 0 && (
          <ul className="mt-4 space-y-3">
            {imports.map((item) => (
              <ImportHistoryItem
                key={item.id}
                job={item}
                isDeleting={deleteMutation.isPending}
                onDelete={(job) => {
                  const count = getImportSummary(job).eventsCreated
                  const confirmed = window.confirm(
                    `Delete this import?\n\n${count} imported events will be removed.\n\nManual events will NOT be affected.\n\nThis action cannot be undone.`,
                  )
                  if (confirmed) deleteMutation.mutate(job.id)
                }}
              />
            ))}
          </ul>
        )}
        {deleteMutation.error && (
          <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
            {(deleteMutation.error as Error).message}
          </div>
        )}
      </div>
    </div>
  )
}

function ImportStatusBadge({ status }: { status: ImportJob['status'] }) {
  const className = status === 'completed' ? 'bg-green-500 text-black' : status === 'failed' ? 'bg-red-600 text-white' : status === 'deleted' ? 'bg-background text-muted' : 'bg-yellow-500 text-black'
  return <span className={`rounded-full px-3 py-1 text-sm font-semibold capitalize ${className}`}>{status}</span>
}

function SummaryValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-surface3 p-3">
      <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
      <p className="mt-2 text-white">{value}</p>
    </div>
  )
}

function SelectedFileSummary({ file }: { file: File | null }) {
  if (!file) {
    return <div className="rounded-2xl border border-border bg-surface p-4 text-sm text-muted">No ZIP selected yet.</div>
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-muted">Selected file</p>
      <div className="mt-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <span className="font-semibold text-white">{file.name}</span>
        <span className="text-sm text-muted">{formatFileSize(file.size)}</span>
      </div>
    </div>
  )
}

function ImportApiError({ error }: { error: Error }) {
  return (
    <div className="mt-4 rounded-3xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
      <p className="font-semibold text-white">Upload could not start.</p>
      <p className="mt-1">BFA did not receive an import job from the API. Technical detail: {error.message}</p>
    </div>
  )
}

function ImportSummary({ job, onOpenEvents }: { job: ImportJob; onOpenEvents: () => void }) {
  const summary = getImportSummary(job)
  const completedWithZero = job.status === 'completed' && summary.eventsCreated === 0
  const warnings = getWarnings(job)

  return (
    <div className={`mt-6 rounded-3xl border p-5 ${job.status === 'failed' ? 'border-red-500/40 bg-red-500/10' : completedWithZero ? 'border-yellow-500/40 bg-yellow-500/10' : 'border-border bg-surface'}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm text-muted">Latest import</p>
          <p className="mt-1 font-semibold text-white">{job.original_filename || job.filename}</p>
          <p className="mt-2 text-sm text-muted">Provider: Veo Highlights ZIP</p>
        </div>
        <ImportStatusBadge status={job.status} />
      </div>

      <div className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-4">
        <SummaryValue label="Status" value={job.status} />
        <SummaryValue label="Events created" value={String(summary.eventsCreated)} />
        {summary.eventsSkipped !== null && <SummaryValue label="Events skipped" value={String(summary.eventsSkipped)} />}
        <SummaryValue label="Warnings" value={String(warnings.length || job.warnings_count || 0)} />
      </div>

      {job.status === 'completed' && summary.eventsCreated > 0 && (
        <div className="mt-4 rounded-2xl border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-100">
          <p className="font-semibold text-white">Import completed.</p>
          <p className="mt-1">Imported events are now available in the Events tab.</p>
          <button type="button" className="btn-secondary mt-3" onClick={onOpenEvents}>
            Open Events tab
          </button>
        </div>
      )}

      {completedWithZero && (
        <div className="mt-4 rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-100">
          Import completed, but 0 events were created. Review warnings and source metadata before continuing.
        </div>
      )}

      {job.status === 'failed' && (
        <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          <p className="font-semibold text-white">Import failed.</p>
          <p className="mt-1">{job.error_message || 'BFA could not import events from this ZIP.'}</p>
        </div>
      )}

      {warnings.length > 0 && (
        <ul className="mt-4 space-y-2 text-sm text-yellow-100">
          {warnings.map((warning, index) => (
            <li key={`${warning}-${index}`} className="rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-3">
              {warning}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ImportHistoryItem({ job, onDelete, isDeleting }: { job: ImportJob; onDelete: (job: ImportJob) => void; isDeleting: boolean }) {
  const summary = getImportSummary(job)
  const warnings = getWarnings(job)
  const isDeleted = job.status === 'deleted'
  const canDelete = job.status === 'completed'
  return (
    <li className="rounded-3xl border border-border bg-surface p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="font-semibold text-white">{job.original_filename || job.filename}</p>
          <p className="mt-1 text-sm text-muted">Provider: {job.provider === 'veo' ? 'Veo Highlights ZIP' : job.provider}</p>
          <p className="mt-1 text-sm text-muted">Created: {formatDateTime(job.created_at)}</p>
          <p className="mt-1 text-sm text-muted">Completed: {job.completed_at ? formatDateTime(job.completed_at) : '-'}</p>
          {isDeleted && <p className="mt-1 text-sm text-muted">Deleted: {job.deleted_at ? formatDateTime(job.deleted_at) : '-'}</p>}
        </div>
        <div className="flex flex-col gap-3 md:items-end">
          <div className="flex flex-wrap items-center gap-2">
            <ImportStatusBadge status={job.status} />
            <span className="rounded-full bg-background px-3 py-1 text-sm text-muted">{summary.eventsCreated} events</span>
            {(warnings.length > 0 || job.error_message) && (
              <span className={`rounded-full px-3 py-1 text-sm ${job.error_message ? 'bg-red-600 text-white' : 'bg-yellow-500 text-black'}`}>
                {job.error_message ? 'Error' : `${warnings.length} warning${warnings.length === 1 ? '' : 's'}`}
              </span>
            )}
          </div>
          {canDelete && (
            <button type="button" className="btn-secondary" onClick={() => onDelete(job)} disabled={isDeleting}>
              {isDeleting ? 'Deleting...' : 'Delete Import'}
            </button>
          )}
        </div>
      </div>
    </li>
  )
}

function getImportSummary(job: ImportJob) {
  const summary = job.summary ?? {}
  return {
    eventsCreated: toNumber(summary.events_created ?? summary.events_imported ?? job.imported_events_count),
    eventsSkipped: summary.events_skipped === undefined ? null : toNumber(summary.events_skipped),
  }
}

function getWarnings(job: ImportJob): string[] {
  const warnings = job.summary?.warnings
  return Array.isArray(warnings) ? warnings.map((warning) => String(warning)) : []
}

function toNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kilobytes = bytes / 1024
  if (kilobytes < 1024) return `${kilobytes.toFixed(1)} KB`
  return `${(kilobytes / 1024).toFixed(1)} MB`
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString()
}

function formatEventName(eventType: string) {
  return eventType
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function formatMatchTime(event: Event) {
  const prefix = event.period ? `${event.period} ` : ''
  return `${prefix}${event.minute}:${String(event.second).padStart(2, '0')}`
}

function getClipIndex(event: Event): number | null {
  const value = event.raw_payload?.clip_index
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function formatClipReference(event: Event) {
  const clipIndex = getClipIndex(event)
  return clipIndex === null ? null : `Clip #${String(clipIndex).padStart(2, '0')}`
}

function getOriginalFilename(event: Event) {
  const value = event.raw_payload?.filename
  return typeof value === 'string' && value.trim() ? value : null
}

function getPeriodSortValue(period?: string | null) {
  const order: Record<string, number> = { '1H': 1, '2H': 2, ET: 3, P: 4 }
  return period ? order[period] ?? 50 : 99
}

function sortEventsForReview(first: Event, second: Event) {
  const periodDelta = getPeriodSortValue(first.period) - getPeriodSortValue(second.period)
  if (periodDelta !== 0) return periodDelta

  const clockDelta = first.minute * 60 + first.second - (second.minute * 60 + second.second)
  if (clockDelta !== 0) return clockDelta

  const firstClip = getClipIndex(first) ?? Number.MAX_SAFE_INTEGER
  const secondClip = getClipIndex(second) ?? Number.MAX_SAFE_INTEGER
  if (firstClip !== secondClip) return firstClip - secondClip

  const firstCreated = first.created_at ? new Date(first.created_at).getTime() : Number.MAX_SAFE_INTEGER
  const secondCreated = second.created_at ? new Date(second.created_at).getTime() : Number.MAX_SAFE_INTEGER
  if (firstCreated !== secondCreated) return firstCreated - secondCreated

  return first.id.localeCompare(second.id)
}

const EVENT_TYPE_OPTIONS = ['goal', 'shot_on_goal', 'highlight', 'pass', 'cross', 'foul', 'save', 'corner', 'free_kick']

type TeamOption = {
  id: string
  label: string
}

type ReviewStatusFilter = 'all' | 'reviewed' | 'unreviewed'

type EventFilters = {
  eventType: string
  teamId: string
  reviewStatus: ReviewStatusFilter
  search: string
}

function TimelineTab({ match, teams }: { match: Match; teams: Team[] }) {
  const matchId = match.id
  const queryClient = useQueryClient()
  const teamNames = useMemo(() => new Map(teams.map((team) => [team.id, team.name])), [teams])
  const teamOptions = useMemo<TeamOption[]>(
    () => [
      { id: match.home_team_id, label: teamNames.get(match.home_team_id) ?? 'Home Team' },
      { id: match.away_team_id, label: teamNames.get(match.away_team_id) ?? 'Away Team' },
    ],
    [match.away_team_id, match.home_team_id, teamNames],
  )
  const { data: events = [], isLoading } = useQuery<Event[]>({
    queryKey: ['matches', matchId, 'events'],
    queryFn: () => getEvents(matchId),
    enabled: !!matchId,
  })
  const { data: videoClips = [], isLoading: isLoadingClips } = useQuery<MatchVideoClip[]>({
    queryKey: ['matches', matchId, 'video-clips'],
    queryFn: () => getMatchVideoClips(matchId),
    enabled: !!matchId,
  })
  const [showForm, setShowForm] = useState(false)
  const [filters, setFilters] = useState<EventFilters>({ eventType: '', teamId: '', reviewStatus: 'all', search: '' })
  const sortedEvents = useMemo(() => events.slice().sort(sortEventsForReview), [events])
  const eventTypeOptions = useMemo(() => Array.from(new Set(sortedEvents.map((event) => event.event_type))).sort(), [sortedEvents])
  const eventTeamOptions = useMemo<TeamOption[]>(() => {
    const teamIds = Array.from(new Set(sortedEvents.map((event) => event.team_id).filter((teamId): teamId is string => Boolean(teamId)))).sort()
    return teamIds.map((teamId) => ({ id: teamId, label: teamNames.get(teamId) ?? teamId }))
  }, [sortedEvents, teamNames])
  const filteredEvents = useMemo(
    () => sortedEvents.filter((event) => eventMatchesFilters(event, filters, teamNames)),
    [filters, sortedEvents, teamNames],
  )
  const filtersActive = filters.eventType !== '' || filters.teamId !== '' || filters.reviewStatus !== 'all' || filters.search.trim() !== ''
  const videoSync = useEventVideoSync(filteredEvents, videoClips)
  const selectedEvent = videoSync.selectedEvent

  const mutation = useMutation({
    mutationFn: (payload: CreateEventPayload) => createEvent(payload),
    onSuccess() {
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
      setShowForm(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ eventId, payload }: { eventId: string; payload: UpdateEventPayload }) => updateEvent(eventId, payload),
    onSuccess(updated) {
      videoSync.selectEvent(updated.id)
      queryClient.invalidateQueries({ queryKey: ['matches', matchId, 'events'] })
    },
  })

  const [form, setForm] = useState({ event_type: '', minute: '0', second: '0', period: '1H', team_id: '' })

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!form.team_id || !form.event_type) return
    mutation.mutate({
      match_id: matchId,
      team_id: form.team_id,
      event_type: form.event_type,
      minute: Number(form.minute),
      second: Number(form.second),
      period: form.period,
      notes: undefined,
    })
  }

  function updateFilter<K extends keyof EventFilters>(key: K, value: EventFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  function clearFilters() {
    setFilters({ eventType: '', teamId: '', reviewStatus: 'all', search: '' })
  }

  return (
    <div>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Events</h3>
          <p className="text-sm text-muted">Track event timeline entries and match actions.</p>
        </div>
        <button className="btn-secondary inline-flex items-center gap-2" onClick={() => setShowForm((current) => !current)}>
          {showForm ? 'Cancel' : 'Add Event'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="mb-4 rounded border border-border p-4 bg-surface3">
          <div className="grid grid-cols-3 gap-3">
            <input className="input" placeholder="Event type" value={form.event_type} onChange={(e) => update('event_type', e.target.value)} required />
            <input className="input" type="number" min={0} placeholder="Minute" value={form.minute} onChange={(e) => update('minute', e.target.value)} required />
            <input className="input" type="number" min={0} max={59} placeholder="Second" value={form.second} onChange={(e) => update('second', e.target.value)} required />
            <select className="input" value={form.period} onChange={(e) => update('period', e.target.value)}>
              <option value="1H">1H</option>
              <option value="2H">2H</option>
              <option value="ET">ET</option>
              <option value="P">P</option>
            </select>
            <select className="input" value={form.team_id} onChange={(e) => update('team_id', e.target.value)} required>
              <option value="">Select team</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>{team.name}</option>
              ))}
            </select>
            <div />
          </div>

          <div className="mt-3">
            <textarea className="input h-24" placeholder="Notes (optional)" />
          </div>

          <div className="mt-3">
            <button className="btn-primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Adding...' : 'Add Event'}</button>
          </div>
        </form>
      )}

      {isLoading && <div className="text-muted">Loading events...</div>}

      {!isLoading && events.length > 0 && (
        <EventFilterControls
          filters={filters}
          eventTypeOptions={eventTypeOptions}
          teamOptions={eventTeamOptions}
          totalCount={sortedEvents.length}
          filteredCount={filteredEvents.length}
          filtersActive={filtersActive}
          onChange={updateFilter}
          onClear={clearFilters}
        />
      )}

      {!isLoading && events.length === 0 && (
        <div className="rounded-3xl border border-border bg-surface3 p-8 text-center text-muted">
          <p className="text-lg font-semibold text-white">No events have been recorded yet.</p>
          <p className="mt-2">Import a Veo Highlights ZIP or add events manually.</p>
        </div>
      )}

      {!isLoading && events.length > 0 && filteredEvents.length === 0 && (
        <div className="rounded-3xl border border-border bg-surface3 p-8 text-center text-muted">
          <p className="text-lg font-semibold text-white">No events match these filters.</p>
          <p className="mt-2">Clear filters to return to the full event list.</p>
          <button type="button" className="btn-secondary mt-4" onClick={clearFilters} disabled={!filtersActive}>
            Clear filters
          </button>
        </div>
      )}

      {!isLoading && filteredEvents.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
          <ul className="space-y-3">
            {filteredEvents.map((event) => {
                const teamLabel = event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team'
                const clipReference = formatClipReference(event)
                const isSelected = videoSync.selectedEventId === event.id
                return (
                  <li key={event.id}>
                    <button
                      type="button"
                      onClick={() => videoSync.selectEvent(event.id)}
                      className={`w-full rounded-3xl border p-4 text-left transition hover:border-accent hover:bg-surface ${
                        isSelected ? 'border-accent bg-surface' : 'border-border bg-surface3'
                      }`}
                    >
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-3">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="inline-flex items-center gap-2 rounded-full bg-background px-3 py-1 text-sm font-semibold text-white">
                              <Clock size={16} />
                              {formatMatchTime(event)}
                            </span>
                            <EventSourceBadge event={event} />
                            {clipReference && <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">{clipReference}</span>}
                          </div>
                          <div>
                            <p className="text-lg font-semibold text-white">{formatEventName(event.event_type)}</p>
                            <p className="mt-1 text-sm text-muted">Team: {teamLabel}</p>
                          </div>
                        </div>
                        <div className="text-sm text-muted">{event.created_at ? formatDateTime(event.created_at) : ''}</div>
                      </div>
                    </button>
                  </li>
                )
              })}
          </ul>

          <div className="space-y-4">
            <VideoPanel
              event={selectedEvent}
              clip={videoSync.selectedClip}
              eventPosition={videoSync.eventPosition}
              eventsCount={filteredEvents.length}
              canGoPrevious={videoSync.canGoPrevious}
              canGoNext={videoSync.canGoNext}
              onPrevious={videoSync.selectPrevious}
              onNext={videoSync.selectNext}
              isClipMetadataLoading={isLoadingClips}
              videoStatus={videoSync.videoStatus}
              onVideoLoadStart={videoSync.markVideoLoading}
              onVideoReady={videoSync.markVideoReady}
              onVideoError={videoSync.markVideoError}
              resolveTeamLabel={(event) => (event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team')}
            />
            <EventDetailsPanel
              event={selectedEvent}
              resolveTeamLabel={(event) => (event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team')}
              teamOptions={teamOptions}
              onSave={(eventId, payload, onSuccess) => {
                updateMutation.mutate(
                  { eventId, payload },
                  {
                    onSuccess,
                  },
                )
              }}
              isSaving={updateMutation.isPending}
              error={updateMutation.error instanceof Error ? updateMutation.error.message : null}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function EventFilterControls({
  filters,
  eventTypeOptions,
  teamOptions,
  totalCount,
  filteredCount,
  filtersActive,
  onChange,
  onClear,
}: {
  filters: EventFilters
  eventTypeOptions: string[]
  teamOptions: TeamOption[]
  totalCount: number
  filteredCount: number
  filtersActive: boolean
  onChange: <K extends keyof EventFilters>(key: K, value: EventFilters[K]) => void
  onClear: () => void
}) {
  return (
    <div className="mb-4 rounded-3xl border border-border bg-surface3 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <label className="block flex-1">
          <span className="label">Search events</span>
          <input
            className="input"
            type="search"
            value={filters.search}
            onChange={(event) => onChange('search', event.target.value)}
            placeholder="Search type, team, time, notes"
          />
        </label>

        <label className="block min-w-40">
          <span className="label">Event type</span>
          <select className="input" value={filters.eventType} onChange={(event) => onChange('eventType', event.target.value)}>
            <option value="">All event types</option>
            {eventTypeOptions.map((eventType) => (
              <option key={eventType} value={eventType}>
                {formatEventName(eventType)}
              </option>
            ))}
          </select>
        </label>

        <label className="block min-w-40">
          <span className="label">Team</span>
          <select className="input" value={filters.teamId} onChange={(event) => onChange('teamId', event.target.value)}>
            <option value="">All teams</option>
            {teamOptions.map((team) => (
              <option key={team.id} value={team.id}>
                {team.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block min-w-40">
          <span className="label">Review status</span>
          <select className="input" value={filters.reviewStatus} onChange={(event) => onChange('reviewStatus', event.target.value as ReviewStatusFilter)}>
            <option value="all">All statuses</option>
            <option value="reviewed">Reviewed</option>
            <option value="unreviewed">Unreviewed</option>
          </select>
        </label>

        <button type="button" className="btn-secondary" onClick={onClear} disabled={!filtersActive}>
          Clear filters
        </button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted">
        <span className="rounded-full bg-background px-3 py-1" aria-live="polite">
          Showing {filteredCount} / {totalCount} events
        </span>
        {filters.reviewStatus !== 'all' && (
          <span className="rounded-full bg-background px-3 py-1">
            Review: {filters.reviewStatus === 'reviewed' ? 'Reviewed' : 'Unreviewed'}
          </span>
        )}
      </div>
    </div>
  )
}

function eventMatchesFilters(event: Event, filters: EventFilters, teamNames: Map<string, string>) {
  if (filters.eventType && event.event_type !== filters.eventType) return false
  if (filters.teamId && event.team_id !== filters.teamId) return false
  if (filters.reviewStatus === 'reviewed' && !isReviewedEvent(event)) return false
  if (filters.reviewStatus === 'unreviewed' && isReviewedEvent(event)) return false

  const query = filters.search.trim().toLowerCase()
  if (!query) return true
  return eventSearchText(event, teamNames).includes(query)
}

function eventSearchText(event: Event, teamNames: Map<string, string>) {
  const values = [
    event.event_type,
    formatEventName(event.event_type),
    event.team_id ? teamNames.get(event.team_id) ?? event.team_id : 'Unknown Team',
    event.player_id,
    event.period,
    formatMatchTime(event),
    event.notes,
  ]
  return values.filter((value): value is string => Boolean(value)).join(' ').toLowerCase()
}

function isReviewedEvent(event: Event) {
  return Boolean(event.edited_at)
}

type VideoStatus = 'idle' | 'loading' | 'ready' | 'error'

function useEventVideoSync(events: Event[], clips: MatchVideoClip[]) {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [videoStatus, setVideoStatus] = useState<VideoStatus>('idle')
  const selectedEventIndex = selectedEventId ? events.findIndex((event) => event.id === selectedEventId) : -1
  const selectedEvent = selectedEventIndex >= 0 ? events[selectedEventIndex] : null
  const selectedClip = selectedEvent?.video_clip_id ? clips.find((clip) => clip.id === selectedEvent.video_clip_id) ?? null : null

  useEffect(() => {
    if (!selectedEventId) return
    if (!events.some((event) => event.id === selectedEventId)) {
      setSelectedEventId(null)
    }
  }, [events, selectedEventId])

  useEffect(() => {
    if (!selectedEvent || !selectedEvent.video_clip_id) {
      setVideoStatus('idle')
      return
    }
    if (!selectedClip) {
      setVideoStatus('loading')
      return
    }
    setVideoStatus('loading')
  }, [selectedClip?.id, selectedEvent?.video_clip_id])

  function selectEvent(eventId: string) {
    setSelectedEventId(eventId)
  }

  function selectPrevious() {
    if (selectedEventIndex > 0) {
      setSelectedEventId(events[selectedEventIndex - 1].id)
    }
  }

  function selectNext() {
    if (selectedEventIndex >= 0 && selectedEventIndex < events.length - 1) {
      setSelectedEventId(events[selectedEventIndex + 1].id)
    }
  }

  return {
    selectedEventId,
    selectedEvent,
    selectedClip,
    eventPosition: selectedEventIndex >= 0 ? selectedEventIndex + 1 : 0,
    canGoPrevious: selectedEventIndex > 0,
    canGoNext: selectedEventIndex >= 0 && selectedEventIndex < events.length - 1,
    videoStatus,
    selectEvent,
    selectPrevious,
    selectNext,
    markVideoLoading: () => setVideoStatus('loading'),
    markVideoReady: () => setVideoStatus('ready'),
    markVideoError: () => setVideoStatus('error'),
  }
}

function VideoPanel({
  event,
  clip,
  eventPosition,
  eventsCount,
  canGoPrevious,
  canGoNext,
  onPrevious,
  onNext,
  isClipMetadataLoading,
  videoStatus,
  onVideoLoadStart,
  onVideoReady,
  onVideoError,
  resolveTeamLabel,
}: {
  event: Event | null
  clip: MatchVideoClip | null
  eventPosition: number
  eventsCount: number
  canGoPrevious: boolean
  canGoNext: boolean
  onPrevious: () => void
  onNext: () => void
  isClipMetadataLoading: boolean
  videoStatus: VideoStatus
  onVideoLoadStart: () => void
  onVideoReady: () => void
  onVideoError: () => void
  resolveTeamLabel: (event: Event) => string
}) {
  const clipReference = event ? formatClipReference(event) : null
  const playbackAvailable = Boolean(event?.video_clip_id && clip)

  return (
    <aside className="rounded-3xl border border-border bg-surface3 p-5">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Video evidence</p>
          <h4 className="mt-2 text-lg font-semibold text-white">Match clip</h4>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className="btn-secondary" onClick={onPrevious} disabled={!canGoPrevious} aria-label="Select previous event">
            Previous event
          </button>
          <button type="button" className="btn-secondary" onClick={onNext} disabled={!canGoNext} aria-label="Select next event">
            Next event
          </button>
          <span className="rounded-full bg-background px-3 py-1 text-sm text-muted" aria-live="polite">
            {eventPosition > 0 ? `${eventPosition} / ${eventsCount}` : `0 / ${eventsCount}`}
          </span>
        </div>
      </div>

      {event && (
        <div className="mt-4 rounded-2xl border border-border bg-surface p-4 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-white">{formatMatchTime(event)}</span>
            {clipReference && <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">{clipReference}</span>}
          </div>
          <p className="mt-3 font-semibold text-white">{formatEventName(event.event_type)}</p>
          <p className="mt-1 text-muted">Team: {resolveTeamLabel(event)}</p>
        </div>
      )}

      {isClipMetadataLoading && <div className="mt-4 rounded-2xl border border-border bg-surface p-4 text-sm text-muted">Loading clips...</div>}

      {!isClipMetadataLoading && !event && (
        <div className="mt-4 rounded-2xl border border-border bg-surface p-4 text-sm text-muted">
          Select an event to review its video evidence.
        </div>
      )}

      {!isClipMetadataLoading && event && !event.video_clip_id && (
        <div className="mt-4 rounded-2xl border border-border bg-surface p-4 text-sm text-muted">
          This event has no linked video clip.
        </div>
      )}

      {!isClipMetadataLoading && event?.video_clip_id && !clip && (
        <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          The linked video clip metadata could not be loaded.
        </div>
      )}

      {!isClipMetadataLoading && playbackAvailable && clip && (
        <div className="mt-4 space-y-3">
          <div className="relative">
            <video
              key={clip.id}
              className="aspect-video w-full rounded-2xl bg-black"
              src={getVideoClipStreamUrl(clip.id)}
              controls
              preload="metadata"
              onLoadStart={onVideoLoadStart}
              onLoadedMetadata={onVideoReady}
              onCanPlay={onVideoReady}
              onError={onVideoError}
            />
            {videoStatus === 'loading' && (
              <div className="pointer-events-none absolute inset-x-3 top-3 rounded-2xl bg-black/70 px-3 py-2 text-sm text-white">
                Loading clip...
              </div>
            )}
          </div>
          <div className="text-sm text-muted">
            <p className="font-semibold text-white">{clipReference ?? 'Linked clip'}</p>
            <p className="mt-1">{clip.original_filename}</p>
          </div>
          {videoStatus === 'error' && (
            <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
              Clip failed to load. Try selecting the event again or confirm the import files still exist.
            </div>
          )}
        </div>
      )}
    </aside>
  )
}

function EventDetailsPanel({
  event,
  resolveTeamLabel,
  teamOptions,
  onSave,
  isSaving,
  error,
}: {
  event: Event | null
  resolveTeamLabel: (event: Event) => string
  teamOptions: TeamOption[]
  onSave: (eventId: string, payload: UpdateEventPayload, onSuccess: () => void) => void
  isSaving: boolean
  error: string | null
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [form, setForm] = useState({ event_type: '', team_id: '', minute: '0', second: '0', notes: '' })

  if (!event) {
    return (
      <aside className="rounded-3xl border border-border bg-surface3 p-5 text-sm text-muted xl:sticky xl:top-6">
        Select an event to review its details.
      </aside>
    )
  }

  const currentEvent = event
  const clipReference = formatClipReference(currentEvent)
  const originalFilename = getOriginalFilename(currentEvent)
  const eventTypeOptions = EVENT_TYPE_OPTIONS.includes(currentEvent.event_type) ? EVENT_TYPE_OPTIONS : [currentEvent.event_type, ...EVENT_TYPE_OPTIONS]

  function startEdit() {
    setForm({
      event_type: currentEvent.event_type,
      team_id: currentEvent.team_id ?? '',
      minute: String(currentEvent.minute),
      second: String(currentEvent.second),
      notes: currentEvent.notes ?? '',
    })
    setIsEditing(true)
  }

  function cancelEdit() {
    setIsEditing(false)
  }

  function submitEdit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    onSave(
      currentEvent.id,
      {
        event_type: form.event_type,
        team_id: form.team_id || null,
        minute: Number(form.minute),
        second: Number(form.second),
        notes: form.notes.trim() ? form.notes : null,
      },
      () => setIsEditing(false),
    )
  }

  return (
    <aside className="rounded-3xl border border-border bg-surface3 p-5 xl:sticky xl:top-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between xl:flex-col 2xl:flex-row">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full bg-background px-3 py-1 text-sm font-semibold text-white">
            <Clock size={16} />
            {formatMatchTime(event)}
          </span>
          <EventSourceBadge event={event} />
        </div>
        {!isEditing && (
          <button type="button" className="btn-secondary" onClick={startEdit}>
            Edit
          </button>
        )}
      </div>

      <h4 className="mt-4 text-xl font-semibold text-white">{formatEventName(event.event_type)}</h4>

      {isEditing ? (
        <form onSubmit={submitEdit} className="mt-5 space-y-4">
          <label className="block">
            <span className="label">Event type</span>
            <select className="input" value={form.event_type} onChange={(e) => setForm((current) => ({ ...current, event_type: e.target.value }))}>
              {eventTypeOptions.map((eventType) => (
                <option key={eventType} value={eventType}>
                  {formatEventName(eventType)}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="label">Team</span>
            <select className="input" value={form.team_id} onChange={(e) => setForm((current) => ({ ...current, team_id: e.target.value }))}>
              <option value="">Unknown Team</option>
              {teamOptions.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.label}
                </option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="label">Minute</span>
              <input className="input" type="number" min={0} value={form.minute} onChange={(e) => setForm((current) => ({ ...current, minute: e.target.value }))} required />
            </label>
            <label className="block">
              <span className="label">Second</span>
              <input className="input" type="number" min={0} max={59} value={form.second} onChange={(e) => setForm((current) => ({ ...current, second: e.target.value }))} required />
            </label>
          </div>

          <label className="block">
            <span className="label">Notes</span>
            <textarea className="input h-28" value={form.notes} onChange={(e) => setForm((current) => ({ ...current, notes: e.target.value }))} />
          </label>

          {error && <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}

          <div className="flex flex-wrap gap-3">
            <button className="btn-primary" type="submit" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button className="btn-secondary" type="button" onClick={cancelEdit} disabled={isSaving}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="mt-5 space-y-3 text-sm">
          <DetailRow label="Event type" value={formatEventName(event.event_type)} />
          <DetailRow label="Match time" value={formatMatchTime(event)} />
          <DetailRow label="Team" value={resolveTeamLabel(event)} />
          <DetailRow label="Player" value={event.player_id || 'Unknown player'} />
          <DetailRow label="Provider" value={event.provider === 'veo' ? 'Veo' : event.provider || '-'} />
          <DetailRow label="Source" value={event.source === 'import' ? 'Import' : 'Manual'} />
          <DetailRow label="Clip number" value={clipReference || '-'} />
          <DetailRow label="Original filename" value={originalFilename || '-'} />
          <DetailRow label="Video Clip ID" value={event.video_clip_id || '-'} />
          <DetailRow label="Import Job ID" value={event.import_job_id || '-'} />
          <DetailRow label="Edited" value={event.edited_at ? formatDateTime(event.edited_at) : '-'} />
        </div>
      )}

      {event.raw_payload && (
        <details className="mt-5 rounded-2xl border border-border bg-surface p-4">
          <summary className="cursor-pointer text-sm font-semibold text-white">Developer payload</summary>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-muted">
            {JSON.stringify(event.raw_payload, null, 2)}
          </pre>
        </details>
      )}
    </aside>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
      <p className="mt-1 break-words text-white">{value}</p>
    </div>
  )
}

function EventSourceBadge({ event }: { event: Event }) {
  if (event.source === 'import' || event.provider === 'veo') {
    return <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-black">Veo Import</span>
  }
  return <span className="rounded-full bg-background px-3 py-1 text-xs font-semibold text-muted">Manual</span>
}
