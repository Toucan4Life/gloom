import type { ReactNode } from 'react';

import type { SelectableBrush } from '../lib/brushes';

type Accent = 'emerald' | 'violet' | 'amber' | 'rose' | 'cyan' | 'slate';

const ACCENT_STYLES: Record<Accent, string> = {
  emerald: 'border-emerald-400/70 bg-emerald-500/15 text-emerald-100 shadow-emerald-950/30',
  violet: 'border-violet-400/70 bg-violet-500/15 text-violet-100 shadow-violet-950/30',
  amber: 'border-amber-400/70 bg-amber-500/15 text-amber-100 shadow-amber-950/30',
  rose: 'border-rose-400/70 bg-rose-500/15 text-rose-100 shadow-rose-950/30',
  cyan: 'border-cyan-400/70 bg-cyan-500/15 text-cyan-100 shadow-cyan-950/30',
  slate: 'border-slate-400/60 bg-slate-400/10 text-slate-100 shadow-slate-950/20',
};

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

export interface BrushButtonProps {
  brush: SelectableBrush;
  label: string;
  description: string;
  icon: ReactNode;
  isSelected: boolean;
  onClick: (brush: SelectableBrush) => void;
  accent?: Accent;
  className?: string;
}

export default function BrushButton({
  brush,
  label,
  description,
  icon,
  isSelected,
  onClick,
  accent = 'slate',
  className,
}: BrushButtonProps) {
  return (
    <button
      type="button"
      title={description}
      aria-label={`${label}: ${description}`}
      aria-pressed={isSelected}
      onClick={() => onClick(brush)}
      className={cx(
        'group flex flex-col items-center gap-1.5 rounded-xl border px-2 py-2 text-center transition duration-150',
        'backdrop-blur-sm hover:-translate-y-0.5 hover:border-slate-400/70 hover:bg-slate-800/90',
        'focus:outline-none focus:ring-2 focus:ring-cyan-400/70 focus:ring-offset-2 focus:ring-offset-slate-950',
        isSelected
          ? cx('shadow-lg', ACCENT_STYLES[accent])
          : 'border-slate-800 bg-slate-900/80 text-slate-200 shadow-lg shadow-slate-950/15',
        className,
      )}
    >
      <span
        className={cx(
          'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-slate-950/70',
          isSelected ? 'border-current/40' : 'border-slate-800 text-slate-200',
        )}
      >
        {icon}
      </span>
      <span className="line-clamp-2 text-[11px] font-semibold leading-tight tracking-wide">{label}</span>
    </button>
  );
}
