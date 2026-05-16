import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ConversationPage from './pages/ConversationPage'
import FlashcardsPage from './pages/FlashcardsPage'
import AnalysisPage from './pages/AnalysisPage'
import GrammarPage from './pages/GrammarPage'
import TextPracticePage from './pages/TextPracticePage'
import AuthPage from './pages/AuthPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Layout>
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
    </Layout>
  )
}
