import { memo, type CSSProperties } from 'react';
import { SightPoint } from './SightPoint';
import type { GridPoint } from './types';

export interface SightPointsProps {
  points?: ReadonlyArray<GridPoint> | null;
  className?: string;
  style?: CSSProperties;
}

export const SightPoints = memo(function SightPoints({ points, className, style }: SightPointsProps) {
  if (!points) {
    return null;
  }

  return (
    <>
      {points.map((point, index) => (
        <SightPoint
          key={index}
          className={className}
          point={point}
          style={style}
        />
      ))}
    </>
  );
});
