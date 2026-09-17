// Re-exports the canonical figure-target highlight enum from the hex grid
// module (see ../hexgrid/types.ts) under the names used elsewhere in the
// brush/figure UI, so both areas share a single source of truth.
import { FIGURE_TARGET_HIGHLIGHT } from './hexgrid/types';
import type { FigureTargetHighlightType } from './hexgrid/types';

export const ATTACKED = FIGURE_TARGET_HIGHLIGHT.ATTACKED;
export const MONSTER_FOCUS = FIGURE_TARGET_HIGHLIGHT.MONSTER_FOCUS;
export const CHARACTER_FOCUS = FIGURE_TARGET_HIGHLIGHT.CHARACTER_FOCUS;
export const ATTACKED_MONSTER_FOCUS = FIGURE_TARGET_HIGHLIGHT.ATTACKED_MONSTER_FOCUS;
export const ATTACKED_CHARACTER_FOCUS = FIGURE_TARGET_HIGHLIGHT.ATTACKED_CHARACTER_FOCUS;

export type FigureHighlightType = FigureTargetHighlightType;
