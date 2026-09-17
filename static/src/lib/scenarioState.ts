import {
  AOE_SIZE,
  GRID_SIZE,
} from './constants';
import {
  CHARACTER,
  EMPTY,
  ICY_TERRAIN,
  MONSTER,
  OBSTACLE,
} from './brushes';

export const NULL_INDEX = -1;
export const MAX_INITIATIVE = 9;

export const GAME_RULES_FROST = 0;
export const GAME_RULES_GLOOM = 1;
export const GAME_RULES_JOTL = 2;

export const GAME_RULES_OPTIONS = [
  [GAME_RULES_FROST, 'Frosthaven'],
  [GAME_RULES_GLOOM, 'Gloomhaven'],
  [GAME_RULES_JOTL, 'Jaws of the Lion'],
] as const;

export const STATE_KEYS = [
  'rotate_grid',
  'grid',
  'figures',
  'initiatives',
  'walls',
  'active_figure_index',
  'move',
  'range',
  'target',
  'flying',
  'teleport',
  'muddled',
  'game_rules',
  'aoe_grid',
  'active_faction',
] as const;

export const SIMPLE_STATE_KEYS = [
  'move',
  'range',
  'target',
  'flying',
  'muddled',
  'active_faction',
  'rotate_grid',
] as const;

export interface ScenarioFieldInfo {
  bits: number;
  min: number;
  max: number;
}

export type ZeroToNine = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type ZeroToSix = 0 | 1 | 2 | 3 | 4 | 5 | 6;
export type ZeroToTwo = 0 | 1 | 2;
export type OneToNine = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type BooleanBit = 0 | 1 | boolean;
export type TerrainBrush = typeof EMPTY | typeof OBSTACLE | 2 | 3 | 4 | 5 | typeof ICY_TERRAIN;
export type FigureBrush = typeof EMPTY | typeof CHARACTER | typeof MONSTER;
export type GameRulesValue = typeof GAME_RULES_FROST | typeof GAME_RULES_GLOOM | typeof GAME_RULES_JOTL;

export type ScenarioStateKey = (typeof STATE_KEYS)[number];
export type SimpleStateKey = (typeof SIMPLE_STATE_KEYS)[number];
export type ScenarioFieldInfoKey = SimpleStateKey | 'teleport' | 'game_rules' | 'jotl';

export const SIMPLE_STATE_PROPERTIES: Record<ScenarioFieldInfoKey, ScenarioFieldInfo> = {
  move: {
    bits: 4,
    min: 0,
    max: 9,
  },
  range: {
    bits: 4,
    min: 0,
    max: 9,
  },
  target: {
    bits: 3,
    min: 0,
    max: 6,
  },
  flying: {
    bits: 2,
    min: 0,
    max: 2,
  },
  teleport: {
    bits: 1,
    min: 0,
    max: 1,
  },
  muddled: {
    bits: 1,
    min: 0,
    max: 1,
  },
  jotl: {
    bits: 1,
    min: 0,
    max: 1,
  },
  game_rules: {
    bits: 2,
    min: 0,
    max: 2,
  },
  active_faction: {
    bits: 1,
    min: 0,
    max: 1,
  },
  rotate_grid: {
    bits: 1,
    min: 0,
    max: 1,
  },
};

export interface ScenarioState {
  grid: TerrainBrush[];
  figures: FigureBrush[];
  initiatives: OneToNine[];
  walls: boolean[];
  active_figure_index: number;
  move: ZeroToNine;
  range: ZeroToNine;
  target: ZeroToSix;
  flying: ZeroToTwo;
  teleport: BooleanBit;
  muddled: BooleanBit;
  game_rules: GameRulesValue;
  aoe_grid: boolean[];
  active_faction: BooleanBit;
  rotate_grid: BooleanBit;
}

export function createDefaultScenarioState(): ScenarioState {
  return {
    grid: Array(GRID_SIZE).fill(EMPTY) as TerrainBrush[],
    figures: Array(GRID_SIZE).fill(EMPTY) as FigureBrush[],
    initiatives: Array(GRID_SIZE).fill(1) as OneToNine[],
    walls: Array(3 * GRID_SIZE).fill(false),
    active_figure_index: NULL_INDEX,
    move: 2,
    range: 0,
    target: 1,
    flying: 0,
    teleport: 0,
    muddled: 0,
    game_rules: GAME_RULES_FROST,
    aoe_grid: Array(AOE_SIZE).fill(false),
    active_faction: false,
    rotate_grid: false,
  };
}
