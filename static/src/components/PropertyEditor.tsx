import type {
  BinaryChoice,
  InitiativeValue,
  MovementValue,
  RangeValue,
  TargetValue,
  TraitValue,
} from '../lib/brushes';

import NumberSelector, { type NumberSelectorOption } from './NumberSelector';
import ToggleSwitch from './ToggleSwitch';

const MOVE_OPTIONS = [
  { value: 0, label: 'None' },
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4' },
  { value: 5, label: '5' },
  { value: 6, label: '6' },
  { value: 7, label: '7' },
  { value: 8, label: '8' },
  { value: 9, label: '9' },
] as const satisfies readonly NumberSelectorOption<MovementValue>[];

const RANGE_OPTIONS = [
  { value: 0, label: 'Melee' },
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4' },
  { value: 5, label: '5' },
  { value: 6, label: '6' },
  { value: 7, label: '7' },
  { value: 8, label: '8' },
  { value: 9, label: '9' },
] as const satisfies readonly NumberSelectorOption<RangeValue>[];

const TARGET_OPTIONS = [
  { value: 0, label: 'No attack' },
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4' },
  { value: 5, label: '5' },
  { value: 6, label: 'All' },
] as const satisfies readonly NumberSelectorOption<TargetValue>[];

const TRAIT_OPTIONS = [
  { value: 0, label: 'None' },
  { value: 1, label: 'Jump' },
  { value: 2, label: 'Flying' },
] as const satisfies readonly NumberSelectorOption<TraitValue>[];

const INITIATIVE_OPTIONS = [
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4' },
  { value: 5, label: '5' },
  { value: 6, label: '6' },
  { value: 7, label: '7' },
  { value: 8, label: '8' },
  { value: 9, label: '9' },
] as const satisfies readonly NumberSelectorOption<InitiativeValue>[];

const FACTION_OPTIONS = [
  { value: 1, label: 'Characters' },
  { value: 0, label: 'Monsters' },
] as const satisfies readonly NumberSelectorOption<0 | 1>[];

export interface PropertyEditorProps {
  move: MovementValue;
  range: RangeValue;
  target: TargetValue;
  flying: TraitValue;
  teleport: BinaryChoice;
  muddled: BinaryChoice;
  initiative: InitiativeValue | -1;
  activeFaction: BinaryChoice;
  onMoveChange: (value: MovementValue) => void;
  onRangeChange: (value: RangeValue) => void;
  onTargetChange: (value: TargetValue) => void;
  onFlyingChange: (value: TraitValue) => void;
  onTeleportChange: (value: 0 | 1) => void;
  onMuddledChange: (value: 0 | 1) => void;
  onInitiativeChange: (value: InitiativeValue) => void;
  onActiveFactionChange: (value: 0 | 1) => void;
  className?: string;
}

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

export default function PropertyEditor({
  move,
  range,
  target,
  flying,
  teleport,
  muddled,
  initiative,
  activeFaction,
  onMoveChange,
  onRangeChange,
  onTargetChange,
  onFlyingChange,
  onTeleportChange,
  onMuddledChange,
  onInitiativeChange,
  onActiveFactionChange,
  className,
}: PropertyEditorProps) {
  const activeFactionLabel = Boolean(activeFaction) ? 'character' : 'monster';
  const inactiveFactionLabel = Boolean(activeFaction) ? 'monster' : 'character';

  return (
    <aside
      className={cx(
        'rounded-2xl border border-slate-800 bg-slate-900/85 p-3 shadow-2xl shadow-slate-950/30',
        className,
      )}
    >
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Turn &amp; figure editor</h2>

      <div className="space-y-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Active faction"
            options={FACTION_OPTIONS}
            value={Boolean(activeFaction) ? 1 : 0}
            onChange={onActiveFactionChange}
            accent="cyan"
            description="Choose whether the current turn belongs to characters or monsters."
          />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Move"
            options={MOVE_OPTIONS}
            value={move}
            onChange={onMoveChange}
            accent="emerald"
            description="Set movement distance from 0–9. Use none when the turn has no move."
          />
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Range"
            options={RANGE_OPTIONS}
            value={range}
            onChange={onRangeChange}
            accent="cyan"
            description="Set attack range. Melee matches the legacy range 0 value."
          />
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Target"
            options={TARGET_OPTIONS}
            value={target}
            onChange={onTargetChange}
            accent="amber"
            description="Set number of targets, including no attack and all."
          />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Trait"
            options={TRAIT_OPTIONS}
            value={flying}
            onChange={onFlyingChange}
            accent="emerald"
            description="Select none, jump, or flying for the current move."
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
            <ToggleSwitch
              label="Teleport"
              checked={Boolean(teleport)}
              onChange={(checked) => onTeleportChange(checked ? 1 : 0)}
              accent="violet"
              description={`Set whether the active ${activeFactionLabel} is teleporting.`}
            />
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
            <ToggleSwitch
              label="Muddled"
              checked={Boolean(muddled)}
              onChange={(checked) => onMuddledChange(checked ? 1 : 0)}
              accent="rose"
              description={`Set whether the active ${activeFactionLabel} is muddled.`}
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/55 p-2">
          <NumberSelector
            label="Initiative"
            options={INITIATIVE_OPTIONS}
            value={initiative === -1 ? 1 : initiative}
            onChange={onInitiativeChange}
            disabled={initiative === -1}
            accent="amber"
            description={`Set the initiative rank of the selected ${inactiveFactionLabel}.`}
          />
        </div>
      </div>
    </aside>
  );
}
