import { memo, useId } from 'react';
import { FigureTargetHighlightBurst } from './FigureTargetHighlightBurst';
import { FigureTargetHighlightClip } from './FigureTargetHighlightClip';
import { FIGURE_TARGET_HIGHLIGHT } from './types';
import type { FigureTargetHighlightType } from './types';

export interface FigureTargetHighlightProps {
  id?: string | number;
  x: number;
  y: number;
  type: FigureTargetHighlightType;
}

export const FigureTargetHighlight = memo(function FigureTargetHighlight({
  id,
  x,
  y,
  type,
}: FigureTargetHighlightProps) {
  const generatedId = useId().replaceAll(':', '-');
  const baseId = id === undefined ? generatedId : String(id);

  if (type < FIGURE_TARGET_HIGHLIGHT.ATTACKED_MONSTER_FOCUS) {
    return (
      <FigureTargetHighlightBurst
        x={x}
        y={y}
        type={type}
        clipPath={null}
      />
    );
  }

  const focusClipId = `focus-clip-${baseId}`;
  const attackedClipId = `attacked-clip-${baseId}`;

  return (
    <>
      <FigureTargetHighlightClip id={focusClipId} x={x} y={y} side />
      <FigureTargetHighlightBurst
        x={x}
        y={y}
        type={type}
        clipPath={`url(#${focusClipId})`}
      />
      <FigureTargetHighlightClip id={attackedClipId} x={x} y={y} side={false} />
      <FigureTargetHighlightBurst
        x={x}
        y={y}
        type={FIGURE_TARGET_HIGHLIGHT.ATTACKED}
        clipPath={`url(#${attackedClipId})`}
      />
    </>
  );
});
