import { memo, type CSSProperties } from 'react';
import { getGridHexPoints } from './hexUtils';
import type { OverlayHexKind } from './types';

const OVERLAY_STYLES: ReadonlyArray<CSSProperties> = [
  {
    fill: '#f59e0b',
    fillOpacity: 0.3,
    stroke: '#fde68a',
    strokeOpacity: 0.18,
    strokeWidth: 1,
  },
  {
    fill: '#22c55e',
    fillOpacity: 0.22,
    stroke: '#86efac',
    strokeOpacity: 0.16,
    strokeWidth: 1,
  },
  {
    fill: '#38bdf8',
    fillOpacity: 0.18,
    stroke: '#7dd3fc',
    strokeOpacity: 0.18,
    strokeWidth: 1,
  },
];

export interface OverlayHexProps {
  row: number;
  column: number;
  content: OverlayHexKind;
  className?: string;
  style?: CSSProperties;
}

export const OverlayHex = memo(function OverlayHex({
  row,
  column,
  content,
  className,
  style,
}: OverlayHexProps) {
  return (
    <polygon
      className={className}
      points={getGridHexPoints(column, row)}
      pointerEvents='none'
      style={{ vectorEffect: 'non-scaling-stroke', ...OVERLAY_STYLES[content] ?? OVERLAY_STYLES[0], ...style }}
    />
  );
});
