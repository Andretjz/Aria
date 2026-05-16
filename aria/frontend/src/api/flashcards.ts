import { apiFetch } from './client'

export interface VocabItem {
  word: string
  cefr_level?: string | null
  definition?: string | null
  example_sentence?: string | null
}

export interface FlashcardDeck {
  id: string
  name: string
  source_language: string
  target_language: string
  created_at: string
}

export interface Flashcard {
  id: string
  deck_id: string
  word: string
  cefr_level: string | null
  definition: string | null
  example_sentence: string | null
  created_at: string
}

export interface FlashcardReview {
  id: string
  flashcard_id: string
  ease_factor: number
  interval: number
  repetitions: number
  next_review: string
  last_reviewed: string | null
}

export interface FlashcardDue {
  card: Flashcard
  review: FlashcardReview
}

export interface FlashcardStats {
  total_cards: number
  cards_due: number
  cards_mastered: number
}

export interface GenerateResponse {
  deck: FlashcardDeck
  cards_created: number
  cards: Flashcard[]
}

export function getStats(): Promise<FlashcardStats> {
  return apiFetch('/v1/flashcards/stats')
}

export function getDueCards(): Promise<FlashcardDue[]> {
  return apiFetch('/v1/flashcards/due')
}

export function submitReview(flashcard_id: string, quality: number): Promise<FlashcardReview> {
  return apiFetch('/v1/flashcards/review', {
    method: 'POST',
    body: JSON.stringify({ flashcard_id, quality }),
  })
}

export function generateDeck(
  deck_name: string,
  source_language: string,
  target_language: string,
  vocabulary: VocabItem[],
): Promise<GenerateResponse> {
  return apiFetch('/v1/flashcards/generate', {
    method: 'POST',
    body: JSON.stringify({ deck_name, source_language, target_language, vocabulary }),
  })
}
