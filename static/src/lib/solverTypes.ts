import type { GameRulesValue, ZeroToNine, ZeroToSix, ZeroToTwo, BooleanBit } from './scenarioState';

export type SolverViewLevel = 0 | 1 | 2;
export type ThinWallDirection = 0 | 1 | 2;
export type ThinWall = [location: number, direction: ThinWallDirection];
export type SolverLocation = number;
export type SolverPoint = [x: number, y: number];
export type SolverSightLine = [start: SolverPoint, end: SolverPoint];
export type SolverDebugVisual = [classIndex: number, points: [SolverPoint, SolverPoint] | [SolverPoint]];
export type SolverLocationRange = [start: number, end: number];
export type SolverViewData = SolverLocationRange[];
export type SolverViewCollection = SolverViewData[];

export interface SolverScenarioMap {
  characters: SolverLocation[];
  monsters: SolverLocation[];
  walls: SolverLocation[];
  obstacles: SolverLocation[];
  traps: SolverLocation[];
  hazardous: SolverLocation[];
  difficult: SolverLocation[];
  icy: SolverLocation[];
  thin_walls: ThinWall[];
  initiatives: number[];
}

export interface SolverScenarioRequest {
  scenario_id: number;
  solve_view: SolverViewLevel;
  active_figure: number;
  move: ZeroToNine;
  range: ZeroToNine;
  target: ZeroToSix;
  flying: ZeroToTwo;
  teleport: BooleanBit;
  muddled: BooleanBit;
  game_rules: GameRulesValue;
  aoe: number[];
  width: number;
  height: number;
  map: SolverScenarioMap;
}

export interface SolverViewsMap {
  walls: SolverLocation[];
  thin_walls: ThinWall[];
}

export interface SolverViewsRequest {
  scenario_id: number;
  solve_view: SolverViewLevel;
  range: ZeroToNine;
  target: ZeroToSix;
  game_rules: GameRulesValue;
  width: number;
  height: number;
  map: SolverViewsMap;
  viewpoints: SolverLocation[];
}

export interface SolverExplanationStep {
  phase: string;
  title: string;
  detail: string;
  focus: number | null;
  locations: SolverLocation[];
}

export interface SolverAction {
  move: SolverLocation;
  attacks: SolverLocation[];
  aoe: SolverLocation[];
  destinations: SolverLocation[];
  focuses: SolverLocation[];
  sightlines: SolverSightLine[];
  debug_lines?: SolverDebugVisual[];
}

export interface SolverScenarioResponse {
  scenario_id: number;
  actions: SolverAction[];
  explanation: SolverExplanationStep[];
  reach?: SolverViewCollection;
  sight?: SolverViewCollection;
}

export interface SolverViewsResponse {
  scenario_id: number;
  reach?: SolverViewCollection;
  sight?: SolverViewCollection;
}
