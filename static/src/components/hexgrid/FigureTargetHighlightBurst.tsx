import { memo, type CSSProperties } from 'react';
import { FIGURE_RADIUS } from '../../lib/constants';
import type { FigureTargetHighlightType } from './types';

const HIGHLIGHT_STYLES: ReadonlyArray<CSSProperties> = [
  { fill: '#fb7185', fillOpacity: 0.4, stroke: '#fecdd3', strokeOpacity: 0.85, strokeWidth: 2 },
  { fill: '#f59e0b', fillOpacity: 0.55, stroke: '#fde68a', strokeOpacity: 0.95, strokeWidth: 2.2 },
  { fill: '#a855f7', fillOpacity: 0.55, stroke: '#e9d5ff', strokeOpacity: 0.95, strokeWidth: 2.2 },
  { fill: '#f59e0b', fillOpacity: 0.55, stroke: '#fde68a', strokeOpacity: 0.95, strokeWidth: 2.2 },
  { fill: '#a855f7', fillOpacity: 0.55, stroke: '#e9d5ff', strokeOpacity: 0.95, strokeWidth: 2.2 },
];

const HALF_TRIANGLE_WIDTH = 0.26 * FIGURE_RADIUS;
const TRIANGLE_BASE_HEIGHT = FIGURE_RADIUS + 1;
const TRIANGLE_TOP_HEIGHT = 1.75 * FIGURE_RADIUS;

export interface FigureTargetHighlightBurstProps {
  x: number;
  y: number;
  type: FigureTargetHighlightType;
  clipPath?: string | null;
  className?: string;
  style?: CSSProperties;
}

export const FigureTargetHighlightBurst = memo(function FigureTargetHighlightBurst({
  x,
  y,
  type,
  clipPath,
  className,
  style,
}: FigureTargetHighlightBurstProps) {
  const trianglePoints = [
    x - HALF_TRIANGLE_WIDTH, y - TRIANGLE_BASE_HEIGHT,
    x, y - TRIANGLE_TOP_HEIGHT,
    x + HALF_TRIANGLE_WIDTH, y - TRIANGLE_BASE_HEIGHT,
  ].join(',');
  const burstStyle = HIGHLIGHT_STYLES[type] ?? HIGHLIGHT_STYLES[0];

  const triangles = [];
  for (let index = 0; index < 6; index += 1) {
    const angle = 30 + 60 * index;
    triangles.push(
      <polygon
        className={className}
        key={index}
        points={trianglePoints}
        pointerEvents='none'
        transform={`rotate(${angle} ${x} ${y})`}
        style={{ vectorEffect: 'non-scaling-stroke', ...burstStyle, ...style }}
      />,
    );
  }

  return (
    <g clipPath={clipPath ?? undefined}>
      <circle
        className={className}
        cx={x}
        cy={y}
        r={FIGURE_RADIUS}
        pointerEvents='none'
        style={{ vectorEffect: 'non-scaling-stroke', ...burstStyle, ...style }}
      />
      {triangles}
    </g>
  );
});
