import { memo } from 'react';
import { GRID_HEIGHT, GRID_WIDTH } from '../../lib/constants';
import { BorderHex } from './BorderHex';

export interface BorderGridProps {
  maskId?: string;
}

export const BorderGrid = memo(function BorderGrid({ maskId }: BorderGridProps) {
  const hexes = [];
  let index = 0;

  for (let column = -1, row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
    hexes.push(<BorderHex key={index} row={row} column={column} />);
  }
  for (let column = GRID_WIDTH, row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
    hexes.push(<BorderHex key={index} row={row} column={column} />);
  }
  for (let column = 0, row = -1; column < GRID_WIDTH; column += 1, index += 1) {
    hexes.push(<BorderHex key={index} row={row} column={column} />);
  }
  for (let column = -1, row = GRID_HEIGHT; column < GRID_WIDTH; column += 1, index += 1) {
    hexes.push(<BorderHex key={index} row={row} column={column} />);
  }

  return <g mask={maskId ? `url(#${maskId})` : undefined}>{hexes}</g>;
});
