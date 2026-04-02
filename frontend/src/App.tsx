import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ReplacementPage from './pages/ReplacementPage'
import SkillMatrixPage from './pages/SkillMatrixPage'
import InsightsPage from './pages/InsightsPage'

function Navigation() {
  return (
    <nav className="navbar">
      <div className="navbar__brand">⚡ Operator IQ</div>
      <div className="navbar__links">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/replacement">Remplacement</NavLink>
        <NavLink to="/skill-matrix">Skill Matrix</NavLink>
        <NavLink to="/insights">Insights</NavLink>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/replacement" element={<ReplacementPage />} />
          <Route path="/skill-matrix" element={<SkillMatrixPage />} />
          <Route path="/insights" element={<InsightsPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
