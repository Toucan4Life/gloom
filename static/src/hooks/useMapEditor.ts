// Core scenario + tool state for the map editor: owns the persisted
// scenario fields (grid/figures/walls/active figure/etc.), the ephemeral
// tool/display state (brush selection, overlay toggles, selection), and all
// mutation handlers driven by board/UI interactions. Loads from a shared
// URL first, falling back to localStorage, mirroring the legacy
// MapEditor.jsx behaviour.
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  ACTIVE_FIGURE,
  CHARACTER,
  EMPTY,
  MONSTER,
  THIN_WALL,
  type BinaryChoice,
  type InitiativeValue,
  type MovementValue,
  type RangeValue,
  type SelectableBrush,
  type TargetValue,
  type TraitValue,
} from '../lib/brushes';
import { AOE_SIZE } from '../lib/constants';
import {
  decodeScenarioFromUrl,
  encodeScenarioToUrl,
} from '../lib/shareUrl';
import {
  isLocalStorageAvailable,
  restoreScenarioState,
  storeScenarioState,
} from '../lib/persistence';
import {
  MAX_INITIATIVE,
  NULL_INDEX,
  createDefaultScenarioState,
  type GameRulesValue,
  type ScenarioState,
} from '../lib/scenarioState';

function isFigureAllowed(content: ScenarioState['grid'][number]): boolean {
  return content !== 2; // BRUSH.WALL
}

function isFigureBrush(brush: number): brush is typeof CHARACTER | typeof MONSTER {
  return brush === MONSTER || brush === CHARACTER;
}

function determineNextInitiative(
  figures: ScenarioState['figures'],
  initiatives: ScenarioState['initiatives'],
  activeFaction: BinaryChoice,
): InitiativeValue {
  const initiativesUsed = Array(MAX_INITIATIVE).fill(false);
  const inactiveFactionBrush = activeFaction ? MONSTER : CHARACTER;
  figures.forEach((figure, index) => {
    if (figure === inactiveFactionBrush) {
      initiativesUsed[initiatives[index] - 1] = true;
    }
  });

  let firstOpenInitiative = 0;
  while (firstOpenInitiative < MAX_INITIATIVE && initiativesUsed[firstOpenInitiative]) {
    firstOpenInitiative += 1;
  }
  return Math.min(firstOpenInitiative + 1, MAX_INITIATIVE) as InitiativeValue;
}

function initializeScenarioState(): ScenarioState {
  const defaults = createDefaultScenarioState();

  const startingPath = typeof location === 'object' ? location.pathname.slice(URL_FOR.root.length) : '';
  const fromUrl = startingPath ? decodeScenarioFromUrl(location.pathname) : null;
  if (fromUrl) {
    return { ...defaults, ...fromUrl };
  }

  const fromStorage = restoreScenarioState();
  if (fromStorage) {
    return { ...defaults, ...fromStorage };
  }

  return defaults;
}

export interface MapEditorState {
  scenario: ScenarioState;
  scenarioId: number;
  brush: SelectableBrush;
  selection: number;
  showMovement: boolean;
  showReach: boolean;
  showSight: boolean;
  showFocus: boolean;
  showDestination: boolean;
  showSightline: boolean;
  showExplanation: boolean;
  nextInitiative: number;
}

export function useMapEditor() {
  const [scenario, setScenarioState] = useState<ScenarioState>(initializeScenarioState);
  const [scenarioId, setScenarioId] = useState(1);
  const [brush, setBrush] = useState<SelectableBrush>(15 as SelectableBrush); // PROGRESS
  const [selection, setSelection] = useState(NULL_INDEX);
  const [showMovement, setShowMovement] = useState(true);
  const [showReach, setShowReach] = useState(false);
  const [showSight, setShowSight] = useState(false);
  const [showFocus, setShowFocus] = useState(true);
  const [showDestination, setShowDestination] = useState(true);
  const [showSightline, setShowSightline] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const localStorageAvailable = useMemo(() => isLocalStorageAvailable(), []);

  useEffect(() => {
    if (localStorageAvailable) {
      storeScenarioState(scenario);
    }
    // Once loaded (whether from a share URL or storage), drop the token from
    // the address bar so reloads and edits don't keep replaying a stale link.
    if (location.pathname !== URL_FOR.root && location.pathname.slice(URL_FOR.root.length) !== '') {
      window.history.replaceState(null, '', URL_FOR.root);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const commitScenario = useCallback((updates: Partial<ScenarioState>) => {
    setScenarioState((current) => {
      const next = { ...current, ...updates };
      if (localStorageAvailable) {
        storeScenarioState(updates);
      }
      return next;
    });
    setScenarioId((current) => (current + 1) % (256 * 256 * 256));
  }, [localStorageAvailable]);

  const activeFactionBrush = scenario.active_faction ? CHARACTER : MONSTER;
  const inactiveFactionBrush = scenario.active_faction ? MONSTER : CHARACTER;

  const nextInitiative = useMemo(
    () => determineNextInitiative(scenario.figures, scenario.initiatives, scenario.active_faction),
    [scenario.figures, scenario.initiatives, scenario.active_faction],
  );

  const handleBrushSelection = useCallback((nextBrush: SelectableBrush) => {
    // Selecting the already-active brush toggles back to the default
    // "interact" brush (PROGRESS) so there's no separate mode button needed
    // to get back to selecting/activating figures.
    setBrush((current) => (current === nextBrush ? (15 as SelectableBrush) : nextBrush));
  }, []);

  const handleHexClick = useCallback((primary: boolean, index: number) => {
    const content = scenario.grid[index];
    const figure = scenario.figures[index];

    let grid: ScenarioState['grid'] | null = null;
    let figures: ScenarioState['figures'] | null = null;
    let initiatives: ScenarioState['initiatives'] | null = null;
    let activeFigureIndex = scenario.active_figure_index;
    let nextSelection = selection;

    // Any hex that already holds a figure is always selectable/activatable by
    // clicking it directly, no matter which brush is currently picked -
    // painting brushes only ever apply to empty hexes. This keeps figure
    // selection always available without a dedicated "interact" mode button.
    const isFigurePlacementBrush = brush === ACTIVE_FIGURE || isFigureBrush(brush);

    if (isFigureBrush(figure) && !isFigurePlacementBrush) {
      if (primary) {
        if (figure === activeFactionBrush) {
          activeFigureIndex = activeFigureIndex !== index ? index : NULL_INDEX;
          nextSelection = NULL_INDEX;
        } else {
          nextSelection = nextSelection !== index ? index : NULL_INDEX;
        }
      } else {
        if (index === activeFigureIndex) {
          activeFigureIndex = NULL_INDEX;
        }
        figures = scenario.figures.slice() as ScenarioState['figures'];
        figures[index] = EMPTY;
        nextSelection = NULL_INDEX;
      }
    } else if (primary) {
      if (brush === ACTIVE_FIGURE) {
        if (figure === activeFactionBrush && activeFigureIndex === index) {
          figures = scenario.figures.slice() as ScenarioState['figures'];
          figures[index] = EMPTY;
          activeFigureIndex = NULL_INDEX;
          nextSelection = NULL_INDEX;
        } else if (isFigureAllowed(content)) {
          figures = scenario.figures.slice() as ScenarioState['figures'];
          figures[index] = activeFactionBrush;
          initiatives = scenario.initiatives.slice() as ScenarioState['initiatives'];
          initiatives[index] = 1 as InitiativeValue;
          if (activeFigureIndex !== NULL_INDEX) {
            figures[activeFigureIndex] = EMPTY;
          }
          activeFigureIndex = index;
          nextSelection = NULL_INDEX;
        }
      } else if (isFigureBrush(brush)) {
        if (figure === brush && activeFigureIndex !== index) {
          if (brush === inactiveFactionBrush) {
            nextSelection = nextSelection === index ? NULL_INDEX : index;
          } else {
            figures = scenario.figures.slice() as ScenarioState['figures'];
            figures[index] = EMPTY;
            nextSelection = NULL_INDEX;
          }
        } else if (isFigureAllowed(content)) {
          figures = scenario.figures.slice() as ScenarioState['figures'];
          figures[index] = brush;
          if (activeFigureIndex === index) {
            activeFigureIndex = NULL_INDEX;
          }
          initiatives = scenario.initiatives.slice() as ScenarioState['initiatives'];
          if (brush === inactiveFactionBrush) {
            initiatives[index] = nextInitiative as InitiativeValue;
            nextSelection = index;
          } else {
            initiatives[index] = 1 as InitiativeValue;
            nextSelection = NULL_INDEX;
          }
        }
      } else if (brush !== 15 /* PROGRESS: no brush picked, empty hexes are a no-op */) {
        // terrain brush (the hex is guaranteed free of figures here)
        grid = scenario.grid.slice() as ScenarioState['grid'];
        grid[index] = grid[index] === brush ? EMPTY : (brush as ScenarioState['grid'][number]);
      }
    } else if (brush !== ACTIVE_FIGURE && !isFigureBrush(brush) && brush !== 15 /* PROGRESS */) {
      grid = scenario.grid.slice() as ScenarioState['grid'];
      grid[index] = EMPTY;
    }

    if (grid || figures || initiatives || activeFigureIndex !== scenario.active_figure_index) {
      commitScenario({
        ...(grid ? { grid } : {}),
        ...(figures ? { figures } : {}),
        ...(initiatives ? { initiatives } : {}),
        active_figure_index: activeFigureIndex,
      });
    }
    setSelection(nextSelection);
  }, [scenario, brush, selection, activeFactionBrush, inactiveFactionBrush, nextInitiative, commitScenario]);

  const handleWallClick = useCallback((primary: boolean, index: number) => {
    const walls = scenario.walls.slice();
    walls[index] = primary ? !walls[index] : false;
    commitScenario({ walls });
    setSelection(NULL_INDEX);
  }, [scenario.walls, commitScenario]);

  const handleAoeClick = useCallback((primary: boolean, index: number) => {
    const aoeGrid = scenario.aoe_grid.slice();
    aoeGrid[index] = primary ? !aoeGrid[index] : false;
    commitScenario({ aoe_grid: aoeGrid });
  }, [scenario.aoe_grid, commitScenario]);

  const handleClearAoe = useCallback(() => {
    commitScenario({ aoe_grid: Array(AOE_SIZE).fill(false) });
  }, [commitScenario]);

  const handleMoveChange = useCallback((value: MovementValue) => commitScenario({ move: value }), [commitScenario]);
  const handleRangeChange = useCallback((value: RangeValue) => commitScenario({ range: value }), [commitScenario]);
  const handleTargetChange = useCallback((value: TargetValue) => commitScenario({ target: value }), [commitScenario]);
  const handleFlyingChange = useCallback((value: TraitValue) => commitScenario({ flying: value }), [commitScenario]);
  const handleTeleportChange = useCallback((value: 0 | 1) => commitScenario({ teleport: value }), [commitScenario]);
  const handleMuddledChange = useCallback((value: 0 | 1) => commitScenario({ muddled: value }), [commitScenario]);
  const handleGameRulesChange = useCallback(
    (value: GameRulesValue) => commitScenario({ game_rules: value }),
    [commitScenario],
  );
  const handleRotateToggle = useCallback(() => {
    commitScenario({ rotate_grid: !scenario.rotate_grid });
  }, [scenario.rotate_grid, commitScenario]);
  const handleActiveFactionChange = useCallback((value: 0 | 1) => {
    commitScenario({ active_faction: Boolean(value), active_figure_index: NULL_INDEX });
    setSelection(NULL_INDEX);
  }, [commitScenario]);

  const handleInitiativeChange = useCallback((value: InitiativeValue) => {
    if (selection === NULL_INDEX) {
      return;
    }
    const initiatives = scenario.initiatives.slice() as ScenarioState['initiatives'];
    initiatives[selection] = value;
    commitScenario({ initiatives });
  }, [selection, scenario.initiatives, commitScenario]);

  const handleReset = useCallback(() => {
    commitScenario(createDefaultScenarioState());
    setSelection(NULL_INDEX);
    setBrush(15 as SelectableBrush);
  }, [commitScenario]);

  const handleShareScenario = useCallback(async (): Promise<string> => {
    const url = encodeScenarioToUrl(scenario);
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Clipboard access can fail (permissions, insecure context); the
      // caller still receives the URL and can present it to the user.
    }
    return url;
  }, [scenario]);

  const selectedInitiative: InitiativeValue | -1 = selection === NULL_INDEX
    ? -1
    : scenario.initiatives[selection];

  return {
    scenario,
    scenarioId,
    brush,
    selection,
    nextInitiative,
    activeFactionBrush,
    inactiveFactionBrush,
    selectedInitiative,
    showMovement,
    showReach,
    showSight,
    showFocus,
    showDestination,
    showSightline,
    showExplanation,
    setShowMovement,
    setShowReach,
    setShowSight,
    setShowFocus,
    setShowDestination,
    setShowSightline,
    setShowExplanation,
    handleBrushSelection,
    handleHexClick,
    handleWallClick,
    handleAoeClick,
    handleClearAoe,
    handleMoveChange,
    handleRangeChange,
    handleTargetChange,
    handleFlyingChange,
    handleTeleportChange,
    handleMuddledChange,
    handleGameRulesChange,
    handleRotateToggle,
    handleActiveFactionChange,
    handleInitiativeChange,
    handleReset,
    handleShareScenario,
    setSelection,
  } as const;
}

export const THIN_WALL_BRUSH = THIN_WALL;
