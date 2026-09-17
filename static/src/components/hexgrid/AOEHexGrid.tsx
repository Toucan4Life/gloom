import { memo } from 'react';
import {
  AOE_GRID_SKIP_LIST,
  AOE_HEIGHT,
  AOE_SIZE,
  AOE_WIDTH,
} from '../../lib/constants';
import { AOEHex } from './AOEHex';
import { AOE_HEX_STATE } from './types';
import type { HexInteractionHandler } from './types';

export const AOE_CENTER_INDEX = (AOE_SIZE - 1) / 2;
export const AOE_CENTER_ROW = (AOE_HEIGHT - 1) / 2;
export const AOE_CENTER_COLUMN = (AOE_WIDTH - 1) / 2;

const AOE_GRID_SKIP_SET = new Set<number>(AOE_GRID_SKIP_LIST);

export interface AOEHexGridProps {
  grid: ReadonlyArray<boolean | number>;
  melee?: boolean;
  onHexClick?: HexInteractionHandler;
}

export const AOEHexGrid = memo(function AOEHexGrid({
  grid,
  melee = false,
  onHexClick,
}: AOEHexGridProps) {
  const hexes = [];

  if (melee) {
    hexes.push(
      <AOEHex
        key={AOE_CENTER_INDEX}
        row={AOE_CENTER_ROW}
        column={AOE_CENTER_COLUMN}
        content={AOE_HEX_STATE.CENTER}
        index={AOE_CENTER_INDEX}
        onClick={null}
      />,
    );
  }

  for (let column = 0, index = 0; column < AOE_WIDTH; column += 1) {
    for (let row = 0; row < AOE_HEIGHT; row += 1, index += 1) {
      if ((index !== AOE_CENTER_INDEX || !melee) && !AOE_GRID_SKIP_SET.has(index) && !grid[index]) {
        hexes.push(
          <AOEHex
            key={index}
            row={row}
            column={column}
            content={AOE_HEX_STATE.EMPTY}
            index={index}
            onClick={onHexClick}
          />,
        );
      }
    }
  }

  for (let column = 0, index = 0; column < AOE_WIDTH; column += 1) {
    for (let row = 0; row < AOE_HEIGHT; row += 1, index += 1) {
      if ((index !== AOE_CENTER_INDEX || !melee) && !AOE_GRID_SKIP_SET.has(index) && grid[index]) {
        hexes.push(
          <AOEHex
            key={index}
            row={row}
            column={column}
            content={AOE_HEX_STATE.SET}
            index={index}
            onClick={onHexClick}
          />,
        );
      }
    }
  }

  return <>{hexes}</>;
});
