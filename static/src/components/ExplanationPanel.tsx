import type { SolverExplanationStep } from '../lib/solverTypes';

const PHASE_LABELS: Record<string, string> = {
  focus: 'Find Focus',
  attack_location: 'Optimize Location to Attack Focus',
  group: 'Find Best Group',
  movement: 'Get Closer',
  result: 'Result',
};

export interface ExplanationStepGroup {
  phase: string;
  steps: SolverExplanationStep[];
}

export interface ExplanationPanelProps {
  steps?: SolverExplanationStep[] | null;
  className?: string;
}

export function groupStepsByPhase(steps: SolverExplanationStep[]): ExplanationStepGroup[] {
  return steps.reduce<ExplanationStepGroup[]>((groups, step) => {
    const lastGroup = groups.at(-1);
    if (lastGroup && lastGroup.phase === step.phase) {
      lastGroup.steps.push(step);
      return groups;
    }

    groups.push({
      phase: step.phase,
      steps: [step],
    });
    return groups;
  }, []);
}

export default function ExplanationPanel({ steps, className = '' }: ExplanationPanelProps) {
  if (!steps || steps.length === 0) {
    return null;
  }

  const groups = groupStepsByPhase(steps);

  return (
    <section
      className={[
        'rounded-xl border border-slate-200 bg-white/90 p-4 shadow-sm',
        'dark:border-slate-700 dark:bg-slate-900/80',
        className,
      ].filter(Boolean).join(' ')}
      aria-label='How the solver reached this solution'
    >
      <h2 className='mb-4 text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-200'>
        How the solver reached this solution
      </h2>
      <div className='max-h-[320px] space-y-4 overflow-y-auto pr-1'>
        {groups.map((group, groupIndex) => (
          <div key={`${group.phase}-${groupIndex}`} className='space-y-2'>
            <div className='text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400'>
              {groupIndex + 1}. {PHASE_LABELS[group.phase] || group.phase}
            </div>
            <ol className='space-y-2 pl-5 text-sm text-slate-700 marker:font-semibold dark:text-slate-200'>
              {group.steps.map((step, stepIndex) => (
                <li key={`${step.title}-${stepIndex}`} className='space-y-1'>
                  <div className='font-medium text-slate-900 dark:text-white'>{step.title}</div>
                  <div className='text-sm leading-6 text-slate-600 dark:text-slate-300'>
                    {step.detail}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </section>
  );
}
