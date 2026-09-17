import type { CSSProperties } from 'react';
import type { TerrainBrush } from '../../lib/scenarioState';

export interface TerrainHexStyle extends CSSProperties {
  fill: string;
  stroke: string;
}

// Indexed by TerrainBrush value (0 = empty … 6 = icy terrain). The board hex
// fill and the terrain glyph accent color are both derived from this single
// palette so the two can never visually drift apart from one another.
export const TERRAIN_HEX_STYLES: readonly TerrainHexStyle[] = [
  {
    fill: '#0f172a',
    fillOpacity: 0.95,
    stroke: '#334155',
    strokeOpacity: 0.92,
    strokeWidth: 1.1,
  },
  {
    fill: '#475569',
    fillOpacity: 0.9,
    stroke: '#cbd5e1',
    strokeOpacity: 0.2,
    strokeWidth: 1.1,
  },
  {
    fill: '#1f2937',
    fillOpacity: 0.95,
    stroke: '#f59e0b',
    strokeOpacity: 0.3,
    strokeWidth: 1.1,
  },
  {
    fill: '#7f1d1d',
    fillOpacity: 0.78,
    stroke: '#fca5a5',
    strokeOpacity: 0.4,
    strokeWidth: 1.1,
  },
  {
    fill: '#7c2d12',
    fillOpacity: 0.8,
    stroke: '#fdba74',
    strokeOpacity: 0.45,
    strokeWidth: 1.1,
  },
  {
    fill: '#3f3f46',
    fillOpacity: 0.88,
    stroke: '#e2e8f0',
    strokeOpacity: 0.24,
    strokeWidth: 1.1,
  },
  {
    fill: '#0c4a6e',
    fillOpacity: 0.78,
    stroke: '#7dd3fc',
    strokeOpacity: 0.42,
    strokeWidth: 1.1,
  },
] as const;

export function getTerrainAccentColor(content: TerrainBrush): string {
  return TERRAIN_HEX_STYLES[content]?.stroke ?? '#f8fafc';
}
