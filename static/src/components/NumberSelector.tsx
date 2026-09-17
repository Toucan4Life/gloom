function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

export interface NumberSelectorOption<T extends number = number> {
  value: T;
  label: string;
}

export interface NumberSelectorProps<T extends number = number> {
  label: string;
  options: readonly NumberSelectorOption<T>[];
  value: T;
  onChange: (value: T) => void;
  description?: string;
  disabled?: boolean;
  accent?: 'slate' | 'emerald' | 'rose' | 'cyan' | 'amber' | 'violet';
}

const ACCENT_CLASSES: Record<NonNullable<NumberSelectorProps['accent']>, string> = {
  slate: 'border-slate-400/50 bg-slate-200/10 text-slate-100',
  emerald: 'border-emerald-400/60 bg-emerald-400/15 text-emerald-100',
  rose: 'border-rose-400/60 bg-rose-400/15 text-rose-100',
  cyan: 'border-cyan-400/60 bg-cyan-400/15 text-cyan-100',
  amber: 'border-amber-400/60 bg-amber-400/15 text-amber-100',
  violet: 'border-violet-400/60 bg-violet-400/15 text-violet-100',
};

function columnsForOptions(count: number, maxLabelLength: number): number {
  if (count <= 2) return 2;
  if (count === 3) return 3;
  if (maxLabelLength <= 5) return 5;
  return 3;
}

export default function NumberSelector<T extends number>({
  label,
  options,
  value,
  onChange,
  description,
  disabled = false,
  accent = 'slate',
}: NumberSelectorProps<T>) {
  const columns = columnsForOptions(
    options.length,
    options.reduce((max, option) => Math.max(max, option.label.length), 0),
  );

  return (
    <section className="space-y-1.5">
      <div className="flex items-center justify-between gap-3">
        <h3
          title={description}
          className={cx('text-xs font-semibold tracking-wide text-slate-100', disabled && 'text-slate-500')}
        >
          {label}
        </h3>
        <span
          className={cx(
            'rounded-full border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.18em]',
            disabled ? 'border-slate-800 text-slate-600' : 'border-slate-700 text-slate-500',
          )}
        >
          {disabled ? 'N/A' : 'Select'}
        </span>
      </div>
      <div
        className={cx(
          'grid gap-1',
          columns === 2 && 'grid-cols-2',
          columns === 3 && 'grid-cols-3',
          columns === 4 && 'grid-cols-4',
          columns === 5 && 'grid-cols-5',
        )}
      >
        {options.map((option) => {
          const active = option.value === value && !disabled;

          return (
            <button
              key={option.value}
              type="button"
              title={description}
              aria-pressed={active}
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={cx(
                'rounded-lg border px-1.5 py-1.5 text-xs font-medium transition',
                'focus:outline-none focus:ring-2 focus:ring-cyan-400/70 focus:ring-offset-2 focus:ring-offset-slate-950',
                disabled
                  ? 'cursor-not-allowed border-slate-900 bg-slate-950/70 text-slate-600'
                  : 'border-slate-800 bg-slate-900/80 text-slate-300 hover:border-slate-600 hover:bg-slate-800',
                active && ACCENT_CLASSES[accent],
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}
