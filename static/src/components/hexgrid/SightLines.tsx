import { memo, type CSSProperties } from 'react';
import { SightLine } from './SightLine';
import type { GridLine } from './types';

export interface SightLinesProps {
  lines?: ReadonlyArray<GridLine> | null;
  className?: string;
  style?: CSSProperties;
}

export const SightLines = memo(function SightLines({ lines, className, style }: SightLinesProps) {
  if (!lines) {
    return null;
  }

  return (
    <>
      {lines.map((line, index) => (
        <SightLine
          key={index}
          className={className}
          line={line}
          style={style}
        />
      ))}
    </>
  );
});
