import { apiFetch } from './client'

export interface UserPreferences {
  input_lang: string
  target_lang: string
  feedback_lang: string
  ui_lang: string
}

export interface User {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  preferences?: UserPreferences
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export function login(body: LoginRequest): Promise<User> {
  return apiFetch('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function register(body: RegisterRequest): Promise<User> {
  return apiFetch('/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function logout(): Promise<void> {
  return apiFetch('/v1/auth/logout', { method: 'POST' })
}

export function getMe(): Promise<User> {
  return apiFetch('/v1/auth/me')
}

export function updatePreferences(prefs: Partial<UserPreferences>): Promise<User> {
  return apiFetch('/v1/auth/me/preferences', {
    method: 'PATCH',
    body: JSON.stringify(prefs),
  })
}
