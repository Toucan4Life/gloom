import type { SVGProps } from 'react';

import { FIGURE_RADIUS } from '../lib/constants';
import {
  ACTIVE_CHARACTER,
  ACTIVE_MONSTER,
  CHARACTER,
  CHARACTER_DESTINATION,
  MONSTER,
  MONSTER_DESTINATION,
  type FigureDisplayBrush,
  type InitiativeValue,
  type TraitValue,
} from '../lib/brushes';

const ACTIVE_CHARACTER_TEXT = ['C', 'J', 'F', 'T', 'U'] as const;
const ACTIVE_MONSTER_TEXT = ['M', 'J', 'F', 'T', 'U'] as const;

function getTextIndex(flying: TraitValue, teleport: boolean): number {
  if (teleport) {
    return flying === 2 ? 4 : 3;
  }

  return flying;
}

function getFigurePalette(figure: FigureDisplayBrush): {
  fill: string;
  stroke: string;
  text: string;
} {
  switch (figure) {
    case CHARACTER:
    case ACTIVE_CHARACTER:
    case CHARACTER_DESTINATION:
      return {
        fill: '#22c55e',
        stroke: '#bbf7d0',
        text: '#052e16',
      };
    case MONSTER:
    case ACTIVE_MONSTER:
    case MONSTER_DESTINATION:
      return {
        fill: '#ef4444',
        stroke: '#fecaca',
        text: '#450a0a',
      };
  }
}

export interface FigureIconProps extends Pick<SVGProps<SVGCircleElement>, 'opacity'> {
  x: number;
  y: number;
  figure: FigureDisplayBrush;
  initiative?: InitiativeValue;
  flying?: TraitValue;
  teleport?: boolean | 0 | 1;
  activeFaction?: boolean;
}

export default function FigureIcon({
  x,
  y,
  figure,
  initiative = 1,
  flying = 0,
  teleport = false,
  activeFaction = false,
  opacity,
}: FigureIconProps) {
  const { fill, stroke, text } = getFigurePalette(figure);

  let glyph = '';
  if (figure === ACTIVE_MONSTER) {
    glyph = ACTIVE_MONSTER_TEXT[getTextIndex(flying, Boolean(teleport))];
  } else if (figure === ACTIVE_CHARACTER) {
    glyph = ACTIVE_CHARACTER_TEXT[getTextIndex(flying, Boolean(teleport))];
  } else if (figure === MONSTER_DESTINATION || figure === CHARACTER_DESTINATION) {
    glyph = '✕';
  } else if (activeFaction) {
    glyph = figure === MONSTER ? String(initiative) : 'C';
  } else {
    glyph = figure === CHARACTER ? String(initiative) : 'M';
  }

  return (
    <g opacity={opacity}>
      <circle
        cx={x}
        cy={y}
        r={FIGURE_RADIUS}
        fill={fill}
        fillOpacity={0.95}
        stroke={stroke}
        strokeWidth={1.5}
      />
      <text
        x={x}
        y={y + 4}
        fontSize={FIGURE_RADIUS * 1.08}
        fontWeight={800}
        textAnchor="middle"
        fill={text}
        style={{ paintOrder: 'stroke', stroke: 'rgba(255,255,255,0.28)', strokeWidth: 0.4 }}
      >
        {glyph}
      </text>
    </g>
  );
}
