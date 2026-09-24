// Gloomhaven Monster Mover — application shell. Wires the ported hex board,
// brush picker, property editor, and Pyodide solver bridge together into a
// single modern layout (top bar, tool palette, board, side panels).
import { useMemo, useRef, useState } from 'react';

import { EMPTY, THIN_WALL } from './lib/brushes';
import { GAME_RULES_OPTIONS, NULL_INDEX } from './lib/scenarioState';
import { AOE_TRANSFORM, AOE_VIEWBOX, GRID_HEIGHT, GRID_WIDTH } from './lib/constants';

import BrushPicker from './components/BrushPicker';
import PropertyEditor from './components/PropertyEditor';
import Figure from './components/Figure';
import ExplanationPanel from './components/ExplanationPanel';
import Message, { type MessageHandle } from './components/Message';
import { AOEHexGrid } from './components/hexgrid/AOEHexGrid';
import { Grid } from './components/hexgrid/Grid';
import { getGridHexCenter } from './components/hexgrid/hexUtils';
import { OVERLAY_HEX_KIND } from './components/hexgrid/types';

import { useMapEditor } from './hooks/useMapEditor';
import { useSolver } from './hooks/useSolver';

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

const INTERACTIVE_FOCUS_RING =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950';

export default function App() {
  const editor = useMapEditor();
  const solver = useSolver(
    editor.scenario,
    editor.scenarioId,
    editor.showMovement,
    editor.showReach,
    editor.showSight,
  );
  const messageRef = useRef<MessageHandle>(null);
  const [copyLabel, setCopyLabel] = useState('Share Scenario');
  const [mobilePanel, setMobilePanel] = useState<'palette' | 'board' | 'properties'>('board');

  const { scenario } = editor;
  const displaySolution = solver.isDisplayingSolution && editor.showMovement;
  const hasExtraDestinations = useMemo(
    () => solver.displayDestinations.some((isDestination, index) => isDestination && !solver.displayMoves[index]),
    [solver.displayDestinations, solver.displayMoves],
  );

  const figures = useMemo(() => {
    const nodes: JSX.Element[] = [];

    for (let column = 0, index = 0; column < GRID_WIDTH; column += 1) {
      for (let row = 0; row < GRID_HEIGHT; row += 1, index += 1) {
        const figure = scenario.figures[index];
        const move = displaySolution && solver.displayMoves[index];
        const destination = displaySolution && editor.showDestination && solver.displayDestinations[index];

        if (figure === EMPTY && !move && !destination) {
          continue;
        }

        const [x, y] = getGridHexCenter(column, row);
        const isActive = index === scenario.active_figure_index;

        nodes.push(
          <Figure
            key={index}
            x={x}
            y={y}
            figure={figure}
            initiative={scenario.initiatives[index]}
            flying={isActive ? scenario.flying : 0}
            teleport={isActive ? Boolean(scenario.teleport) : false}
            selected={index === editor.selection}
            rotate={Boolean(scenario.rotate_grid)}
            displaySolution={displaySolution}
            move={Boolean(move)}
            destination={Boolean(destination)}
            attack={displaySolution && solver.displayAttacks[index]}
            focus={displaySolution && editor.showFocus && solver.displayFocuses[index]}
            activeFaction={Boolean(scenario.active_faction)}
            activeFigure={isActive}
          />,
        );
      }
    }

    return nodes;
  }, [
    scenario.figures,
    scenario.initiatives,
    scenario.active_figure_index,
    scenario.flying,
    scenario.teleport,
    scenario.rotate_grid,
    scenario.active_faction,
    editor.selection,
    editor.showDestination,
    editor.showFocus,
    displaySolution,
    solver.displayMoves,
    solver.displayDestinations,
    solver.displayAttacks,
    solver.displayFocuses,
  ]);

  const overlayLayers = [
    { grid: solver.displayAoe, content: OVERLAY_HEX_KIND.AOE, show: displaySolution },
    { grid: solver.displayReach, content: OVERLAY_HEX_KIND.REACH, show: editor.showReach },
    { grid: solver.displaySight, content: OVERLAY_HEX_KIND.SIGHT, show: editor.showSight },
  ];

  const statusLabel = solver.pending
    ? (editor.showMovement ? 'Solving…' : 'Calculating…')
    : solver.error
      ? `Solver error: ${solver.error}`
      : scenario.active_figure_index === NULL_INDEX
        ? 'Place an active figure to see solver suggestions.'
        : displaySolution && solver.actionCount > 0
          ? solver.actionDisplayed === -1
            ? `Showing all ${solver.actionCount} movement option${solver.actionCount === 1 ? '' : 's'}.`
            : `Showing option ${solver.actionDisplayed + 1} of ${solver.actionCount}.`
          : null;

  const handleShare = async () => {
    const url = await editor.handleShareScenario();
    setCopyLabel('Copied!');
    messageRef.current?.display('alert-success', `Scenario link copied: ${url}`);
    window.setTimeout(() => setCopyLabel('Share Scenario'), 2000);
  };

  const handleResetClick = () => {
    if (window.confirm('Clear the entire board? This cannot be undone.')) {
      editor.handleReset();
    }
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-950 text-slate-100">
      <header className="shrink-0 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex flex-wrap items-center gap-2 px-3 py-2 sm:gap-4 sm:px-6">
          <div className="min-w-0">
            <p className="hidden text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300 sm:block">
              {typeof APP_NAME === 'string' ? APP_NAME : 'Gloomhaven Monster Mover'}
            </p>
            <h1 className="text-base font-semibold text-slate-50 sm:text-lg">Scenario board</h1>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-1.5 sm:gap-3">
            <label className="flex items-center gap-1.5 text-sm text-slate-300">
              <span className="hidden text-xs uppercase tracking-widest text-slate-500 sm:inline">Rules</span>
              <select
                value={scenario.game_rules}
                onChange={(event) => editor.handleGameRulesChange(Number(event.target.value) as 0 | 1 | 2)}
                className={cx(
                  'rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100 sm:text-sm',
                  INTERACTIVE_FOCUS_RING,
                )}
              >
                {GAME_RULES_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>

            <button
              type="button"
              onClick={editor.handleRotateToggle}
              aria-pressed={Boolean(scenario.rotate_grid)}
              title="Rotate board"
              className={cx(
                'rounded-lg border px-2 py-1.5 text-xs font-medium transition sm:px-3 sm:text-sm',
                INTERACTIVE_FOCUS_RING,
                scenario.rotate_grid
                  ? 'border-cyan-400/70 bg-cyan-400/15 text-cyan-100'
                  : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500',
              )}
            >
              <span className="sm:hidden">Rotate</span>
              <span className="hidden sm:inline">Rotate board</span>
            </button>

            <button
              type="button"
              onClick={handleShare}
              title="Share scenario"
              className={cx(
                'rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-300 hover:border-cyan-400/60 hover:text-cyan-100 sm:px-3 sm:text-sm',
                INTERACTIVE_FOCUS_RING,
              )}
            >
              <span className="sm:hidden">Share</span>
              <span className="hidden sm:inline">{copyLabel}</span>
            </button>

            <button
              type="button"
              onClick={handleResetClick}
              title="Reset board"
              className={cx(
                'rounded-lg border border-rose-800/70 bg-rose-950/40 px-2 py-1.5 text-xs font-medium text-rose-200 hover:border-rose-500 hover:bg-rose-900/40 sm:px-3 sm:text-sm',
                INTERACTIVE_FOCUS_RING,
              )}
            >
              <span className="sm:hidden">Reset</span>
              <span className="hidden sm:inline">Reset board</span>
            </button>
          </div>
        </div>
      </header>

      <nav className="flex shrink-0 items-center justify-center gap-1 border-b border-slate-800 bg-slate-950/80 px-2 py-1.5 lg:hidden">
        {([
          ['palette', 'Brushes'],
          ['board', 'Board'],
          ['properties', 'Details'],
        ] as const).map(([id, label]) => (
          <button
            key={id}
            type="button"
            aria-pressed={mobilePanel === id}
            onClick={() => setMobilePanel(id)}
            className={cx(
              'flex-1 rounded-lg border px-3 py-1.5 text-xs font-semibold uppercase tracking-wide transition',
              INTERACTIVE_FOCUS_RING,
              mobilePanel === id
                ? 'border-cyan-400/70 bg-cyan-400/15 text-cyan-100'
                : 'border-slate-800 bg-slate-900/70 text-slate-400 hover:border-slate-600',
            )}
          >
            {label}
          </button>
        ))}
      </nav>

      <main className="mx-auto grid w-full max-w-[1600px] flex-1 grid-cols-1 gap-3 overflow-y-auto px-3 py-3 sm:px-4 lg:min-h-0 lg:grid-cols-[260px_minmax(0,1fr)_300px] lg:overflow-hidden">
        <div
          className={cx(
            'min-h-0 flex-col gap-2 overflow-y-auto pr-1 lg:flex lg:min-h-0',
            mobilePanel === 'palette' ? 'flex' : 'hidden',
          )}
        >
          <BrushPicker
            selection={editor.brush}
            onSelection={editor.handleBrushSelection}
            activeFaction={scenario.active_faction}
            flying={scenario.flying}
            teleport={scenario.teleport}
            initiative={editor.nextInitiative}
          />

          <aside className="rounded-2xl border border-slate-800 bg-slate-900/85 p-2.5 shadow-2xl shadow-slate-950/30">
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">AOE template</h2>
              <span
                title="Left-click a hex to add or remove it from the pattern."
                className="cursor-help rounded-full border border-slate-700 px-1.5 py-0.5 text-[10px] font-medium text-slate-500"
              >
                ?
              </span>
            </div>
            <div className="flex justify-center">
              <svg viewBox={AOE_VIEWBOX} className="h-auto w-full max-w-[150px]">
                <g transform={AOE_TRANSFORM}>
                  <AOEHexGrid
                    grid={scenario.aoe_grid}
                    melee={scenario.range === 0}
                    onHexClick={editor.handleAoeClick}
                  />
                </g>
              </svg>
            </div>
            <button
              type="button"
              onClick={editor.handleClearAoe}
              className={cx(
                'mt-2 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-1.5 text-sm font-medium text-slate-300 hover:border-slate-500',
                INTERACTIVE_FOCUS_RING,
              )}
            >
              Clear area of effect
            </button>
          </aside>
        </div>

        <section
          className={cx(
            'min-h-0 flex-col items-center gap-2 lg:flex lg:min-h-0 lg:overflow-hidden',
            mobilePanel === 'board' ? 'flex' : 'hidden',
          )}
        >
          {statusLabel ? (
            <div className="flex shrink-0 items-center gap-2 rounded-full border border-slate-800 bg-slate-900/70 px-4 py-1.5 text-sm text-slate-300">
              {solver.pending ? (
                <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" aria-hidden="true" />
              ) : null}
              {statusLabel}
            </div>
          ) : null}

          <div className="max-h-[55vh] w-full min-h-0 overflow-auto rounded-2xl lg:max-h-none lg:flex-1">
            <Grid
              grid={scenario.grid}
              walls={scenario.walls}
              rotateGrid={Boolean(scenario.rotate_grid)}
              rotate={Boolean(scenario.rotate_grid)}
              overlayLayers={overlayLayers}
              showHexLabels={editor.showExplanation}
              sightLines={editor.showSightline && displaySolution ? solver.displaySightlineLines : null}
              sightPoints={editor.showSightline && displaySolution ? solver.displaySightlinePoints : null}
              onHexClick={editor.handleHexClick}
              onWallClick={editor.handleWallClick}
              activeWalls={editor.brush === THIN_WALL}
            >
              {figures}
            </Grid>
          </div>

          {displaySolution && solver.actionCount > 1 ? (
            <div className="flex shrink-0 items-center gap-3 rounded-full border border-slate-800 bg-slate-900/70 px-4 py-2 text-sm text-slate-300">
              <button
                type="button"
                onClick={solver.showPreviousAction}
                className={cx('rounded-md border border-slate-700 px-2 py-1 hover:border-cyan-400/60', INTERACTIVE_FOCUS_RING)}
              >
                ← Prev
              </button>
              <button
                type="button"
                onClick={solver.showAllActions}
                className={cx('rounded-md border border-slate-700 px-2 py-1 hover:border-cyan-400/60', INTERACTIVE_FOCUS_RING)}
              >
                Show all
              </button>
              <button
                type="button"
                onClick={solver.showNextAction}
                className={cx('rounded-md border border-slate-700 px-2 py-1 hover:border-cyan-400/60', INTERACTIVE_FOCUS_RING)}
              >
                Next →
              </button>
            </div>
          ) : null}

          <div className="flex shrink-0 flex-wrap justify-center gap-2">
            {([
              ['showMovement', 'Movement', editor.showMovement, editor.setShowMovement, undefined],
              ['showReach', 'Reach', editor.showReach, editor.setShowReach, undefined],
              ['showSight', 'Line of sight', editor.showSight, editor.setShowSight, undefined],
              [
                'showFocus',
                'Focus',
                editor.showFocus,
                editor.setShowFocus,
                'Highlights the character the monster is focusing (moving toward or attacking). Adds a gold halo around that figure.',
              ],
              [
                'showDestination',
                'Destination',
                editor.showDestination,
                editor.setShowDestination,
                'Shows alternate hexes the monster could land on instead. Only appears when several equally good hexes exist \u2013 usually when the monster is not attacking, since an attack locks in one specific hex.',
              ],
              [
                'showSightline',
                'Sightline',
                editor.showSightline,
                editor.setShowSightline,
                scenario.range === 0
                  ? 'Draws a line from the monster to a ranged target. Melee attacks target an adjacent hex, so there is no visible line to draw.'
                  : 'Draws a line from the monster to each target it can attack at range.',
              ],
              ['showExplanation', 'Explanation', editor.showExplanation, editor.setShowExplanation, undefined],
            ] as const).map(([key, label, value, setValue, title]) => (
              <button
                key={key}
                type="button"
                aria-pressed={value}
                title={title}
                onClick={() => setValue(!value)}
                className={cx(
                  'rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-wide transition',
                  INTERACTIVE_FOCUS_RING,
                  value
                    ? 'border-cyan-400/70 bg-cyan-400/15 text-cyan-100'
                    : 'border-slate-800 bg-slate-900/70 text-slate-400 hover:border-slate-600',
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {editor.showSightline && scenario.range === 0 ? (
            <p className="shrink-0 text-center text-xs text-slate-500">
              No sightline is drawn for melee attacks &ndash; the monster always ends up adjacent to its target.
            </p>
          ) : null}

          {editor.showDestination && solver.isDisplayingSolution && !hasExtraDestinations ? (
            <p className="shrink-0 text-center text-xs text-slate-500">
              Only one landing hex was possible here, so there is no alternate destination to show.
            </p>
          ) : null}

          {editor.showExplanation ? (
            <ExplanationPanel steps={solver.explanation} className="w-full shrink-0" />
          ) : null}
        </section>

        <div
          className={cx(
            'min-h-0 flex-col gap-2 overflow-y-auto pr-1 lg:flex lg:min-h-0',
            mobilePanel === 'properties' ? 'flex' : 'hidden',
          )}
        >
          <PropertyEditor
            move={scenario.move}
            range={scenario.range}
            target={scenario.target}
            flying={scenario.flying}
            teleport={scenario.teleport}
            muddled={scenario.muddled}
            initiative={editor.selectedInitiative}
            activeFaction={scenario.active_faction}
            onMoveChange={editor.handleMoveChange}
            onRangeChange={editor.handleRangeChange}
            onTargetChange={editor.handleTargetChange}
            onFlyingChange={editor.handleFlyingChange}
            onTeleportChange={editor.handleTeleportChange}
            onMuddledChange={editor.handleMuddledChange}
            onInitiativeChange={editor.handleInitiativeChange}
            onActiveFactionChange={editor.handleActiveFactionChange}
          />
        </div>
      </main>

      <footer className="shrink-0 border-t border-slate-800 bg-slate-950/90 px-3 py-2 text-center text-xs leading-5 text-slate-500">
        <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-0.5">
          <span>
            &copy; 2023-2026{' '}
            <a
              href="https://github.com/Toucan4Life"
              className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
            >
              Toucan4Life
            </a>
          </span>
          <a
            href="https://github.com/Toucan4Life/gloom"
            className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
          >
            github.com/Toucan4Life/gloom
          </a>
          <span>
            Based on the original work by{' '}
            <a
              href="mailto:daniel.richard.nelson@gmail.com"
              className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
            >
              Daniel Nelson
            </a>{' '}
            (
            <a
              href="https://github.com/AluminumAngel/gloom"
              className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
            >
              github.com/AluminumAngel/gloom
            </a>
            )
          </span>
          <a
            href="https://boardgamegeek.com/user/AluminumAngel"
            className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
          >
            boardgamegeek.com/user/AluminumAngel
          </a>
          <a
            href="https://www.reddit.com/user/AluminumAngel"
            className="text-slate-400 underline decoration-slate-700 underline-offset-2 hover:text-cyan-300"
          >
            u/AluminumAngel
          </a>
        </div>
      </footer>

      <Message ref={messageRef} />
    </div>
  );
}
