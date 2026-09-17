import { memo } from 'react';

import {
  DIFFICULT_TERRAIN,
  HAZARDOUS_TERRAIN,
  ICY_TERRAIN,
  OBSTACLE,
  TRAP,
  WALL,
} from '../../lib/brushes';
import type { TerrainBrush } from '../../lib/scenarioState';
import { getTerrainAccentColor } from './terrainPalette';

export interface TerrainGlyphProps {
  content: TerrainBrush;
  x: number;
  y: number;
}

// Draws the same motif used for each terrain brush in the brush picker
// (bricks, rubble, spike, flame, wavy line, snowflake) on top of the board
// hex, so a placed terrain tile is recognizable as the same icon shown in
// the palette rather than a plain, unlabeled color.
export const TerrainGlyph = memo(function TerrainGlyph({ content, x, y }: TerrainGlyphProps) {
  const color = getTerrainAccentColor(content);
  const transform = `translate(${x} ${y})`;

  switch (content) {
    case WALL:
      return (
        <g transform={transform} stroke={color} strokeOpacity={0.85} strokeWidth={1.3} strokeLinecap="round" pointerEvents="none">
          <path d="M-11 -11 H11 M-11 -3.7 H11 M-11 3.7 H11 M-11 11 H11" />
          <path d="M-5.5 -11 V-3.7 M5.5 -11 V-3.7 M0 -3.7 V3.7 M-5.5 3.7 V11 M5.5 3.7 V11" />
        </g>
      );
    case OBSTACLE:
      // Matches the warm rubble/boulder tones used for this brush in the
      // picker (rather than the generic per-type accent color) so the two
      // read as the same "rock pile" motif.
      return (
        <g transform={transform} pointerEvents="none">
          <path
            d="M-8 7 C-9 2 -6 -3 -2 -2 C-1 -7 5 -8 7 -3 C10 -1 10 4 7 7 C3 9 -4 9 -8 7 Z"
            fill="#a8794f"
            stroke="#5c3d21"
            strokeWidth={1}
            strokeLinejoin="round"
          />
        </g>
      );
    case TRAP:
      return (
        <g transform={transform} pointerEvents="none">
          <path
            d="M-5.5 6 L0 -6 L5.5 6 M-3.5 9.5 h7"
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.8}
          />
        </g>
      );
    case HAZARDOUS_TERRAIN:
      return (
        <g transform={transform} pointerEvents="none">
          <path
            d="M-6 7 C-2 3.5 -1 -3.5 1.5 -6 C1.5 -1.5 4.5 0 6 6 C4.5 4.5 2.5 3.5 1 5 C-1 6 -3.5 7 -6 7z"
            fill={color}
            fillOpacity={0.85}
          />
        </g>
      );
    case DIFFICULT_TERRAIN:
      return (
        <g transform={transform} pointerEvents="none">
          <path d="M-7 4.5 Q-3.5 0 0 3.5 T7 3.5" fill="none" stroke={color} strokeLinecap="round" strokeWidth={2} />
        </g>
      );
    case ICY_TERRAIN:
      return (
        <g transform={transform} pointerEvents="none">
          <path d="M0 -7 v14 M-5.5 -3.5 l11 7 M5.5 -3.5 l-11 7" fill="none" stroke={color} strokeLinecap="round" strokeWidth={1.8} />
        </g>
      );
    default:
      return null;
  }
});
