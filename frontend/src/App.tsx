import { Route, Routes } from 'react-router-dom'
import { DashboardPage } from './pages/dashboard'
import { MatchesPage } from './pages/matches'
import { CompetitionsPage } from './pages/competitions'
import { SeasonsPage } from './pages/seasons'
import { SettingsPage } from './pages/settings'
import { AppShell } from './components/app-shell'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/competitions" element={<CompetitionsPage />} />
        <Route path="/seasons" element={<SeasonsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  )
}

export default App
