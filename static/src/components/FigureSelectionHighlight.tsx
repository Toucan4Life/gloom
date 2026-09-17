import { FIGURE_RADIUS } from '../lib/constants';

export interface FigureSelectionHighlightProps {
  x: number;
  y: number;
}

export default function FigureSelectionHighlight({
  x,
  y,
}: FigureSelectionHighlightProps) {
  return (
    <circle
      cx={x}
      cy={y}
      r={FIGURE_RADIUS + 4}
      fill="none"
      stroke="#f8fafc"
      strokeOpacity={0.9}
      strokeWidth={2.5}
      strokeDasharray="4 3"
      pointerEvents="none"
    />
  );
}
