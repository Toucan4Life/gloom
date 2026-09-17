import {
  memo,
  useId,
  type CSSProperties,
  type MouseEventHandler,
  type ReactNode,
} from 'react';
import {
  GRID_DELTA,
  GRID_EXTENT,
  GRID_MARGIN,
  GRID_SCALED_HEIGHT,
  GRID_SCALED_WIDTH,
  GRID_TRANSFORM,
} from '../../lib/constants';
import type { TerrainBrush } from '../../lib/scenarioState';
import { BorderGrid } from './BorderGrid';
import { DebugLines } from './DebugLines';
import { HexGrid } from './HexGrid';
import { HexLabelGrid } from './HexLabelGrid';
import { OverlayHexGrid } from './OverlayHexGrid';
import { SightLines } from './SightLines';
import { SightPoints } from './SightPoints';
import { WallGrid } from './WallGrid';
import type {
  DebugGeometry,
  GridLine,
  GridPoint,
  HexInteractionHandler,
  HexMouseDownHandler,
  HexMouseUpHandler,
  OverlayHexKind,
} from './types';

const VIEW_BOX_STANDARD = `${-(GRID_MARGIN + GRID_DELTA)} ${-GRID_MARGIN} ${GRID_EXTENT} ${GRID_EXTENT}`;
const VIEW_BOX_ROTATED = `${-GRID_MARGIN} ${-(GRID_MARGIN + GRID_DELTA)} ${GRID_EXTENT} ${GRID_EXTENT}`;

interface GridDefsProps {
  edgeFadeId: string;
}

const GridDefs = memo(function GridDefs({ edgeFadeId }: GridDefsProps) {
  const xFadeMargin = GRID_MARGIN + GRID_DELTA;
  const yFadeMargin = GRID_MARGIN;

  return (
    <defs>
      <linearGradient id={`${edgeFadeId}-top`} y2='1' x2='0'>
        <stop offset='0' stopColor='black' />
        <stop offset='1' stopColor='white' />
      </linearGradient>
      <linearGradient id={`${edgeFadeId}-bottom`} y2='1' x2='0'>
        <stop offset='0' stopColor='white' />
        <stop offset='1' stopColor='black' />
      </linearGradient>
      <linearGradient id={`${edgeFadeId}-left`} y2='0' x2='1'>
        <stop offset='0' stopColor='black' />
        <stop offset='1' stopColor='white' />
      </linearGradient>
      <linearGradient id={`${edgeFadeId}-right`} y2='0' x2='1'>
        <stop offset='0' stopColor='white' />
        <stop offset='1' stopColor='black' />
      </linearGradient>
      <mask id={edgeFadeId} maskContentUnits='userSpaceOnUse'>
        <rect
          x={-xFadeMargin}
          y={-yFadeMargin}
          width={xFadeMargin}
          height={GRID_SCALED_HEIGHT + 2 * yFadeMargin}
          fill={`url(#${edgeFadeId}-left)`}
        />
        <rect
          x={GRID_SCALED_WIDTH}
          y={-yFadeMargin}
          width={xFadeMargin}
          height={GRID_SCALED_HEIGHT + 2 * yFadeMargin}
          fill={`url(#${edgeFadeId}-right)`}
        />
        <rect
          x={0}
          y={-yFadeMargin}
          width={GRID_SCALED_WIDTH}
          height={yFadeMargin}
          fill={`url(#${edgeFadeId}-top)`}
        />
        <rect
          x={0}
          y={GRID_SCALED_HEIGHT}
          width={GRID_SCALED_WIDTH}
          height={yFadeMargin}
          fill={`url(#${edgeFadeId}-bottom)`}
        />
        <rect x={0} y={0} width={GRID_SCALED_WIDTH} height={GRID_SCALED_HEIGHT} fill='white' />
      </mask>
    </defs>
  );
});

export interface GridOverlayLayer {
  grid?: ReadonlyArray<boolean | number> | null;
  content: OverlayHexKind;
  show?: boolean;
}

export interface GridProps {
  grid: ReadonlyArray<TerrainBrush>;
  walls: ReadonlyArray<boolean>;
  activeHexes?: boolean;
  activeWalls?: boolean;
  rotate?: boolean;
  rotateGrid?: boolean;
  overlayLayers?: ReadonlyArray<GridOverlayLayer>;
  showHexLabels?: boolean;
  sightLines?: ReadonlyArray<GridLine> | null;
  sightPoints?: ReadonlyArray<GridPoint> | null;
  debugLines?: ReadonlyArray<DebugGeometry> | null;
  onGridMouseUp?: MouseEventHandler<SVGSVGElement>;
  onGridMouseLeave?: MouseEventHandler<SVGSVGElement>;
  onHexClick?: HexInteractionHandler;
  onHexMouseDown?: HexMouseDownHandler;
  onHexMouseUp?: HexMouseUpHandler;
  onWallClick?: HexInteractionHandler;
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export const Grid = memo(function Grid({
  grid,
  walls,
  activeHexes = true,
  activeWalls = !activeHexes,
  rotate = false,
  rotateGrid = false,
  overlayLayers = [],
  showHexLabels = false,
  sightLines,
  sightPoints,
  debugLines,
  onGridMouseUp,
  onGridMouseLeave,
  onHexClick,
  onHexMouseDown,
  onHexMouseUp,
  onWallClick,
  children,
  className,
  style,
}: GridProps) {
  const edgeFadeId = `edge-fade-${useId().replaceAll(':', '-')}`;

  return (
    <svg
      width={GRID_EXTENT}
      height={GRID_EXTENT}
      viewBox={rotateGrid ? VIEW_BOX_ROTATED : VIEW_BOX_STANDARD}
      onMouseUp={onGridMouseUp}
      onMouseLeave={onGridMouseLeave}
      className={[
        'block h-auto max-w-full overflow-visible rounded-2xl bg-slate-950/70 shadow-2xl ring-1 ring-slate-800/80',
        className,
      ].filter(Boolean).join(' ')}
      style={style}
    >
      <GridDefs edgeFadeId={edgeFadeId} />
      <g transform={rotateGrid ? GRID_TRANSFORM : undefined}>
        <HexGrid
          grid={grid}
          activeHexes={activeHexes}
          onHexClick={onHexClick}
          onHexMouseDown={onHexMouseDown}
          onHexMouseUp={onHexMouseUp}
        />
        <BorderGrid maskId={edgeFadeId} />
        <WallGrid
          walls={walls}
          activeWalls={activeWalls}
          onWallClick={onWallClick}
        />
        {overlayLayers.map((layer, index) => (
          <OverlayHexGrid
            key={index}
            show={layer.show}
            grid={layer.grid}
            content={layer.content}
          />
        ))}
        <HexLabelGrid show={showHexLabels} rotate={rotate} />
        {children}
        <SightLines lines={sightLines} />
        <SightPoints points={sightPoints} />
        <DebugLines lines={debugLines} />
      </g>
    </svg>
  );
});
