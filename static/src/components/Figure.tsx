import {
  EMPTY,
  getActiveFigureBrush,
  getDestinationBrush,
  type FigureBrushValue,
  type FigureDisplayBrush,
  type InitiativeValue,
  type TraitValue,
} from '../lib/brushes';

import FigureIcon from './FigureIcon';
import FigureSelectionHighlight from './FigureSelectionHighlight';
import { FigureTargetHighlight } from './hexgrid/FigureTargetHighlight';
import FigureTransform from './FigureTransform';
import {
  ATTACKED,
  ATTACKED_CHARACTER_FOCUS,
  ATTACKED_MONSTER_FOCUS,
  CHARACTER_FOCUS,
  MONSTER_FOCUS,
  type FigureHighlightType,
} from './figure_highlights';

function getHighlightType(
  activeFaction: boolean,
  attack: boolean,
  focus: boolean,
): FigureHighlightType | null {
  if (focus) {
    if (attack) {
      return activeFaction ? ATTACKED_CHARACTER_FOCUS : ATTACKED_MONSTER_FOCUS;
    }

    return activeFaction ? CHARACTER_FOCUS : MONSTER_FOCUS;
  }

  if (attack) {
    return ATTACKED;
  }

  return null;
}

export interface FigureProps {
  x: number;
  y: number;
  figure: FigureBrushValue | typeof EMPTY;
  initiative?: InitiativeValue;
  flying?: TraitValue;
  teleport?: boolean | 0 | 1;
  selected?: boolean;
  rotate?: boolean;
  displaySolution?: boolean;
  move?: boolean;
  destination?: boolean;
  attack?: boolean;
  focus?: boolean;
  dragSource?: boolean;
  activeFaction?: boolean;
  activeFigure?: boolean;
}

export default function Figure({
  x,
  y,
  figure,
  initiative = 1,
  flying = 0,
  teleport = false,
  selected = false,
  rotate = false,
  displaySolution = false,
  move = false,
  destination = false,
  attack = false,
  focus = false,
  dragSource = false,
  activeFaction = false,
  activeFigure = false,
}: FigureProps) {
  if (dragSource) {
    return null;
  }

  if (figure === EMPTY && (!displaySolution || (!move && !destination))) {
    return null;
  }

  let renderedFigure: FigureDisplayBrush = figure === EMPTY ? getDestinationBrush(activeFaction) : figure;
  let ghost = false;

  if (figure === EMPTY) {
    if (move) {
      renderedFigure = getActiveFigureBrush(activeFaction);
    } else {
      renderedFigure = getDestinationBrush(activeFaction);
      ghost = true;
    }
  } else if (activeFigure) {
    renderedFigure = getActiveFigureBrush(activeFaction);
    ghost = displaySolution && !move;
  }

  const highlightType = displaySolution ? getHighlightType(activeFaction, attack, focus) : null;

  return (
    <>
      <FigureTransform rotate={rotate} x={x} y={y}>
        <FigureIcon
          x={x}
          y={y}
          figure={renderedFigure}
          flying={flying}
          teleport={teleport}
          initiative={initiative}
          activeFaction={activeFaction}
          opacity={ghost ? 0.4 : 1}
        />
      </FigureTransform>
      {highlightType === null ? null : <FigureTargetHighlight x={x} y={y} type={highlightType} />}
      {selected ? <FigureSelectionHighlight x={x} y={y} /> : null}
    </>
  );
}
