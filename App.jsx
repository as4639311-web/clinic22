import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { useApp } from './state'
import { BottomNav } from './components/ui'
import Login from './pages/Login'
import Home from './pages/Home'
import Book from './pages/Book'
import { AppointmentDetail, Appointments } from './pages/Appointments'
import { PlanDetail, Plans } from './pages/Plans'
import Card from './pages/Card'
import Share from './pages/Share'
import { Article, Library } from './pages/Library'
import { Messages, Thread } from './pages/Messages'
import Assistant from './pages/Assistant'
import Notifications from './pages/Notifications'
import Settings from './pages/Settings'
import Emergency from './pages/Emergency'

export default function App() {
  const { session } = useApp()
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])

  if (!session) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    )
  }
  return (
    <div className="shell">
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/book" element={<Book />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/appointments/:id" element={<AppointmentDetail />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/plans/:id" element={<PlanDetail />} />
          <Route path="/card" element={<Card />} />
          <Route path="/card/share" element={<Share />} />
          <Route path="/library" element={<Library />} />
          <Route path="/library/:id" element={<Article />} />
          <Route path="/messages" element={<Messages />} />
          <Route path="/messages/:id" element={<Thread />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/urgent" element={<Emergency />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  )
}
