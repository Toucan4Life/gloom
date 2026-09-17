import { memo, type CSSProperties, type ReactNode } from 'react';
import { GRID_HEIGHT, GRID_WIDTH, SCALE } from '../../lib/constants';
import { getGridHexCenter } from './hexUtils';

const FONT_SIZE = 0.5 * SCALE;
const LABEL_OFFSET = 0.6 * SCALE;

const DEFAULT_LABEL_STYLE: CSSProperties = {
  fill: '#e2e8f0',
  fillOpacity: 0.9,
  fontSize: FONT_SIZE,
  fontWeight: 600,
  letterSpacing: '0.01em',
  textAnchor: 'middle',
  paintOrder: 'stroke',
  stroke: '#020617',
  strokeOpacity: 0.95,
  strokeWidth: 2.5,
  vectorEffect: 'non-scaling-stroke',
};

export interface HexLabelGridProps {
  show?: boolean;
  rotate?: boolean;
  renderLabel?: (index: number) => ReactNode;
  className?: string;
  style?: CSSProperties;
}

export const HexLabelGrid = memo(function HexLabelGrid({
  show = false,
  rotate = false,
  renderLabel,
  className,
  style,
}: HexLabelGridProps) {
  if (!show) {
    return null;
  }

  const labels = [];
  for (let column = 0, index = 0; column < GRID_WIDTH; column += 1) {
    for (let row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
      const [x, y] = getGridHexCenter(column, row);
      const labelY = y - LABEL_OFFSET;

      labels.push(
        <g key={index} transform={rotate ? `rotate(-90 ${x} ${labelY})` : undefined}>
          <text
            className={className}
            x={x}
            y={labelY + 4.5}
            pointerEvents='none'
            style={{ ...DEFAULT_LABEL_STYLE, ...style }}
          >
            {renderLabel ? renderLabel(index) : index}
          </text>
        </g>,
      );
    }
  }

  return <>{labels}</>;
});
