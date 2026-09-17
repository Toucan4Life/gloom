import { memo, type CSSProperties } from 'react';
import { SCALE } from '../../lib/constants';
import { gridPointToSvgPoint } from './hexUtils';
import type { GridPoint } from './types';

const SIGHTLINE_ENDPOINT_RADIUS = 0.2 * SCALE;
const DEFAULT_SIGHT_POINT_STYLE: CSSProperties = {
  fill: '#67e8f9',
  fillOpacity: 0.95,
  stroke: '#082f49',
  strokeOpacity: 0.95,
  strokeWidth: 1,
  vectorEffect: 'non-scaling-stroke',
};

export interface SightPointProps {
  point: GridPoint;
  className?: string;
  style?: CSSProperties;
}

export const SightPoint = memo(function SightPoint({ point, className, style }: SightPointProps) {
  const [cx, cy] = gridPointToSvgPoint(point);

  return (
    <circle
      cx={cx}
      cy={cy}
      r={SIGHTLINE_ENDPOINT_RADIUS}
      className={className}
      pointerEvents='none'
      style={{ ...DEFAULT_SIGHT_POINT_STYLE, ...style }}
    />
  );
});
