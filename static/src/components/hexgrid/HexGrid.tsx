import { memo } from 'react';
import { GRID_HEIGHT, GRID_WIDTH } from '../../lib/constants';
import type { TerrainBrush } from '../../lib/scenarioState';
import { Hex } from './Hex';
import type {
  HexInteractionHandler,
  HexMouseDownHandler,
  HexMouseUpHandler,
} from './types';

export interface HexGridProps {
  grid: ReadonlyArray<TerrainBrush>;
  activeHexes?: boolean;
  onHexClick?: HexInteractionHandler;
  onHexMouseDown?: HexMouseDownHandler;
  onHexMouseUp?: HexMouseUpHandler;
}

export const HexGrid = memo(function HexGrid({
  grid,
  activeHexes = true,
  onHexClick,
  onHexMouseDown,
  onHexMouseUp,
}: HexGridProps) {
  const hexes = [];

  for (let column = 0, index = 0; column < GRID_WIDTH; column += 1) {
    for (let row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
      hexes.push(
        <Hex
          key={index}
          row={row}
          column={column}
          content={grid[index]}
          index={index}
          active={activeHexes}
          onClick={onHexClick}
          onMouseDown={onHexMouseDown}
          onMouseUp={onHexMouseUp}
        />,
      );
    }
  }

  return <>{hexes}</>;
});
