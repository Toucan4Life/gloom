import type { ReactNode } from 'react';

import { SCALE, SQRT_3_OVER_2 } from '../lib/constants';
import {
  ACTIVE_FIGURE,
  CHARACTER,
  DIFFICULT_TERRAIN,
  HAZARDOUS_TERRAIN,
  ICY_TERRAIN,
  MONSTER,
  OBSTACLE,
  THIN_WALL,
  TRAP,
  WALL,
  getActiveFigureBrush,
  getBrushLabel,
  type InitiativeValue,
  type SelectableBrush,
  type TraitValue,
} from '../lib/brushes';

import BrushButton from './BrushButton';
import FigureIcon from './FigureIcon';

const HEX_POINTS = [
  [0, -SCALE],
  [SCALE * SQRT_3_OVER_2, -SCALE / 2],
  [SCALE * SQRT_3_OVER_2, SCALE / 2],
  [0, SCALE],
  [-SCALE * SQRT_3_OVER_2, SCALE / 2],
  [-SCALE * SQRT_3_OVER_2, -SCALE / 2],
]
  .map(([x, y]) => `${x},${y}`)
  .join(' ');

const WALL_POINTS = [
  [-SCALE * 0.45, -SCALE * 0.58],
  [SCALE * 0.45, SCALE * 0.58],
]
  .map(([x, y]) => `${x},${y}`)
  .join(' ');

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

function PanelIcon({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <svg viewBox="-24 -24 48 48" className={cx('h-8 w-8 overflow-visible', className)} aria-hidden="true">
      {children}
    </svg>
  );
}

function TerrainIcon({ brush }: { brush: SelectableBrush }) {
  const fillMap: Partial<Record<SelectableBrush, string>> = {
    [TRAP]: '#fb7185',
    [HAZARDOUS_TERRAIN]: '#f97316',
    [DIFFICULT_TERRAIN]: '#eab308',
    [ICY_TERRAIN]: '#67e8f9',
  };

  if (brush === THIN_WALL) {
    return (
      <PanelIcon>
        <polyline
          points={WALL_POINTS}
          fill="none"
          stroke="#f8fafc"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={4}
        />
      </PanelIcon>
    );
  }

  if (brush === WALL) {
    // Solid brick wall: cool slate tones + a brick coursing pattern so it
    // reads as a hard, impassable barrier (distinct from Obstacle's rubble).
    return (
      <PanelIcon>
        <defs>
          <linearGradient id="wallGradient" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#cbd5e1" />
            <stop offset="100%" stopColor="#334155" />
          </linearGradient>
          <clipPath id="wallClip">
            <polygon points={HEX_POINTS} />
          </clipPath>
        </defs>
        <polygon points={HEX_POINTS} fill="url(#wallGradient)" stroke="#f8fafc" strokeWidth={1.5} />
        <g clipPath="url(#wallClip)" stroke="#1e293b" strokeWidth={1.2} strokeLinecap="round" opacity={0.8}>
          <path d="M-12 -12 H12 M-12 -4 H12 M-12 4 H12 M-12 12 H12" />
          <path d="M-6 -12 V-4 M6 -12 V-4 M0 -4 V4 M-6 4 V12 M6 4 V12" />
        </g>
      </PanelIcon>
    );
  }

  if (brush === OBSTACLE) {
    // Rubble/boulder pile: warm stone tones + an irregular rounded silhouette
    // so it reads as a physical obstruction (distinct from Wall's brickwork).
    return (
      <PanelIcon>
        <polygon points={HEX_POINTS} fill="#1e293b" stroke="#475569" strokeOpacity={0.6} strokeWidth={1} />
        <path
          d="M-9 8 C-10 2 -7 -3 -2 -2 C-1 -8 6 -9 8 -3 C12 -1 11 5 8 8 C3 10 -5 10 -9 8 Z"
          fill="#a8794f"
          stroke="#5c3d21"
          strokeWidth={1.2}
          strokeLinejoin="round"
        />
        <path
          d="M-4 3 Q-1 -1 3 1 M-2 6 Q2 4 5 6"
          fill="none"
          stroke="#5c3d21"
          strokeOpacity={0.6}
          strokeLinecap="round"
          strokeWidth={1}
        />
      </PanelIcon>
    );
  }

  return (
    <PanelIcon>
      <polygon points={HEX_POINTS} fill={fillMap[brush]} stroke="#f8fafc" strokeOpacity={0.85} strokeWidth={1.5} />
      {brush === TRAP ? (
        <path
          d="M-6 7 L0 -7 L6 7 M-4 11 h8"
          fill="none"
          stroke="#431407"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
        />
      ) : null}
      {brush === HAZARDOUS_TERRAIN ? (
        <path
          d="M-7 8 C-2 4 -1 -4 2 -7 C2 -2 5 0 7 7 C5 5 3 4 1 6 C-1 7 -4 8 -7 8z"
          fill="#7c2d12"
          opacity={0.75}
        />
      ) : null}
      {brush === DIFFICULT_TERRAIN ? (
        <path
          d="M-8 5 Q-4 0 0 4 T8 4"
          fill="none"
          stroke="#78350f"
          strokeLinecap="round"
          strokeWidth={2.2}
        />
      ) : null}
      {brush === ICY_TERRAIN ? (
        <path
          d="M0 -8 v16 M-6 -4 l12 8 M6 -4 l-12 8"
          fill="none"
          stroke="#083344"
          strokeLinecap="round"
          strokeWidth={2}
        />
      ) : null}
    </PanelIcon>
  );
}

function FigurePreview({
  brush,
  activeFaction,
  flying,
  teleport,
  initiative,
}: {
  brush: typeof ACTIVE_FIGURE | typeof CHARACTER | typeof MONSTER;
  activeFaction: boolean;
  flying: TraitValue;
  teleport: boolean;
  initiative: InitiativeValue;
}) {
  const displayBrush = brush === ACTIVE_FIGURE ? getActiveFigureBrush(activeFaction) : brush;

  return (
    <PanelIcon className="overflow-visible">
      <FigureIcon
        x={0}
        y={0}
        figure={displayBrush}
        flying={flying}
        teleport={teleport}
        initiative={initiative}
        activeFaction={activeFaction}
      />
    </PanelIcon>
  );
}

function getBrushDescription(brush: SelectableBrush, activeFaction: boolean): string {
  switch (brush) {
    case ACTIVE_FIGURE:
      return activeFaction
        ? 'Place or remove the active character on the board.'
        : 'Place or remove the active monster on the board.';
    case CHARACTER:
      return activeFaction
        ? 'Place or remove a character figure.'
        : 'Place a character and select one to adjust initiative.';
    case MONSTER:
      return activeFaction
        ? 'Place a monster and select one to adjust initiative.'
        : 'Place or remove a monster figure.';
    case WALL:
      return 'Paint full wall hexes on the scenario board.';
    case OBSTACLE:
      return 'Paint obstacle hexes that block movement.';
    case TRAP:
      return 'Paint trap hexes.';
    case HAZARDOUS_TERRAIN:
      return 'Paint hazardous terrain hexes.';
    case DIFFICULT_TERRAIN:
      return 'Paint difficult terrain hexes.';
    case ICY_TERRAIN:
      return 'Paint icy terrain hexes.';
    case THIN_WALL:
      return 'Paint wall-line segments between hexes.';
    default:
      return '';
  }
}

export interface BrushPickerProps {
  selection: SelectableBrush;
  onSelection: (brush: SelectableBrush) => void;
  activeFaction: boolean | 0 | 1;
  flying?: TraitValue;
  teleport?: boolean | 0 | 1;
  initiative?: InitiativeValue;
  className?: string;
}

export default function BrushPicker({
  selection,
  onSelection,
  activeFaction,
  flying = 0,
  teleport = false,
  initiative = 1,
  className,
}: BrushPickerProps) {
  const currentFaction = Boolean(activeFaction);
  const sections = [
    {
      title: 'Figures',
      accent: 'emerald' as const,
      brushes: [ACTIVE_FIGURE, CHARACTER, MONSTER] as const,
    },
    {
      title: 'Terrain & Obstacles',
      accent: 'amber' as const,
      brushes: [WALL, OBSTACLE, TRAP, HAZARDOUS_TERRAIN, DIFFICULT_TERRAIN, ICY_TERRAIN, THIN_WALL] as const,
    },
  ];

  return (
    <aside
      className={cx(
        'rounded-2xl border border-slate-800 bg-slate-900/85 p-3 shadow-2xl shadow-slate-950/30',
        className,
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Brush picker</h2>
        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.2em] text-slate-400">
          {currentFaction ? 'Character turn' : 'Monster turn'}
        </span>
      </div>

      <p className="mb-3 text-[11px] leading-snug text-slate-500">
        Click any figure on the board to select or activate it. Pick a brush below to paint terrain or place
        figures; click a selected brush again to put it away.
      </p>

      <div className="space-y-3">
        {sections.map((section) => (
          <section key={section.title} className="space-y-1.5">
            <h3 className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500">{section.title}</h3>
            <div className="grid grid-cols-3 gap-1.5">
              {section.brushes.map((brush) => (
                <BrushButton
                  key={brush}
                  brush={brush}
                  label={getBrushLabel(brush, currentFaction)}
                  description={getBrushDescription(brush, currentFaction)}
                  isSelected={selection === brush}
                  onClick={onSelection}
                  accent={section.accent}
                  icon={
                    brush === ACTIVE_FIGURE || brush === CHARACTER || brush === MONSTER ? (
                      <FigurePreview
                        brush={brush}
                        activeFaction={currentFaction}
                        flying={flying}
                        teleport={Boolean(teleport)}
                        initiative={initiative}
                      />
                    ) : (
                      <TerrainIcon brush={brush} />
                    )
                  }
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </aside>
  );
}
