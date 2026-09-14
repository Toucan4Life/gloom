// Runs the Gloomhaven solver (server/solver_api.py + server/solver/) entirely
// in the browser via Pyodide (Python compiled to WebAssembly). This lets the
// app solve scenarios with no backend server at all, which is required for a
// static host like GitHub Pages, while reusing the exact same Python logic
// that previously ran behind the Flask /solve and /views endpoints.

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
];

let pyodide_promise = null;

function loadPyodideRuntime() {
  return new Promise( ( resolve, reject ) => {
    if ( window.loadPyodide ) {
      resolve();
      return;
    }
    const script = document.createElement( 'script' );
    script.src = PYODIDE_CDN + 'pyodide.js';
    script.onload = resolve;
    script.onerror = () => reject( new Error( 'Failed to load the Pyodide runtime' ) );
    document.head.appendChild( script );
  } );
}

async function initPyodide() {
  await loadPyodideRuntime();
  const pyodide = await window.loadPyodide( { indexURL: PYODIDE_CDN } );

  const py_source_base = window.PY_SOURCE_BASE || 'py/';
  pyodide.FS.mkdirTree( `${PY_MODULE_DIR}/solver` );
  await Promise.all( PY_FILES.map( async ( relative_path ) => {
    const response = await fetch( py_source_base + relative_path );
    if ( !response.ok ) {
      throw new Error( `Failed to fetch solver source file: ${relative_path}` );
    }
    const source = await response.text();
    pyodide.FS.writeFile( `${PY_MODULE_DIR}/${relative_path}`, source );
  } ) );

  pyodide.runPython( `
import sys
if '${PY_MODULE_DIR}' not in sys.path:
    sys.path.insert( 0, '${PY_MODULE_DIR}' )
import solver_api
` );

  return pyodide;
}

function getPyodide() {
  if ( !pyodide_promise ) {
    pyodide_promise = initPyodide();
  }
  return pyodide_promise;
}

async function callSolverFunction( function_name, payload ) {
  const pyodide = await getPyodide();
  pyodide.globals.set( '_payload_json', JSON.stringify( payload ) );
  try {
    const result_json = pyodide.runPython( `
import solver_api, json
json.dumps( solver_api.${function_name}( _payload_json.encode() ) )
` );
    return JSON.parse( result_json );
  }
  catch ( error ) {
    const message = ( error && error.message ) || String( error );
    if ( message.includes( 'InvalidScenarioError' ) ) {
      throw new Error( 'invalid scenario payload' );
    }
    throw error;
  }
}

// Mirrors the response shape previously returned by `axios.put(URL_FOR.solve, scenario)`.
export function solveScenario( scenario ) {
  return callSolverFunction( 'solve_scenario', scenario );
}

// Mirrors the response shape previously returned by `axios.put(URL_FOR.views, views_request)`.
export function solveViews( views_request ) {
  return callSolverFunction( 'solve_views', views_request );
}
