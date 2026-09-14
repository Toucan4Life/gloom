// Copies the pure-Python solver package (server/solver_api.py + server/solver/)
// into static/dist/py/ so it can be fetched by the browser and imported into
// Pyodide (WebAssembly Python) at runtime. This lets the site solve scenarios
// entirely client-side, with no backend required (needed for GitHub Pages).
const fs = require( 'fs' );
const path = require( 'path' );

const SERVER_DIR = path.join( __dirname, '..', '..', 'server' );
const DEST_DIR = path.join( __dirname, '..', 'dist', 'py' );

const FILES_TO_COPY = [
  'solver_api.py',
  path.join( 'solver', '__init__.py' ),
  path.join( 'solver', 'gloomhaven_map.py' ),
  path.join( 'solver', 'hexagonal_grid.py' ),
  path.join( 'solver', 'monster.py' ),
  path.join( 'solver', 'print_map.py' ),
  path.join( 'solver', 'rule.py' ),
  path.join( 'solver', 'settings.py' ),
  path.join( 'solver', 'solver.py' ),
  path.join( 'solver', 'utils.py' ),
];

for ( const relative_path of FILES_TO_COPY ) {
  const source_path = path.join( SERVER_DIR, relative_path );
  const dest_path = path.join( DEST_DIR, relative_path );
  fs.mkdirSync( path.dirname( dest_path ), { recursive: true } );
  fs.copyFileSync( source_path, dest_path );
}

console.log( `Copied ${FILES_TO_COPY.length} Python solver files to ${DEST_DIR}` );
