import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ConversationPage from './pages/ConversationPage'
import FlashcardsPage from './pages/FlashcardsPage'
import AnalysisPage from './pages/AnalysisPage'
import GrammarPage from './pages/GrammarPage'
import TextPracticePage from './pages/TextPracticePage'
import AuthPage from './pages/AuthPage'
import NotFoundPage from './pages/NotFoundPage'

/**
 * Root application router.
 *
 * All page components are stubs — Fiona_Frontend (Phase 7) implements
 * the full UI. Sam_Architect provides the routing scaffold so the app
 * renders without errors.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/conversation" element={<ConversationPage />} />
      <Route path="/flashcards" element={<FlashcardsPage />} />
      <Route path="/analysis" element={<AnalysisPage />} />
      <Route path="/grammar" element={<GrammarPage />} />
      <Route path="/text-practice" element={<TextPracticePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
