import { ref } from 'vue'

export interface UiPreferences {
  logRefreshIntervalMs: number
  defaultLogLines: number
  requireDeleteConfirmText: boolean
}

const PREFERENCES_KEY = 'dian_ui_preferences'

const DEFAULT_PREFERENCES: UiPreferences = {
  logRefreshIntervalMs: 3000,
  defaultLogLines: 100,
  requireDeleteConfirmText: true,
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function normalizePreferences(partial: Partial<UiPreferences>): UiPreferences {
  return {
    logRefreshIntervalMs: clampNumber(
      Number(partial.logRefreshIntervalMs ?? DEFAULT_PREFERENCES.logRefreshIntervalMs),
      1000,
      10000,
    ),
    defaultLogLines: clampNumber(
      Number(partial.defaultLogLines ?? DEFAULT_PREFERENCES.defaultLogLines),
      50,
      500,
    ),
    requireDeleteConfirmText: Boolean(
      partial.requireDeleteConfirmText ?? DEFAULT_PREFERENCES.requireDeleteConfirmText,
    ),
  }
}

function loadPreferences(): UiPreferences {
  const raw = localStorage.getItem(PREFERENCES_KEY)
  if (!raw) {
    return { ...DEFAULT_PREFERENCES }
  }

  try {
    const parsed = JSON.parse(raw) as Partial<UiPreferences>
    return normalizePreferences(parsed)
  } catch {
    return { ...DEFAULT_PREFERENCES }
  }
}

const preferences = ref<UiPreferences>(loadPreferences())

function savePreferences(nextPreferences: UiPreferences): void {
  const normalized = normalizePreferences(nextPreferences)
  preferences.value = normalized
  localStorage.setItem(PREFERENCES_KEY, JSON.stringify(normalized))
}

function resetPreferences(): void {
  preferences.value = { ...DEFAULT_PREFERENCES }
  localStorage.setItem(PREFERENCES_KEY, JSON.stringify(DEFAULT_PREFERENCES))
}

export function useUiPreferences() {
  return {
    preferences,
    savePreferences,
    resetPreferences,
    defaultPreferences: DEFAULT_PREFERENCES,
  }
}
