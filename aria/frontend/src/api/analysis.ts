import { apiUpload } from './client'

export interface SpeakerSegment {
  text: string
  start: number
  end: number
  speaker: string
  language: string
}

export interface QuizQuestion {
  question: string
  options: string[]
  correct: number
  explanation: string
}

export interface GrammarSpotlight {
  rule: string
  example: string
  correction: string
  frequency: number
}

export interface VoiceBlueprint {
  speaker: string
  tempo_wpm: number
  filler_word_count: number
  vocabulary_richness: number
}

export interface AnalysisSession {
  id: string
  created_at: string
  audio_filename: string
  language: string
  duration_seconds: number
  num_speakers: number
  segments: SpeakerSegment[]
  fluency_score: number | null
  vocabulary: string[]
  status: string
  quiz: QuizQuestion[]
  grammar_spotlights: GrammarSpotlight[]
  voice_blueprints: VoiceBlueprint[]
}

export function analyzeAudio(file: File): Promise<AnalysisSession> {
  const fd = new FormData()
  fd.append('file', file)
  return apiUpload('/v1/sessions/analyze', fd)
}
