import { memo } from 'react';
import { GRID_HEIGHT, GRID_WIDTH } from '../../lib/constants';
import { OverlayHex } from './OverlayHex';
import type { OverlayHexKind } from './types';

export interface OverlayHexGridProps {
  show?: boolean;
  grid?: ReadonlyArray<boolean | number> | null;
  content: OverlayHexKind;
}

export const OverlayHexGrid = memo(function OverlayHexGrid({
  show = true,
  grid,
  content,
}: OverlayHexGridProps) {
  if (!show || !grid) {
    return null;
  }

  const hexes = [];
  for (let column = 0, index = 0; column < GRID_WIDTH; column += 1) {
    for (let row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
      if (grid[index]) {
        hexes.push(
          <OverlayHex
            key={index}
            row={row}
            column={column}
            content={content}
          />,
        );
      }
    }
  }

  return <>{hexes}</>;
});
