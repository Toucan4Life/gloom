import { memo, type CSSProperties } from 'react';
import { gridLineToSvgLine } from './hexUtils';
import type { GridLine } from './types';

const DEFAULT_SIGHT_LINE_STYLE: CSSProperties = {
  fill: 'none',
  stroke: '#67e8f9',
  strokeOpacity: 0.88,
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  vectorEffect: 'non-scaling-stroke',
};

export interface SightLineProps {
  line: GridLine;
  className?: string;
  style?: CSSProperties;
}

export const SightLine = memo(function SightLine({ line, className, style }: SightLineProps) {
  const [[x1, y1], [x2, y2]] = gridLineToSvgLine(line);

  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      className={className}
      pointerEvents='none'
      style={{ ...DEFAULT_SIGHT_LINE_STYLE, ...style }}
    />
  );
});
