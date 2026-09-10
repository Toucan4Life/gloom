import React from 'react';
import * as C from './defines';
import HexUtils from './HexUtils';
import FigureTransform from './FigureTransform';

const FONT_SIZE = 0.5 * C.SCALE;

// Draws the numeric index of every hex, matching the hex numbers used
// elsewhere in the UI (and by the solver's explanation of its reasoning),
// so a hex mentioned by number can be located on the board.
const HexLabelGrid = React.memo( function( props ) {
  if ( !props.show ) {
    return null;
  }

  var labels = [];
  for ( var c = 0, index = 0; c < C.GRID_WIDTH; c++ ) {
    for ( var r = 0; r < C.GRID_HEIGHT; r++, index++ ) {
      const [ x, y ] = HexUtils.getGridHexCenter( c, r );
      labels.push(
        <FigureTransform key={index} rotate={props.rotate} x={x} y={y - 0.6 * C.SCALE}>
          <text
            className='hex-label'
            x={x}
            y={y - 0.6 * C.SCALE + 4.5}
            fontSize={FONT_SIZE}
            pointerEvents='none'
          >
            {index}
          </text>
        </FigureTransform>
      );
    }
  }
  return <React.Fragment>{labels}</React.Fragment>;
} );
export default HexLabelGrid;
