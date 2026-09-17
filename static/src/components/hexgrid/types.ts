export type GridPoint = readonly [number, number];
export type GridLine = readonly [GridPoint, GridPoint];
export type DebugGeometry = readonly [number, readonly [GridPoint] | GridLine];

export type HexInteractionHandler = (primary: boolean, index: number) => void;
export type HexMouseDownHandler = (
  pageX: number,
  pageY: number,
  index: number,
  column: number,
  row: number,
) => void;
export type HexMouseUpHandler = (index: number) => void;

export type WallSide = 0 | 1 | 2;

export const OVERLAY_HEX_KIND = {
  AOE: 0,
  REACH: 1,
  SIGHT: 2,
} as const;
export type OverlayHexKind = (typeof OVERLAY_HEX_KIND)[keyof typeof OVERLAY_HEX_KIND];

export const AOE_HEX_STATE = {
  EMPTY: 0,
  SET: 1,
  CENTER: 2,
} as const;
export type AOEHexState = (typeof AOE_HEX_STATE)[keyof typeof AOE_HEX_STATE];

export const FIGURE_TARGET_HIGHLIGHT = {
  ATTACKED: 0,
  MONSTER_FOCUS: 1,
  CHARACTER_FOCUS: 2,
  ATTACKED_MONSTER_FOCUS: 3,
  ATTACKED_CHARACTER_FOCUS: 4,
} as const;
export type FigureTargetHighlightType = (typeof FIGURE_TARGET_HIGHLIGHT)[keyof typeof FIGURE_TARGET_HIGHLIGHT];
