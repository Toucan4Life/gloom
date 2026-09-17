import { memo, type CSSProperties } from 'react';
import { SCALE } from '../../lib/constants';
import { gridLineToSvgLine, gridPointToSvgPoint } from './hexUtils';
import type { DebugGeometry, GridLine, GridPoint } from './types';

const DEBUG_POINT_RADIUS = 0.2 * SCALE;
const DEBUG_STYLES: ReadonlyArray<CSSProperties> = [
  { fill: '#f8fafc', stroke: '#f8fafc', strokeOpacity: 0.95, fillOpacity: 0.95, strokeWidth: 1.4 },
  { fill: '#f87171', stroke: '#f87171', strokeOpacity: 0.95, fillOpacity: 0.95, strokeWidth: 1.4 },
  { fill: '#4ade80', stroke: '#4ade80', strokeOpacity: 0.95, fillOpacity: 0.95, strokeWidth: 1.4 },
  { fill: '#60a5fa', stroke: '#60a5fa', strokeOpacity: 0.95, fillOpacity: 0.95, strokeWidth: 1.4 },
  { fill: '#fb923c', stroke: '#fb923c', strokeOpacity: 0.95, fillOpacity: 0.95, strokeWidth: 1.4 },
];

function isLineGeometry(points: readonly [GridPoint] | GridLine): points is GridLine {
  return points.length === 2;
}

export interface DebugLinesProps {
  lines?: ReadonlyArray<DebugGeometry> | null;
  className?: string;
  style?: CSSProperties;
}

export const DebugLines = memo(function DebugLines({ lines, className, style }: DebugLinesProps) {
  if (!lines) {
    return null;
  }

  return (
    <>
      {lines.map(([classIndexValue, points], index) => {
        let classIndex = classIndexValue;
        let radius = DEBUG_POINT_RADIUS;

        if (isLineGeometry(points)) {
          const [[x1, y1], [x2, y2]] = gridLineToSvgLine(points);
          return (
            <line
              key={index}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              className={className}
              pointerEvents='none'
              style={{ vectorEffect: 'non-scaling-stroke', ...DEBUG_STYLES[classIndex] ?? DEBUG_STYLES[0], ...style }}
            />
          );
        }

        if (classIndex > DEBUG_STYLES.length) {
          classIndex -= DEBUG_STYLES.length;
          radius /= 4;
        }

        const [cx, cy] = gridPointToSvgPoint(points[0]);
        return (
          <circle
            key={index}
            cx={cx}
            cy={cy}
            r={radius}
            className={className}
            pointerEvents='none'
            style={{ vectorEffect: 'non-scaling-stroke', ...DEBUG_STYLES[classIndex] ?? DEBUG_STYLES[0], ...style }}
          />
        );
      })}
    </>
  );
});
