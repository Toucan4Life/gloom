function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

export interface ToggleSwitchProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  description?: string;
  disabled?: boolean;
  accent?: 'slate' | 'emerald' | 'rose' | 'cyan' | 'amber' | 'violet';
}

const ACCENT_TRACK: Record<NonNullable<ToggleSwitchProps['accent']>, string> = {
  slate: 'border-slate-400/60 bg-slate-400/70',
  emerald: 'border-emerald-400/60 bg-emerald-500/80',
  rose: 'border-rose-400/60 bg-rose-500/80',
  cyan: 'border-cyan-400/60 bg-cyan-500/80',
  amber: 'border-amber-400/60 bg-amber-500/80',
  violet: 'border-violet-400/60 bg-violet-500/80',
};

export default function ToggleSwitch({
  label,
  checked,
  onChange,
  description,
  disabled = false,
  accent = 'slate',
}: ToggleSwitchProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span
        title={description}
        className={cx('text-xs font-semibold tracking-wide text-slate-100', disabled && 'text-slate-500')}
      >
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        title={description}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cx(
          'relative h-6 w-11 shrink-0 rounded-full border transition',
          'focus:outline-none focus:ring-2 focus:ring-cyan-400/70 focus:ring-offset-2 focus:ring-offset-slate-950',
          disabled
            ? 'cursor-not-allowed border-slate-900 bg-slate-950/70'
            : checked
              ? ACCENT_TRACK[accent]
              : 'border-slate-700 bg-slate-800',
        )}
      >
        <span
          className={cx(
            'absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
            checked && 'translate-x-5',
          )}
        />
      </button>
    </div>
  );
}
