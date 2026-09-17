import { memo, type CSSProperties, type MouseEvent } from 'react';
import { getWallInteractivePoints, getWallPoints } from './hexUtils';
import type { HexInteractionHandler, WallSide } from './types';

const WALL_STYLE: CSSProperties = {
  fill: 'none',
  stroke: '#f8fafc',
  strokeOpacity: 0.92,
  strokeWidth: 2.4,
  strokeLinecap: 'round',
  vectorEffect: 'non-scaling-stroke',
};

const NO_WALL_STYLE: CSSProperties = {
  fill: 'none',
  stroke: '#64748b',
  strokeOpacity: 0.24,
  strokeWidth: 1.4,
  strokeLinecap: 'round',
  strokeDasharray: '4 4',
  vectorEffect: 'non-scaling-stroke',
};

export interface WallProps {
  row: number;
  column: number;
  side: WallSide;
  wall: boolean;
  index: number;
  active?: boolean;
  onClick?: HexInteractionHandler;
  className?: string;
  style?: CSSProperties;
}

export const Wall = memo(function Wall({
  row,
  column,
  side,
  wall,
  index,
  active = true,
  onClick,
  className,
  style,
}: WallProps) {
  const handleClick = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(true, index);
    event.preventDefault();
  };

  const handleContextMenu = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(false, index);
    event.preventDefault();
  };

  return (
    <>
      <polyline
        className={className}
        points={getWallPoints(column, row, side)}
        pointerEvents='none'
        style={{ ...(wall ? WALL_STYLE : NO_WALL_STYLE), ...style }}
      />
      <polygon
        points={getWallInteractivePoints(column, row, side)}
        pointerEvents={active ? 'all' : 'none'}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        style={{ fill: 'transparent', opacity: 0 }}
      />
    </>
  );
});
