import BitReader from './bitReader';
import BitWriter from './bitWriter';
import {
  AOE_GRID_SKIP_LIST,
  AOE_SIZE,
  AOE_SIZE_BITS,
  COLUMN_ADJUST,
  GRID_HEIGHT,
  GRID_HEIGHT_V0,
  GRID_SIZE,
  GRID_SIZE_BITS,
  GRID_SIZE_BITS_V0,
  GRID_SIZE_V0,
  ROW_ADJUST,
} from './constants';
import {
  EMPTY,
  FIRST_FIGURE_BRUSH,
  FIRST_TERRAIN_BRUSH,
  LAST_FIGURE_BRUSH,
  LAST_TERRAIN_BRUSH,
  MONSTER,
  CHARACTER,
} from './brushes';
import {
  createDefaultScenarioState,
  GAME_RULES_GLOOM,
  GAME_RULES_JOTL,
  MAX_INITIATIVE,
  NULL_INDEX,
  SIMPLE_STATE_KEYS,
  SIMPLE_STATE_PROPERTIES,
  type BooleanBit,
  type ScenarioState,
} from './scenarioState';

const BAD_SCENARIO_URL_ERROR = 'bad scenario URL';

type GridMappingEntry = {
  content: number;
  figure: number;
  walls: [boolean, boolean, boolean];
  initiative: number;
};

type LegacyVersionFlags = {
  gameRulesDataVersion: 0 | 1 | 2;
  gridDataVersion: 0 | 1;
  teleportDataVersion: 0 | 1;
};

function validate(value: number, min: number, max: number): void {
  if (value < min || value > max) {
    throw BAD_SCENARIO_URL_ERROR;
  }
}

function toBitValue(value: number | BooleanBit): number {
  return typeof value === 'boolean' ? Number(value) : value;
}

function createGridMapping(state: ScenarioState): Record<number, GridMappingEntry> {
  const gridMapping: Record<number, GridMappingEntry> = {};

  function addEntry(location: number): void {
    if (!(location in gridMapping)) {
      gridMapping[location] = {
        content: EMPTY,
        figure: EMPTY,
        walls: [false, false, false],
        initiative: 1,
      };
    }
  }

  state.grid.forEach((element, location) => {
    if (element !== EMPTY) {
      addEntry(location);
      gridMapping[location]!.content = element;
    }
  });

  state.figures.forEach((element, location) => {
    if (element !== EMPTY) {
      addEntry(location);
      gridMapping[location]!.figure = element;
      gridMapping[location]!.initiative = state.initiatives[location] ?? 1;
    }
  });

  state.walls.forEach((element, index) => {
    if (element) {
      const location = Math.floor(index / 3);
      const wallIndex = index - 3 * location;
      addEntry(location);
      gridMapping[location]!.walls[wallIndex as 0 | 1 | 2] = true;
    }
  });

  return gridMapping;
}

function getLegacyVersionFlags(
  dataVersionMajor: number,
  dataVersionMinor: number,
  dataVersionBuild: number,
): LegacyVersionFlags {
  if (dataVersionMajor === 1 && dataVersionMinor === 0 && dataVersionBuild === 0) {
    return {
      gameRulesDataVersion: 0,
      gridDataVersion: 0,
      teleportDataVersion: 0,
    };
  }

  if (dataVersionMajor === 1 && dataVersionMinor === 1 && dataVersionBuild === 0) {
    return {
      gameRulesDataVersion: 1,
      gridDataVersion: 0,
      teleportDataVersion: 0,
    };
  }

  if (dataVersionMajor === 1 && dataVersionMinor === 2 && dataVersionBuild === 0) {
    return {
      gameRulesDataVersion: 2,
      gridDataVersion: 0,
      teleportDataVersion: 0,
    };
  }

  if (
    dataVersionMajor === 1
    && (dataVersionMinor === 3 || dataVersionMinor === 4)
    && dataVersionBuild === 0
  ) {
    return {
      gameRulesDataVersion: 2,
      gridDataVersion: 1,
      teleportDataVersion: 0,
    };
  }

  if (
    dataVersionMajor === DATA_VERSION_MAJOR
    && dataVersionMinor === DATA_VERSION_MINOR
    && dataVersionBuild === DATA_VERSION_BUILD
  ) {
    return {
      gameRulesDataVersion: 2,
      gridDataVersion: 1,
      teleportDataVersion: 1,
    };
  }

  throw BAD_SCENARIO_URL_ERROR;
}

function extractScenarioToken(path: string): string | null {
  const trimmedPath = path.trim();
  if (trimmedPath.length === 0) {
    return null;
  }

  if (!trimmedPath.includes('/') && !trimmedPath.includes('?') && !trimmedPath.includes('#')) {
    return trimmedPath;
  }

  const parsedUrl = new URL(trimmedPath, 'https://example.invalid');
  const pathname = parsedUrl.pathname;

  if (pathname.startsWith(URL_FOR.root)) {
    return pathname.slice(URL_FOR.root.length) || null;
  }

  const segments = pathname.split('/').filter(Boolean);
  return segments.at(-1) ?? null;
}

function encodeScenarioToken(state: ScenarioState): string {
  const gridMapping = createGridMapping(state);
  const bitWriter = new BitWriter();

  bitWriter.writeBits(4, DATA_VERSION_MAJOR);
  bitWriter.writeBits(3, DATA_VERSION_MINOR);
  bitWriter.writeBits(3, DATA_VERSION_BUILD);

  SIMPLE_STATE_KEYS.forEach((key) => {
    bitWriter.writeBits(SIMPLE_STATE_PROPERTIES[key].bits, toBitValue(state[key]));
  });

  bitWriter.writeBits(SIMPLE_STATE_PROPERTIES.game_rules.bits, state.game_rules);
  bitWriter.writeBits(SIMPLE_STATE_PROPERTIES.teleport.bits, toBitValue(state.teleport));

  let activeFigureIndex = state.active_figure_index;
  if (activeFigureIndex === NULL_INDEX) {
    activeFigureIndex = GRID_SIZE;
  }
  bitWriter.writeBits(GRID_SIZE_BITS, activeFigureIndex);

  let aoeGridCount = 0;
  state.aoe_grid.forEach((element) => {
    if (element) {
      aoeGridCount += 1;
    }
  });
  bitWriter.writeBits(AOE_SIZE_BITS, aoeGridCount);
  state.aoe_grid.forEach((element, index) => {
    if (element) {
      bitWriter.writeBits(AOE_SIZE_BITS, index);
    }
  });

  const orderedGridMappingKeys = Object.keys(gridMapping).sort((a, b) => Number(a) - Number(b));
  bitWriter.writeBits(GRID_SIZE_BITS, orderedGridMappingKeys.length);
  let lastLocationWritten = -1;

  orderedGridMappingKeys.forEach((locationString) => {
    const location = Number(locationString);
    const locationDelta = location - lastLocationWritten - 1;
    if (locationDelta < 4) {
      bitWriter.writeBits(1, 0);
      bitWriter.writeBits(2, locationDelta);
    }
    else {
      bitWriter.writeBits(1, 1);
      bitWriter.writeBits(GRID_SIZE_BITS, locationDelta);
    }
    lastLocationWritten = location;

    const entry = gridMapping[location]!;
    bitWriter.writeBits(3, entry.content);
    if (entry.figure !== EMPTY) {
      bitWriter.writeBits(2, entry.figure - FIRST_FIGURE_BRUSH + 1);
      bitWriter.writeBits(4, entry.initiative);
    }
    else {
      bitWriter.writeBits(2, 0);
    }

    const anyWalls = entry.walls[0] || entry.walls[1] || entry.walls[2];
    bitWriter.writeBits(1, anyWalls ? 1 : 0);
    if (anyWalls) {
      bitWriter.writeBits(1, entry.walls[0] ? 1 : 0);
      bitWriter.writeBits(1, entry.walls[1] ? 1 : 0);
      bitWriter.writeBits(1, entry.walls[2] ? 1 : 0);
    }
  });

  bitWriter.flush();
  return bitWriter.result();
}

function decodeScenarioToken(token: string): ScenarioState {
  const scenarioState = createDefaultScenarioState();
  const bitReader = new BitReader(token);

  const dataVersionMajor = bitReader.readBits(4);
  const dataVersionMinor = bitReader.readBits(3);
  const dataVersionBuild = bitReader.readBits(3);
  const { gameRulesDataVersion, gridDataVersion, teleportDataVersion } = getLegacyVersionFlags(
    dataVersionMajor,
    dataVersionMinor,
    dataVersionBuild,
  );

  SIMPLE_STATE_KEYS.forEach((key) => {
    const value = bitReader.readBits(SIMPLE_STATE_PROPERTIES[key].bits);
    validate(value, SIMPLE_STATE_PROPERTIES[key].min, SIMPLE_STATE_PROPERTIES[key].max);
    switch (key) {
      case 'move':
        scenarioState.move = value as ScenarioState['move'];
        break;
      case 'range':
        scenarioState.range = value as ScenarioState['range'];
        break;
      case 'target':
        scenarioState.target = value as ScenarioState['target'];
        break;
      case 'flying':
        scenarioState.flying = value as ScenarioState['flying'];
        break;
      case 'muddled':
        scenarioState.muddled = value as ScenarioState['muddled'];
        break;
      case 'active_faction':
        scenarioState.active_faction = value === 1;
        break;
      case 'rotate_grid':
        scenarioState.rotate_grid = value === 1;
        break;
    }
  });

  if (gameRulesDataVersion === 0) {
    scenarioState.game_rules = GAME_RULES_GLOOM;
  }
  else if (gameRulesDataVersion === 1) {
    const value = bitReader.readBits(SIMPLE_STATE_PROPERTIES.jotl.bits);
    validate(value, SIMPLE_STATE_PROPERTIES.jotl.min, SIMPLE_STATE_PROPERTIES.jotl.max);
    scenarioState.game_rules = value === 0 ? GAME_RULES_GLOOM : GAME_RULES_JOTL;
  }
  else {
    const value = bitReader.readBits(SIMPLE_STATE_PROPERTIES.game_rules.bits);
    validate(value, SIMPLE_STATE_PROPERTIES.game_rules.min, SIMPLE_STATE_PROPERTIES.game_rules.max);
    scenarioState.game_rules = value as ScenarioState['game_rules'];
  }

  if (teleportDataVersion === 0) {
    scenarioState.teleport = 0;
  }
  else {
    const value = bitReader.readBits(SIMPLE_STATE_PROPERTIES.teleport.bits);
    validate(value, SIMPLE_STATE_PROPERTIES.teleport.min, SIMPLE_STATE_PROPERTIES.teleport.max);
    scenarioState.teleport = value as ScenarioState['teleport'];
  }

  let gridSize: number;
  let gridSizeBits: number;
  let adjustLocation: (location: number) => number;
  if (gridDataVersion === 0) {
    gridSize = GRID_SIZE_V0;
    gridSizeBits = GRID_SIZE_BITS_V0;
    adjustLocation = (location: number) => {
      const column = Math.floor(location / GRID_HEIGHT_V0) + COLUMN_ADJUST;
      const row = location % GRID_HEIGHT_V0 + ROW_ADJUST - (column % 2);
      return column * GRID_HEIGHT + row;
    };
  }
  else {
    gridSize = GRID_SIZE;
    gridSizeBits = GRID_SIZE_BITS;
    adjustLocation = (location: number) => location;
  }

  let activeFigureIndex = bitReader.readBits(gridSizeBits);
  validate(activeFigureIndex, 0, gridSize);
  if (activeFigureIndex === gridSize) {
    activeFigureIndex = NULL_INDEX;
  }
  else {
    activeFigureIndex = adjustLocation(activeFigureIndex);
  }
  scenarioState.active_figure_index = activeFigureIndex;

  scenarioState.aoe_grid = Array(AOE_SIZE).fill(false);
  const aoeGridCount = bitReader.readBits(AOE_SIZE_BITS);
  for (let i = 0; i < aoeGridCount; i += 1) {
    const index = bitReader.readBits(AOE_SIZE_BITS);
    validate(index, 0, AOE_SIZE - 1);
    if (AOE_GRID_SKIP_LIST.includes(index as (typeof AOE_GRID_SKIP_LIST)[number])) {
      throw BAD_SCENARIO_URL_ERROR;
    }
    scenarioState.aoe_grid[index] = true;
  }

  scenarioState.grid = Array(GRID_SIZE).fill(EMPTY) as ScenarioState['grid'];
  scenarioState.figures = Array(GRID_SIZE).fill(EMPTY) as ScenarioState['figures'];
  scenarioState.initiatives = Array(GRID_SIZE).fill(1) as ScenarioState['initiatives'];
  scenarioState.walls = Array(3 * GRID_SIZE).fill(false);

  let lastLocationRead = -1;
  const gridMappingSize = bitReader.readBits(gridSizeBits);
  for (let i = 0; i < gridMappingSize; i += 1) {
    let locationDelta: number;
    if (bitReader.readBits(1) === 0) {
      locationDelta = bitReader.readBits(2);
    }
    else {
      locationDelta = bitReader.readBits(gridSizeBits);
    }

    const locationRead = lastLocationRead + locationDelta + 1;
    validate(locationRead, 0, gridSize - 1);
    lastLocationRead = locationRead;
    const location = adjustLocation(locationRead);

    scenarioState.grid[location] = bitReader.readBits(3) as ScenarioState['grid'][number];
    validate(scenarioState.grid[location], FIRST_TERRAIN_BRUSH - 1, LAST_TERRAIN_BRUSH);

    scenarioState.figures[location] = bitReader.readBits(2) as ScenarioState['figures'][number];
    if (scenarioState.figures[location] !== EMPTY) {
      scenarioState.figures[location] = (scenarioState.figures[location] + FIRST_FIGURE_BRUSH - 1) as ScenarioState['figures'][number];
      validate(scenarioState.figures[location], FIRST_FIGURE_BRUSH, LAST_FIGURE_BRUSH);
      scenarioState.initiatives[location] = bitReader.readBits(4) as ScenarioState['initiatives'][number];
      validate(scenarioState.initiatives[location], 1, MAX_INITIATIVE);
    }

    if (bitReader.readBits(1)) {
      scenarioState.walls[3 * location + 0] = bitReader.readBits(1) === 1;
      scenarioState.walls[3 * location + 1] = bitReader.readBits(1) === 1;
      scenarioState.walls[3 * location + 2] = bitReader.readBits(1) === 1;
    }
  }

  const activeFactionBrush = scenarioState.active_faction ? CHARACTER : MONSTER;
  if (scenarioState.active_figure_index !== NULL_INDEX) {
    if (scenarioState.figures[scenarioState.active_figure_index] !== activeFactionBrush) {
      throw BAD_SCENARIO_URL_ERROR;
    }
  }

  return scenarioState;
}

export function encodeScenarioToToken(state: ScenarioState): string {
  return encodeScenarioToken(state);
}

export function encodeScenarioToUrl(state: ScenarioState): string {
  return `${location.origin}${URL_FOR.root}${encodeScenarioToken(state)}`;
}

export function decodeScenarioFromUrl(path: string): Partial<ScenarioState> | null {
  try {
    const token = extractScenarioToken(path);
    if (token === null) {
      return null;
    }

    return decodeScenarioToken(token);
  }
  catch (error) {
    if (error === BAD_SCENARIO_URL_ERROR || error instanceof TypeError) {
      return null;
    }
    throw error;
  }
}
