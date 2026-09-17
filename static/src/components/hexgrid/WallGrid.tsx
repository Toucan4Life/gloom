import { memo } from 'react';
import { GRID_HEIGHT, GRID_WIDTH } from '../../lib/constants';
import { Wall } from './Wall';
import type { HexInteractionHandler, WallSide } from './types';

export interface WallGridProps {
  walls: ReadonlyArray<boolean>;
  activeWalls?: boolean;
  onWallClick?: HexInteractionHandler;
}

export const WallGrid = memo(function WallGrid({
  walls,
  activeWalls = true,
  onWallClick,
}: WallGridProps) {
  const wallElements = [];
  let index = 0;

  for (let column = 0; column < GRID_WIDTH; column += 1) {
    for (let row = 0; row < GRID_HEIGHT; row += 1) {
      for (let side = 0; side < 3; side += 1, index += 1) {
        wallElements.push(
          <Wall
            key={index}
            row={row}
            column={column}
            side={side as WallSide}
            wall={Boolean(walls[index])}
            index={index}
            active={activeWalls}
            onClick={onWallClick}
          />,
        );
      }
    }
  }

  return <>{wallElements}</>;
});
