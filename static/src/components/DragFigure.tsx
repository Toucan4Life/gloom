import { EMPTY, type FigureDisplayBrush, type InitiativeValue, type TraitValue } from '../lib/brushes';

import FigureIcon from './FigureIcon';
import FigureTransform from './FigureTransform';

export interface DragFigureProps {
  dragging: boolean;
  x: number;
  y: number;
  figure: FigureDisplayBrush | typeof EMPTY;
  initiative?: InitiativeValue;
  flying?: TraitValue;
  teleport?: boolean | 0 | 1;
  rotate?: boolean;
  activeFaction?: boolean;
}

export default function DragFigure({
  dragging,
  x,
  y,
  figure,
  initiative = 1,
  flying = 0,
  teleport = false,
  rotate = false,
  activeFaction = false,
}: DragFigureProps) {
  if (!dragging || figure === EMPTY) {
    return null;
  }

  return (
    <g className="pointer-events-none">
      <FigureTransform rotate={rotate} x={x} y={y}>
        <FigureIcon
          x={x}
          y={y}
          figure={figure}
          initiative={initiative}
          flying={flying}
          teleport={teleport}
          activeFaction={activeFaction}
          opacity={0.92}
        />
      </FigureTransform>
    </g>
  );
}
