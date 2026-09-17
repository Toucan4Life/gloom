import { memo } from 'react';
import { FIGURE_RADIUS } from '../../lib/constants';

export interface FigureTargetHighlightClipProps {
  id: string;
  x: number;
  y: number;
  side: boolean;
}

export const FigureTargetHighlightClip = memo(function FigureTargetHighlightClip({
  id,
  x,
  y,
  side,
}: FigureTargetHighlightClipProps) {
  const clipPoints = [
    x, y + 2 * FIGURE_RADIUS,
    x, y - 2 * FIGURE_RADIUS,
    x - 2 * FIGURE_RADIUS, y - 2 * FIGURE_RADIUS,
    x - 2 * FIGURE_RADIUS, y + 2 * FIGURE_RADIUS,
  ].join(',');
  const angle = side ? 'rotate(60 ' : 'rotate(240 ';

  return (
    <clipPath id={id}>
      <polygon points={clipPoints} transform={`${angle}${x} ${y})`} />
    </clipPath>
  );
});
