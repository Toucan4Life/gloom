import {
  GRID_SCALED_HEIGHT,
  GRID_HEIGHT,
  GRID_SIZE,
  SCALE,
  SQRT_3_OVER_2,
} from '../../lib/constants';
import type {
  GridLine,
  GridPoint,
  WallSide,
} from './types';

const NUM_GRID_POINTS = 6 * GRID_SIZE;

export function getHexPoints(x: number, y: number): string {
  return [
    SCALE * (x - 1.0), SCALE * y,
    SCALE * (x - 0.5), SCALE * (y - SQRT_3_OVER_2),
    SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2),
    SCALE * (x + 1.0), SCALE * y,
    SCALE * (x + 0.5), SCALE * (y + SQRT_3_OVER_2),
    SCALE * (x - 0.5), SCALE * (y + SQRT_3_OVER_2),
  ].join(',');
}

export function getGridHexCenter(column: number, row: number): GridPoint {
  const x = 1.0 + 1.5 * column;
  const y = GRID_SCALED_HEIGHT / SCALE - SQRT_3_OVER_2 * (2 * row + column % 2 + 1);
  return [SCALE * x, SCALE * y];
}

export function getGridHexPoints(column: number, row: number): string {
  const x = 1.0 + 1.5 * column;
  const y = GRID_SCALED_HEIGHT / SCALE - SQRT_3_OVER_2 * (2 * row + column % 2 + 1);
  return getHexPoints(x, y);
}

export function getAOEHexPoints(column: number, row: number): string {
  const x = 1.0 + 1.5 * column;
  const y = SQRT_3_OVER_2 * (2 * row + column % 2);
  return getHexPoints(x, y);
}

export function getGridHexPoint(point: number): GridPoint {
  const hex = Math.floor(point / 6);
  const vertex = point % 6;
  const row = hex % GRID_HEIGHT;
  const column = Math.floor(hex / GRID_HEIGHT);
  const x = 1.0 + 1.5 * column;
  const y = GRID_SCALED_HEIGHT / SCALE - SQRT_3_OVER_2 * (2 * row + column % 2 + 1);

  switch (vertex) {
    case 0:
      return [SCALE * (x + 1.0), SCALE * y];
    case 1:
      return [SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2)];
    case 2:
      return [SCALE * (x - 0.5), SCALE * (y - SQRT_3_OVER_2)];
    case 3:
      return [SCALE * (x - 1.0), SCALE * y];
    case 4:
      return [SCALE * (x - 0.5), SCALE * (y + SQRT_3_OVER_2)];
    default:
      return [SCALE * (x + 0.5), SCALE * (y + SQRT_3_OVER_2)];
  }
}

export function getLinePoints(line: number): readonly [number, number] {
  return [Math.floor(line / NUM_GRID_POINTS), line % NUM_GRID_POINTS];
}

function getWallBase(column: number, row: number): GridPoint {
  const x = 1.0 + 1.5 * column;
  let y = SQRT_3_OVER_2 + SQRT_3_OVER_2 * (2.0 * row + column % 2);
  y = GRID_SCALED_HEIGHT / SCALE - y;
  return [x, y];
}

export function getWallPoints(column: number, row: number, wall: WallSide): string {
  const [x, y] = getWallBase(column, row);
  const pointsList: string[] = [];

  if (wall === 0) {
    pointsList.push([SCALE * (x - 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
  } else if (wall === 1) {
    pointsList.push([SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * (x + 1.0), SCALE * y].join(','));
  } else {
    pointsList.push([SCALE * (x + 1.0), SCALE * y].join(','));
    pointsList.push([SCALE * (x + 0.5), SCALE * (y + SQRT_3_OVER_2)].join(','));
  }

  return pointsList.join(',');
}

export function getWallInteractivePoints(column: number, row: number, wall: WallSide): string {
  const [x, y] = getWallBase(column, row);
  const pointsList: string[] = [];

  if (wall === 0) {
    pointsList.push([SCALE * (x - 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * x, SCALE * y].join(','));
    pointsList.push([SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * x, SCALE * (y - 2 * SQRT_3_OVER_2)].join(','));
  } else if (wall === 1) {
    pointsList.push([SCALE * (x + 0.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * x, SCALE * y].join(','));
    pointsList.push([SCALE * (x + 1.0), SCALE * y].join(','));
    pointsList.push([SCALE * (x + 1.5), SCALE * (y - SQRT_3_OVER_2)].join(','));
  } else {
    pointsList.push([SCALE * (x + 1.0), SCALE * y].join(','));
    pointsList.push([SCALE * x, SCALE * y].join(','));
    pointsList.push([SCALE * (x + 0.5), SCALE * (y + SQRT_3_OVER_2)].join(','));
    pointsList.push([SCALE * (x + 1.5), SCALE * (y + SQRT_3_OVER_2)].join(','));
  }

  return pointsList.join(',');
}

export function gridPointToSvgPoint([x, y]: GridPoint): GridPoint {
  return [SCALE * x, GRID_SCALED_HEIGHT - SCALE * y];
}

export function gridLineToSvgLine([start, end]: GridLine): GridLine {
  return [gridPointToSvgPoint(start), gridPointToSvgPoint(end)];
}
