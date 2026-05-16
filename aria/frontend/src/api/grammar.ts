import { apiFetch } from './client'

export interface GrammarDeficit {
  rule: string
  total_frequency: number
  example: string | null
}

export function getDeficits(): Promise<GrammarDeficit[]> {
  return apiFetch('/v1/grammar/deficits')
}
