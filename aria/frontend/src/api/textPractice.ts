import { apiUpload } from './client'

export interface CEFRVocabItem {
  word: string
  cefr_level: string
  definition: string
}

export interface TextQuizQuestion {
  question: string
  options: string[]
  correct: number
  explanation: string
}

export interface TextGrammarSpotlight {
  rule: string
  example: string
  correction: string
  frequency: number
}

export interface TextPracticeResult {
  detected_language: string
  translated_text: string
  vocabulary: CEFRVocabItem[]
  quiz: TextQuizQuestion[]
  grammar_spotlights: TextGrammarSpotlight[]
}

export function uploadText(file: File): Promise<TextPracticeResult> {
  const fd = new FormData()
  fd.append('file', file)
  return apiUpload('/v1/text-practice/upload', fd)
}
