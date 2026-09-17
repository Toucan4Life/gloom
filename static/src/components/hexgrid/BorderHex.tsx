import { memo, type CSSProperties } from 'react';
import { getGridHexPoints } from './hexUtils';

const BORDER_HEX_STYLE: CSSProperties = {
  fill: '#0f172a',
  fillOpacity: 0.92,
  stroke: '#1e293b',
  strokeOpacity: 0.7,
  strokeWidth: 1,
  vectorEffect: 'non-scaling-stroke',
};

export interface BorderHexProps {
  row: number;
  column: number;
  className?: string;
  style?: CSSProperties;
}

export const BorderHex = memo(function BorderHex({
  row,
  column,
  className,
  style,
}: BorderHexProps) {
  return (
    <polygon
      className={className}
      points={getGridHexPoints(column, row)}
      pointerEvents='none'
      style={{ ...BORDER_HEX_STYLE, ...style }}
    />
  );
});
