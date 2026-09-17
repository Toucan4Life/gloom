export const EMPTY = 0;

export const OBSTACLE = 1;
export const WALL = 2;
export const TRAP = 3;
export const HAZARDOUS_TERRAIN = 4;
export const DIFFICULT_TERRAIN = 5;
export const ICY_TERRAIN = 6;
export const FIRST_TERRAIN_BRUSH = OBSTACLE;
export const LAST_TERRAIN_BRUSH = ICY_TERRAIN;

export const CHARACTER = 7;
export const MONSTER = 8;
export const FIRST_FIGURE_BRUSH = CHARACTER;
export const LAST_FIGURE_BRUSH = MONSTER;

export const ACTIVE_CHARACTER = 9;
export const ACTIVE_MONSTER = 10;
export const CHARACTER_DESTINATION = 11;
export const MONSTER_DESTINATION = 12;
export const FIRST_ACTIVE_BRUSH = ACTIVE_CHARACTER;

export const ACTIVE_FIGURE = 13;
export const THIN_WALL = 14;
export const PROGRESS = 15;
export const FIRST_ACTION_BRUSH = ACTIVE_FIGURE;

export const AOE_EMPTY = 0;
export const AOE_SET = 1;
export const AOE_CENTER = 2;

export const OVERLAY_AOE = 0;
export const OVERLAY_REACH = 1;
export const OVERLAY_SIGHT = 2;

type TerrainBrushCode =
  | typeof OBSTACLE
  | typeof WALL
  | typeof TRAP
  | typeof HAZARDOUS_TERRAIN
  | typeof DIFFICULT_TERRAIN
  | typeof ICY_TERRAIN;

type FigureBrushCode = typeof CHARACTER | typeof MONSTER;
export type ActiveFigureBrush = typeof ACTIVE_CHARACTER | typeof ACTIVE_MONSTER;
export type DestinationBrush = typeof CHARACTER_DESTINATION | typeof MONSTER_DESTINATION;
export type FigureDisplayBrush = FigureBrushCode | ActiveFigureBrush | DestinationBrush;
export type ActionBrush = typeof ACTIVE_FIGURE | typeof THIN_WALL | typeof PROGRESS;
export type Brush =
  | typeof EMPTY
  | TerrainBrushCode
  | FigureBrushCode
  | ActiveFigureBrush
  | DestinationBrush
  | ActionBrush;
export type SelectableBrush =
  | typeof PROGRESS
  | typeof ACTIVE_FIGURE
  | FigureBrushCode
  | TerrainBrushCode
  | typeof THIN_WALL;

export type AoeBrush = typeof AOE_EMPTY | typeof AOE_SET | typeof AOE_CENTER;
export type OverlayBrush = typeof OVERLAY_AOE | typeof OVERLAY_REACH | typeof OVERLAY_SIGHT;
export type TerrainBrushValue = TerrainBrushCode;
export type FigureBrushValue = FigureBrushCode;

export type MovementValue = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type RangeValue = MovementValue;
export type TargetValue = 0 | 1 | 2 | 3 | 4 | 5 | 6;
export type TraitValue = 0 | 1 | 2;
export type InitiativeValue = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type BinaryChoice = 0 | 1 | boolean;

export const TERRAIN_BRUSHES = [
  WALL,
  OBSTACLE,
  TRAP,
  HAZARDOUS_TERRAIN,
  DIFFICULT_TERRAIN,
  ICY_TERRAIN,
  THIN_WALL,
] as const;

export const FIGURE_BRUSHES = [ACTIVE_FIGURE, CHARACTER, MONSTER] as const;
export const MODE_BRUSHES = [PROGRESS] as const;

export const BRUSH_SECTIONS = {
  mode: MODE_BRUSHES,
  figures: FIGURE_BRUSHES,
  terrain: TERRAIN_BRUSHES,
} as const;

export const BRUSH_LABELS: Record<SelectableBrush, string> = {
  [PROGRESS]: 'Play Scenario',
  [ACTIVE_FIGURE]: 'Active Figure',
  [CHARACTER]: 'Character',
  [MONSTER]: 'Monster',
  [WALL]: 'Wall',
  [OBSTACLE]: 'Obstacle',
  [TRAP]: 'Trap',
  [HAZARDOUS_TERRAIN]: 'Hazardous Terrain',
  [DIFFICULT_TERRAIN]: 'Difficult Terrain',
  [ICY_TERRAIN]: 'Icy Terrain',
  [THIN_WALL]: 'Wall Line',
};

export function getActiveFigureBrush(activeFaction: boolean): ActiveFigureBrush {
  return activeFaction ? ACTIVE_CHARACTER : ACTIVE_MONSTER;
}

export function getDestinationBrush(activeFaction: boolean): DestinationBrush {
  return activeFaction ? CHARACTER_DESTINATION : MONSTER_DESTINATION;
}

export function getBrushLabel(brush: SelectableBrush, activeFaction?: boolean): string {
  if (brush === ACTIVE_FIGURE) {
    return activeFaction ? 'Active Character' : 'Active Monster';
  }

  return BRUSH_LABELS[brush];
}

export function isFigureDisplayBrush(brush: Brush): brush is FigureDisplayBrush {
  return brush >= CHARACTER && brush <= MONSTER_DESTINATION;
}
