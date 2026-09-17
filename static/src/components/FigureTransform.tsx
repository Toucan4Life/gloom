import type { ReactNode } from 'react';

export interface FigureTransformProps {
  rotate?: boolean;
  x: number;
  y: number;
  children: ReactNode;
}

export default function FigureTransform({ rotate = false, x, y, children }: FigureTransformProps) {
  return <g transform={rotate ? `rotate(-90 ${x} ${y})` : undefined}>{children}</g>;
}
