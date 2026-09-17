import {
  CHARACTER,
  EMPTY,
  LAST_FIGURE_BRUSH,
  LAST_TERRAIN_BRUSH,
} from './brushes';
import { AOE_SIZE, GRID_SIZE } from './constants';
import type { ScenarioState, ScenarioStateKey } from './scenarioState';
import { GAME_RULES_OPTIONS, MAX_INITIATIVE, NULL_INDEX, STATE_KEYS } from './scenarioState';

const VERSION_KEY = 'version';
const STORAGE_TEST_KEY = '__gloom_storage_test__';
const GAME_RULES_VALUES = GAME_RULES_OPTIONS.map(([value]) => value);

function isIntegerInRange(value: unknown, min: number, max: number): value is number {
  return Number.isInteger(value) && (value as number) >= min && (value as number) <= max;
}

function isBooleanBit(value: unknown): value is boolean | 0 | 1 {
  return typeof value === 'boolean' || value === 0 || value === 1;
}

function isBooleanArray(value: unknown, length: number): value is boolean[] {
  return Array.isArray(value)
    && value.length === length
    && value.every((element) => typeof element === 'boolean');
}

function isTerrainArray(value: unknown): value is ScenarioState['grid'] {
  return Array.isArray(value)
    && value.length === GRID_SIZE
    && value.every((element) => isIntegerInRange(element, EMPTY, LAST_TERRAIN_BRUSH));
}

function isFigureArray(value: unknown): value is ScenarioState['figures'] {
  return Array.isArray(value)
    && value.length === GRID_SIZE
    && value.every((element) => element === EMPTY || isIntegerInRange(element, CHARACTER, LAST_FIGURE_BRUSH));
}

function isInitiativeArray(value: unknown): value is ScenarioState['initiatives'] {
  return Array.isArray(value)
    && value.length === GRID_SIZE
    && value.every((element) => isIntegerInRange(element, 1, MAX_INITIATIVE));
}

function isScenarioStateValue(
  key: ScenarioStateKey,
  value: unknown,
): value is ScenarioState[ScenarioStateKey] {
  switch (key) {
    case 'rotate_grid':
    case 'active_faction':
    case 'teleport':
    case 'muddled':
      return isBooleanBit(value);
    case 'grid':
      return isTerrainArray(value);
    case 'figures':
      return isFigureArray(value);
    case 'initiatives':
      return isInitiativeArray(value);
    case 'walls':
      return isBooleanArray(value, 3 * GRID_SIZE);
    case 'active_figure_index':
      return value === NULL_INDEX || isIntegerInRange(value, 0, GRID_SIZE - 1);
    case 'move':
    case 'range':
      return isIntegerInRange(value, 0, 9);
    case 'target':
      return isIntegerInRange(value, 0, 6);
    case 'flying':
      return isIntegerInRange(value, 0, 2);
    case 'game_rules':
      return GAME_RULES_VALUES.includes(value as (typeof GAME_RULES_VALUES)[number]);
    case 'aoe_grid':
      return isBooleanArray(value, AOE_SIZE);
    default:
      return false;
  }
}

export function isLocalStorageAvailable(): boolean {
  let storage: Storage | undefined;

  try {
    storage = window.localStorage;
    storage.setItem(STORAGE_TEST_KEY, STORAGE_TEST_KEY);
    storage.removeItem(STORAGE_TEST_KEY);
    return true;
  }
  catch (error) {
    return error instanceof DOMException && (
      error.code === 22
      || error.code === 1014
      || error.name === 'QuotaExceededError'
      || error.name === 'NS_ERROR_DOM_QUOTA_REACHED'
    ) && (storage?.length ?? 0) !== 0;
  }
}

export function storeScenarioState(state: Partial<ScenarioState>): void {
  if (!isLocalStorageAvailable()) {
    return;
  }

  try {
    STATE_KEYS.forEach((key) => {
      if (key in state) {
        const value = state[key as ScenarioStateKey];
        localStorage.setItem(key, JSON.stringify(value));
      }
    });

    localStorage.setItem(VERSION_KEY, DATA_VERSION);
  }
  catch {
    // Swallow storage failures so a blocked/quota-limited browser does not
    // break editor boot or scenario updates.
  }
}

export function restoreScenarioState(): Partial<ScenarioState> | null {
  if (!isLocalStorageAvailable()) {
    return null;
  }

  try {
    const previousVersion = localStorage.getItem(VERSION_KEY);
    if (previousVersion !== DATA_VERSION) {
      localStorage.clear();
      localStorage.setItem(VERSION_KEY, DATA_VERSION);
      return null;
    }

    const restoredState: Partial<ScenarioState> = {};
    for (const key of STATE_KEYS) {
      const value = localStorage.getItem(key);
      if (!value) {
        continue;
      }

      const parsedValue = JSON.parse(value) as unknown;
      if (!isScenarioStateValue(key, parsedValue)) {
        localStorage.clear();
        localStorage.setItem(VERSION_KEY, DATA_VERSION);
        return null;
      }

      (restoredState as Record<ScenarioStateKey, ScenarioState[ScenarioStateKey]>)[key] = parsedValue;
    }

    localStorage.setItem(VERSION_KEY, DATA_VERSION);
    return restoredState;
  }
  catch {
    try {
      localStorage.clear();
      localStorage.setItem(VERSION_KEY, DATA_VERSION);
    }
    catch {
      // Ignore follow-up storage errors for the same reason as above.
    }
    return null;
  }
}
