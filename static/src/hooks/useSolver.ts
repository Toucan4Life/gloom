// Drives the Pyodide-based solver: builds scenario/view request payloads
// from the current scenario state, requests solutions/reach/sight views
// when the active figure or display toggles change, and derives the
// per-hex display arrays (moves/attacks/aoe/focuses/destinations/
// sightlines/reach/sight) the board renders as overlays.
import { useEffect, useMemo, useRef, useState } from 'react';

import {
  CHARACTER,
  MONSTER,
  OBSTACLE,
  WALL,
  TRAP,
  HAZARDOUS_TERRAIN,
  DIFFICULT_TERRAIN,
  ICY_TERRAIN,
} from '../lib/brushes';
import { GRID_HEIGHT, GRID_SIZE, GRID_WIDTH } from '../lib/constants';
import { NULL_INDEX, type ScenarioState } from '../lib/scenarioState';
import { solveScenario, solveViews } from '../lib/pySolver';
import type {
  SolverAction,
  SolverExplanationStep,
  SolverScenarioMap,
  SolverScenarioRequest,
  SolverViewCollection,
  SolverViewsRequest,
} from '../lib/solverTypes';
import type { GridLine, GridPoint } from '../components/hexgrid/types';

function addElements(layer: ReadonlyArray<number | boolean>, brush: number): number[] {
  const locations: number[] = [];
  layer.forEach((element, index) => {
    if (element === brush) {
      locations.push(index);
    }
  });
  return locations;
}

function buildThinWalls(walls: ReadonlyArray<boolean>): [number, 0 | 1 | 2][] {
  const thinWalls: [number, 0 | 1 | 2][] = [];
  walls.forEach((wall, index) => {
    if (wall) {
      thinWalls.push([Math.trunc(index / 3), (index % 3) as 0 | 1 | 2]);
    }
  });
  return thinWalls;
}

function getSolveViewLevel(showReach: boolean, showSight: boolean): 0 | 1 | 2 {
  if (showSight) return 2;
  if (showReach) return 1;
  return 0;
}

function packScenario(
  scenario: ScenarioState,
  scenarioId: number,
  solveView: 0 | 1 | 2,
): SolverScenarioRequest {
  const inactiveFactionBrush = scenario.active_faction ? MONSTER : CHARACTER;

  const map: SolverScenarioMap = {
    characters: addElements(scenario.figures, CHARACTER),
    monsters: addElements(scenario.figures, MONSTER),
    walls: addElements(scenario.grid, WALL),
    obstacles: addElements(scenario.grid, OBSTACLE),
    traps: addElements(scenario.grid, TRAP),
    hazardous: addElements(scenario.grid, HAZARDOUS_TERRAIN),
    difficult: addElements(scenario.grid, DIFFICULT_TERRAIN),
    icy: addElements(scenario.grid, ICY_TERRAIN),
    thin_walls: buildThinWalls(scenario.walls),
    initiatives: [],
  };

  scenario.figures.forEach((figure, index) => {
    if (figure === inactiveFactionBrush) {
      map.initiatives.push(scenario.initiatives[index]);
    }
  });

  const aoe: number[] = [];
  scenario.aoe_grid.forEach((set, index) => {
    if (set) aoe.push(index);
  });

  return {
    scenario_id: scenarioId,
    solve_view: solveView,
    active_figure: scenario.active_figure_index,
    move: scenario.move,
    range: scenario.range,
    target: scenario.target,
    flying: scenario.flying,
    teleport: scenario.teleport,
    muddled: scenario.muddled,
    game_rules: scenario.game_rules,
    aoe,
    width: GRID_WIDTH,
    height: GRID_HEIGHT,
    map,
  };
}

function packScenarioForViews(
  scenario: ScenarioState,
  scenarioId: number,
  solveView: 0 | 1 | 2,
  viewpoints: number[],
): SolverViewsRequest {
  return {
    scenario_id: scenarioId,
    solve_view: solveView,
    range: scenario.range,
    target: scenario.target,
    game_rules: scenario.game_rules,
    width: GRID_WIDTH,
    height: GRID_HEIGHT,
    map: {
      walls: addElements(scenario.grid, WALL),
      thin_walls: buildThinWalls(scenario.walls),
    },
    viewpoints,
  };
}

function fillRanges(ranges: readonly (readonly [number, number])[] | null | undefined, target: boolean[]): void {
  ranges?.forEach(([start, end]) => {
    for (let location = start; location < end; location += 1) {
      target[location] = true;
    }
  });
}

export interface SolverDisplayState {
  pending: boolean;
  error: string | null;
  explanation: SolverExplanationStep[] | null;
  displayMoves: boolean[];
  displayAttacks: boolean[];
  displayAoe: boolean[];
  displayFocuses: boolean[];
  displayDestinations: boolean[];
  displaySightlineLines: GridLine[];
  displaySightlinePoints: GridPoint[];
  displayReach: boolean[];
  displaySight: boolean[];
  actionDisplayed: number;
  actionCount: number;
  isDisplayingSolution: boolean;
  setActionDisplayed: (value: number) => void;
  showPreviousAction: () => void;
  showNextAction: () => void;
  showAllActions: () => void;
}

const DISPLAY_ALL_ACTIONS = -1;

export function useSolver(
  scenario: ScenarioState,
  scenarioId: number,
  showMovement: boolean,
  showReach: boolean,
  showSight: boolean,
): SolverDisplayState {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [solutionScenarioId, setSolutionScenarioId] = useState<number | null>(null);
  const [actions, setActions] = useState<SolverAction[] | null>(null);
  const [actionsReach, setActionsReach] = useState<SolverViewCollection | null>(null);
  const [actionsSight, setActionsSight] = useState<SolverViewCollection | null>(null);
  const [startReach, setStartReach] = useState<SolverViewCollection[number] | null>(null);
  const [startSight, setStartSight] = useState<SolverViewCollection[number] | null>(null);
  const [explanation, setExplanation] = useState<SolverExplanationStep[] | null>(null);
  const [actionDisplayed, setActionDisplayedState] = useState(DISPLAY_ALL_ACTIONS);
  const requestSeq = useRef(0);

  const solveView = getSolveViewLevel(showReach, showSight);
  const activeFigureIndex = scenario.active_figure_index;
  const haveSolutionForScenario = solutionScenarioId === scenarioId;

  // Reset any cached solution once the scenario changes underneath it.
  useEffect(() => {
    if (!haveSolutionForScenario) {
      setActionDisplayedState(DISPLAY_ALL_ACTIONS);
    }
  }, [haveSolutionForScenario]);

  useEffect(() => {
    if (activeFigureIndex === NULL_INDEX) {
      setPending(false);
      setActions(null);
      setActionsReach(null);
      setActionsSight(null);
      setStartReach(null);
      setStartSight(null);
      setExplanation(null);
      setSolutionScenarioId(null);
      setError(null);
      return;
    }

    if (!showMovement && !showReach && !showSight) {
      setPending(false);
      return;
    }

    const seq = requestSeq.current + 1;
    requestSeq.current = seq;
    let cancelled = false;

    async function run() {
      setPending(true);
      setError(null);
      try {
        if (showMovement) {
          const response = await solveScenario(packScenario(scenario, scenarioId, solveView));
          if (cancelled || requestSeq.current !== seq) return;

          setSolutionScenarioId(response.scenario_id);
          setActions(response.actions);
          setActionsReach(response.reach ?? null);
          setActionsSight(response.sight ?? null);
          setExplanation(response.explanation ?? null);

          if (response.reach || response.sight) {
            const startIndex = response.actions.findIndex((action) => action.move === activeFigureIndex);
            if (startIndex >= 0) {
              setStartReach(response.reach ? response.reach[startIndex] : null);
              setStartSight(response.sight ? response.sight[startIndex] : null);
            }
          }
        } else {
          const response = await solveViews(
            packScenarioForViews(scenario, scenarioId, solveView, [activeFigureIndex]),
          );
          if (cancelled || requestSeq.current !== seq) return;

          setSolutionScenarioId(response.scenario_id);
          setActions(null);
          setActionsReach(null);
          setActionsSight(null);
          setExplanation(null);
          setStartReach(response.reach ? response.reach[0] : null);
          setStartSight(response.sight ? response.sight[0] : null);
        }
      } catch (caught) {
        if (cancelled || requestSeq.current !== seq) return;
        setError(caught instanceof Error ? caught.message : String(caught));
      } finally {
        if (!cancelled && requestSeq.current === seq) {
          setPending(false);
        }
      }
    }

    void run();

    return () => {
      cancelled = true;
    };
    // scenarioId captures every scenario field relevant to the solve; the
    // display toggles additionally affect solve_view / which request is sent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId, activeFigureIndex, showMovement, showReach, showSight]);

  const display = useMemo<Omit<SolverDisplayState, 'setActionDisplayed' | 'showPreviousAction' | 'showNextAction' | 'showAllActions'>>(() => {
    const moves = Array(GRID_SIZE).fill(false);
    const attacks = Array(GRID_SIZE).fill(false);
    const aoe = Array(GRID_SIZE).fill(false);
    const focuses = Array(GRID_SIZE).fill(false);
    const destinations = Array(GRID_SIZE).fill(false);
    const sightlineLines: GridLine[] = [];
    const reach = Array(GRID_SIZE).fill(false);
    const sight = Array(GRID_SIZE).fill(false);

    const isDisplayingSolution = haveSolutionForScenario;

    if (showMovement && actions && isDisplayingSolution) {
      const indices = actionDisplayed === DISPLAY_ALL_ACTIONS
        ? actions.map((_, index) => index)
        : [actionDisplayed];

      indices.forEach((index) => {
        const action = actions[index];
        if (!action) return;
        moves[action.move] = true;
        action.attacks.forEach((location) => { attacks[location] = true; });
        action.aoe.forEach((location) => { aoe[location] = true; });
        action.focuses.forEach((location) => { focuses[location] = true; });
        action.destinations.forEach((location) => { destinations[location] = true; });
        action.sightlines.forEach((line) => { sightlineLines.push(line as GridLine); });

        if (showReach && actionsReach) fillRanges(actionsReach[index], reach);
        if (showSight && actionsSight) fillRanges(actionsSight[index], sight);
      });
    } else if (isDisplayingSolution) {
      if (showReach) fillRanges(startReach, reach);
      if (showSight) fillRanges(startSight, sight);
    }

    const sightlinePoints: GridPoint[] = [];
    sightlineLines.forEach((line) => {
      sightlinePoints.push(line[0]);
      sightlinePoints.push(line[1]);
    });

    return {
      pending,
      error,
      explanation: isDisplayingSolution ? explanation : null,
      displayMoves: moves,
      displayAttacks: attacks,
      displayAoe: aoe,
      displayFocuses: focuses,
      displayDestinations: destinations,
      displaySightlineLines: sightlineLines,
      displaySightlinePoints: sightlinePoints,
      displayReach: reach,
      displaySight: sight,
      actionDisplayed,
      actionCount: actions?.length ?? 0,
      isDisplayingSolution,
    };
  }, [
    actions,
    actionsReach,
    actionsSight,
    startReach,
    startSight,
    explanation,
    actionDisplayed,
    showMovement,
    showReach,
    showSight,
    pending,
    error,
    haveSolutionForScenario,
  ]);

  const actionCount = display.actionCount;

  return {
    ...display,
    setActionDisplayed: setActionDisplayedState,
    showPreviousAction: () => {
      setActionDisplayedState((current) => {
        if (actionCount <= 1) return current;
        if (current === DISPLAY_ALL_ACTIONS) return actionCount - 1;
        if (current === 0) return actionCount - 1;
        return current - 1;
      });
    },
    showNextAction: () => {
      setActionDisplayedState((current) => {
        if (actionCount <= 1) return current;
        if (current === DISPLAY_ALL_ACTIONS) return 0;
        if (current === actionCount - 1) return 0;
        return current + 1;
      });
    },
    showAllActions: () => setActionDisplayedState(DISPLAY_ALL_ACTIONS),
  };
}
