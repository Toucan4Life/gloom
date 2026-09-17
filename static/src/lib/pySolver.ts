import type {
  SolverScenarioRequest,
  SolverScenarioResponse,
  SolverViewsRequest,
  SolverViewsResponse,
} from './solverTypes';

const PYODIDE_VERSION = 'v0.26.4';
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`;
const PY_MODULE_DIR = '/pysolver';

const PY_FILES = [
  'solver_api.py',
  'solver/__init__.py',
  'solver/gloomhaven_map.py',
  'solver/hexagonal_grid.py',
  'solver/monster.py',
  'solver/print_map.py',
  'solver/rule.py',
  'solver/settings.py',
  'solver/solver.py',
  'solver/utils.py',
] as const;

interface PyodideFs {
  mkdirTree(path: string): void;
  writeFile(path: string, data: string): void;
}

interface PyodideGlobals {
  set(name: string, value: unknown): void;
}

interface PyodideInstance {
  FS: PyodideFs;
  globals: PyodideGlobals;
  runPython(code: string): unknown;
}

type LoadPyodide = (options: { indexURL: string }) => Promise<PyodideInstance>;

declare global {
  interface Window {
    loadPyodide?: LoadPyodide;
  }
}

let pyodidePromise: Promise<PyodideInstance> | null = null;

function loadPyodideRuntime(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.loadPyodide) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = `${PYODIDE_CDN}pyodide.js`;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load the Pyodide runtime'));
    document.head.appendChild(script);
  });
}

async function initPyodide(): Promise<PyodideInstance> {
  await loadPyodideRuntime();

  if (!window.loadPyodide) {
    throw new Error('Failed to load the Pyodide runtime');
  }

  const pyodide = await window.loadPyodide({ indexURL: PYODIDE_CDN });
  const pySourceBase = globalThis.PY_SOURCE_BASE || 'py/';

  pyodide.FS.mkdirTree(`${PY_MODULE_DIR}/solver`);
  await Promise.all(
    PY_FILES.map(async (relativePath) => {
      const response = await fetch(`${pySourceBase}${relativePath}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch solver source file: ${relativePath}`);
      }

      const source = await response.text();
      pyodide.FS.writeFile(`${PY_MODULE_DIR}/${relativePath}`, source);
    }),
  );

  pyodide.runPython(`
import sys
if '${PY_MODULE_DIR}' not in sys.path:
    sys.path.insert(0, '${PY_MODULE_DIR}')
import solver_api
`);

  return pyodide;
}

function getPyodide(): Promise<PyodideInstance> {
  if (!pyodidePromise) {
    pyodidePromise = initPyodide();
  }

  return pyodidePromise;
}

async function callSolverFunction<TResponse>(
  functionName: 'solve_scenario' | 'solve_views',
  payload: SolverScenarioRequest | SolverViewsRequest,
): Promise<TResponse> {
  const pyodide = await getPyodide();
  pyodide.globals.set('_payload_json', JSON.stringify(payload));

  try {
    const resultJson = pyodide.runPython(`
import json, solver_api
json.dumps(solver_api.${functionName}(_payload_json.encode()))
`);

    if (typeof resultJson !== 'string') {
      throw new Error('Solver returned a non-JSON result');
    }

    return JSON.parse(resultJson) as TResponse;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes('InvalidScenarioError')) {
      throw new Error('invalid scenario payload');
    }

    throw error;
  }
}

export function solveScenario(scenario: SolverScenarioRequest): Promise<SolverScenarioResponse> {
  return callSolverFunction<SolverScenarioResponse>('solve_scenario', scenario);
}

export function solveViews(viewsRequest: SolverViewsRequest): Promise<SolverViewsResponse> {
  return callSolverFunction<SolverViewsResponse>('solve_views', viewsRequest);
}
