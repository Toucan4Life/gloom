import { memo, type CSSProperties, type MouseEvent } from 'react';
import { EMPTY } from '../../lib/brushes';
import type { TerrainBrush } from '../../lib/scenarioState';
import { getGridHexCenter, getGridHexPoints } from './hexUtils';
import { TerrainGlyph } from './TerrainGlyph';
import { TERRAIN_HEX_STYLES } from './terrainPalette';
import type {
  HexInteractionHandler,
  HexMouseDownHandler,
  HexMouseUpHandler,
} from './types';

export interface HexProps {
  row: number;
  column: number;
  content: TerrainBrush;
  index: number;
  active?: boolean;
  onClick?: HexInteractionHandler;
  onMouseDown?: HexMouseDownHandler;
  onMouseUp?: HexMouseUpHandler;
  className?: string;
  style?: CSSProperties;
}

export const Hex = memo(function Hex({
  row,
  column,
  content,
  index,
  active = true,
  onClick,
  onMouseDown,
  onMouseUp,
  className,
  style,
}: HexProps) {
  const handleClick = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(true, index);
    event.preventDefault();
  };

  const handleContextMenu = (event: MouseEvent<SVGPolygonElement>) => {
    onClick?.(false, index);
    event.preventDefault();
  };

  const handleMouseDown = (event: MouseEvent<SVGPolygonElement>) => {
    onMouseDown?.(event.pageX, event.pageY, index, column, row);
  };

  const handleMouseUp = (event: MouseEvent<SVGPolygonElement>) => {
    onMouseUp?.(index);
    event.stopPropagation();
  };

  const [centerX, centerY] = getGridHexCenter(column, row);

  return (
    <>
      <polygon
        className={['transition-colors duration-150', className].filter(Boolean).join(' ')}
        points={getGridHexPoints(column, row)}
        pointerEvents={active ? 'all' : 'none'}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        style={{ vectorEffect: 'non-scaling-stroke', ...TERRAIN_HEX_STYLES[content] ?? TERRAIN_HEX_STYLES[0], ...style }}
      />
      {content === EMPTY ? null : <TerrainGlyph content={content} x={centerX} y={centerY} />}
    </>
  );
});
