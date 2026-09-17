import { memo, type CSSProperties, type MouseEvent } from 'react';
import { getAOEHexPoints } from './hexUtils';
import type { AOEHexState, HexInteractionHandler } from './types';

const AOE_STYLES: ReadonlyArray<CSSProperties> = [
  {
    fill: '#0f172a',
    fillOpacity: 0.92,
    stroke: '#334155',
    strokeOpacity: 0.85,
    strokeWidth: 1,
  },
  {
    fill: '#f59e0b',
    fillOpacity: 0.45,
    stroke: '#fef3c7',
    strokeOpacity: 0.42,
    strokeWidth: 1.2,
  },
  {
    fill: '#ef4444',
    fillOpacity: 0.65,
    stroke: '#fee2e2',
    strokeOpacity: 0.5,
    strokeWidth: 1.2,
  },
];

export interface AOEHexProps {
  row: number;
  column: number;
  content: AOEHexState;
  index: number;
  onClick?: HexInteractionHandler | null;
  className?: string;
  style?: CSSProperties;
}

export const AOEHex = memo(function AOEHex({
  row,
  column,
  content,
  index,
  onClick,
  className,
  style,
}: AOEHexProps) {
  const handleClick = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(true, index);
    event.preventDefault();
  };

  const handleContextMenu = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(false, index);
    event.preventDefault();
  };

  return (
    <polygon
      className={className}
      points={getAOEHexPoints(column, row)}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      style={{ vectorEffect: 'non-scaling-stroke', ...AOE_STYLES[content] ?? AOE_STYLES[0], ...style }}
    />
  );
});
