import React from 'react';
import HexUtils from './HexUtils';

const VIEW_OPTIONS = [
  [ 'story', 'Narrative' ],
  [ 'score', 'Scorecard' ],
  [ 'raw', 'Raw' ],
];

const MAX_STAGE_CANDIDATES = 10;


function formatStageValue( value ) {
  if ( Array.isArray( value ) ) {
    return value.map( ( item ) => formatStageValue( item ) ).join( ' / ' );
  }
  if ( value && typeof value === 'object' ) {
    return JSON.stringify( value );
  }
  return String( value );
}


function summarizeNumberList( values, emptyLabel ) {
  if ( !values || values.length === 0 ) {
    return emptyLabel;
  }
  return values.join( ', ' );
}


function formatHexCoordinate( location ) {
  return HexUtils.getGridCoordinateLabel( location );
}


function formatInitiativeLabel( location, initiatives ) {
  if ( typeof location !== 'number' || !initiatives || location < 0 || location >= initiatives.length ) {
    return null;
  }

  const initiative = initiatives[location];
  if ( initiative === undefined || initiative === null || initiative === 0 ) {
    return null;
  }

  return String( initiative );
}


function formatFigureLabel( location, initiatives ) {
  return formatInitiativeLabel( location, initiatives ) || formatHexCoordinate( location );
}


function formatLocationList( values, initiatives ) {
  if ( !values || values.length === 0 ) {
    return 'none';
  }
  return values.map( ( location ) => formatHexCoordinate( location ) ).join( ', ' );
}


function formatFigureList( values, initiatives ) {
  if ( !values || values.length === 0 ) {
    return 'none';
  }
  return values.map( ( location ) => formatFigureLabel( location, initiatives ) ).join( ', ' );
}


function compareStageValues( left, right ) {
  if ( Array.isArray( left ) && Array.isArray( right ) ) {
    const limit = Math.min( left.length, right.length );
    for ( let index = 0; index < limit; index++ ) {
      const comparison = compareStageValues( left[index], right[index] );
      if ( comparison !== 0 ) {
        return comparison;
      }
    }
    return left.length - right.length;
  }

  if ( typeof left === 'number' && typeof right === 'number' ) {
    return left - right;
  }

  if ( typeof left === 'string' && typeof right === 'string' ) {
    return left.localeCompare( right, undefined, { numeric: true } );
  }

  if ( typeof left === 'boolean' && typeof right === 'boolean' ) {
    return Number( left ) - Number( right );
  }

  return formatStageValue( left ).localeCompare( formatStageValue( right ), undefined, { numeric: true } );
}


function compareStageCandidates( left, right ) {
  const leftHasScore = left.score !== undefined;
  const rightHasScore = right.score !== undefined;
  if ( leftHasScore && rightHasScore ) {
    const scoreComparison = compareStageValues( left.score, right.score );
    if ( scoreComparison !== 0 ) {
      return scoreComparison;
    }
  }
  else if ( leftHasScore !== rightHasScore ) {
    return leftHasScore ? -1 : 1;
  }

  if ( left.selected !== right.selected ) {
    return left.selected ? -1 : 1;
  }

  return ( left.label || '' ).localeCompare( right.label || '', undefined, { numeric: true } );
}


function formatCandidateLabel( candidate, initiatives ) {
  if ( candidate.targets && candidate.locations ) {
    return 'Targets ' + formatFigureList( candidate.targets, initiatives ) + ' from ' + formatLocationList( candidate.locations, initiatives );
  }

  if ( candidate.targets && candidate.location !== undefined ) {
    return 'Targets ' + formatFigureList( candidate.targets, initiatives ) + ' from ' + formatHexCoordinate( candidate.location );
  }

  if ( candidate.focus !== undefined && candidate.location !== undefined ) {
    return 'Focus ' + formatFigureLabel( candidate.focus, initiatives ) + ' via ' + formatHexCoordinate( candidate.location );
  }

  if ( candidate.focus !== undefined ) {
    return 'Focus ' + formatFigureLabel( candidate.focus, initiatives );
  }

  if ( candidate.locations ) {
    return formatLocationList( candidate.locations, initiatives );
  }

  if ( candidate.location !== undefined ) {
    if ( typeof candidate.key === 'string' && candidate.key.indexOf( 'end-hex:' ) === 0 ) {
      return 'End on ' + formatHexCoordinate( candidate.location );
    }
    return formatHexCoordinate( candidate.location );
  }

  return candidate.label;
}


function prepareStage( stage, initiatives ) {
  const sortedCandidates = ( stage.candidates || [] )
    .map( ( candidate ) => Object.assign( {}, candidate, {
      label: formatCandidateLabel( candidate, initiatives ),
    } ) )
    .sort( compareStageCandidates );

  return Object.assign( {}, stage, {
    candidates: sortedCandidates.slice( 0, MAX_STAGE_CANDIDATES ),
    hidden_candidate_count: Math.max( 0, sortedCandidates.length - MAX_STAGE_CANDIDATES ),
  } );
}


function renderCandidateRow( title, candidates, selected, keyPrefix ) {
  if ( !candidates || candidates.length === 0 ) {
    return null;
  }

  return (
    <div className='mt-2'>
      <div className='small text-uppercase text-muted mb-1'>
        {title}
      </div>
      <div className='explain-chip-row'>
        {candidates.map( ( candidate, index ) => (
          <span
            key={keyPrefix + candidate.key + ':' + index}
            className={'explain-chip ' + ( selected ? 'explain-chip-kept' : 'explain-chip-removed' )}
          >
            {candidate.label}
            {candidate.score !== undefined ? (
              <span className='ml-1 explain-chip-score'>
                {formatStageValue( candidate.score )}
              </span>
            ) : null}
          </span>
        ) )}
      </div>
    </div>
  );
}


function StageNarrative( props ) {
  const survivors = props.stage.candidates.filter( ( candidate ) => candidate.selected );
  const eliminated = props.stage.candidates.filter( ( candidate ) => !candidate.selected );

  return (
    <div className='explain-stage'>
      <div className='d-flex justify-content-between align-items-start'>
        <div className='font-weight-bold'>
          {props.stage.title}
        </div>
        <span className='badge badge-dark explain-count'>
          {props.stage.after_count}/{props.stage.before_count}
        </span>
      </div>
      <div className='small text-muted mt-1'>
        {props.stage.summary || props.stage.description}
      </div>
      {props.stage.hidden_candidate_count > 0 ? (
        <div className='small explain-stage-limit'>
          Showing the 10 best candidates out of {props.stage.before_count}.
        </div>
      ) : null}
      {renderCandidateRow( 'Kept', survivors, true, props.keyPrefix )}
      {renderCandidateRow( 'Removed', eliminated, false, props.keyPrefix )}
    </div>
  );
}


function StageScorecard( props ) {
  return (
    <div className='explain-stage'>
      <div className='font-weight-bold mb-2'>
        {props.stage.title}
      </div>
      {props.stage.hidden_candidate_count > 0 ? (
        <div className='small explain-stage-limit'>
          Showing the 10 best candidates out of {props.stage.before_count}.
        </div>
      ) : null}
      <div className='table-responsive'>
        <table className='table table-sm explain-table mb-0'>
          <thead>
            <tr>
              <th scope='col'>Candidate</th>
              {props.stage.score_label ? <th scope='col'>Score</th> : null}
              <th scope='col'>Status</th>
            </tr>
          </thead>
          <tbody>
            {props.stage.candidates.map( ( candidate, index ) => (
              <tr key={props.keyPrefix + candidate.key + ':' + index}>
                <td>{candidate.label}</td>
                {props.stage.score_label ? <td>{candidate.score !== undefined ? formatStageValue( candidate.score ) : 'n/a'}</td> : null}
                <td>
                  <span className={'badge explain-status-pill ' + ( candidate.selected ? 'explain-status-kept' : 'explain-status-removed' )}>
                    {candidate.selected ? 'kept' : 'removed'}
                  </span>
                </td>
              </tr>
            ) )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


function renderStages( stages, explainView, keyPrefix, initiatives ) {
  if ( !stages || stages.length === 0 ) {
    return (
      <div className='small text-muted'>
        No trace data was recorded for this section.
      </div>
    );
  }

  return stages.map( ( stage, index ) => {
    const preparedStage = prepareStage( stage, initiatives );
    if ( explainView === 'score' ) {
      return <StageScorecard key={keyPrefix + index} stage={preparedStage} keyPrefix={keyPrefix + index + ':'}/>;
    }
    return <StageNarrative key={keyPrefix + index} stage={preparedStage} keyPrefix={keyPrefix + index + ':'}/>;
  } );
}


function ActionCard( props ) {
  const attacks = formatFigureList( props.action.attacks, props.initiatives );
  const focuses = formatFigureList( props.action.focuses, props.initiatives );
  const destinations = formatLocationList( props.action.destinations, props.initiatives );
  const pathCount = props.action.explain ? props.action.explain.path_count : 0;

  return (
    <button
      type='button'
      className={'btn btn-sm text-left explain-action-card' + ( props.active ? ' active' : '' )}
      onClick={() => { props.onSelect( props.index ); }}
    >
      <div className='font-weight-bold'>
        End on {formatHexCoordinate( props.action.move )}
      </div>
      <div className='small'>
        Targets: {attacks}
      </div>
      <div className='small'>
        Focuses: {focuses}
      </div>
      <div className='small'>
        Attack from: {destinations}
      </div>
      {pathCount > 0 ? (
        <div className='small text-muted mt-2'>
          {pathCount} internal path{pathCount === 1 ? '' : 's'}
          {props.action.explain.note ? ' - ' + props.action.explain.note : ''}
        </div>
      ) : null}
    </button>
  );
}


const ExplainPanel = React.memo( function( props ) {
  const hasSolution = props.displaySolution && props.showMovement && props.solutionActions;
  const hasSingleAction = hasSolution && props.solutionActions.length === 1;
  const sharedStages = props.sharedExplain && props.sharedExplain.shared_stages
    ? props.sharedExplain.shared_stages
    : [];
  const selectedAction = hasSolution
    ? ( hasSingleAction
      ? props.solutionActions[0]
      : ( !props.showingAllActions ? props.solutionActions[props.actionDisplayed] : null ) )
    : null;
  const selectedExplain = selectedAction && selectedAction.explain ? selectedAction.explain : null;

  const rawPayload = {
    shared_stages: sharedStages,
    showing_all_actions: props.showingAllActions,
    selected_action_index: hasSingleAction ? 0 : ( props.showingAllActions ? null : props.actionDisplayed ),
    selected_action: selectedAction,
    actions: props.solutionActions || [],
  };

  let body = null;
  if ( !props.showMovement ) {
    body = (
      <div className='small text-muted'>
        Turn on Show Movement to request a decision trace.
      </div>
    );
  }
  else if ( !hasSolution ) {
    body = (
      <div className='small text-muted'>
        Explain mode will populate as soon as the current solution finishes loading.
      </div>
    );
  }
  else if ( props.explainView === 'raw' ) {
    body = (
      <pre className='explain-raw mb-0'>
        {JSON.stringify( rawPayload, null, 2 )}
      </pre>
    );
  }
  else {
    body = (
      <React.Fragment>
        {props.solutionActions.length > 1 ? (
          <div className='mb-3'>
            <div className='explain-section-label'>Compare displayed actions</div>
            <div className='explain-action-grid'>
              {props.solutionActions.map( ( action, index ) => (
                <ActionCard
                  key={index}
                  index={index}
                  action={action}
                  initiatives={props.initiatives}
                  active={!props.showingAllActions && props.actionDisplayed === index}
                  onSelect={props.onSelectAction}
                />
              ) )}
            </div>
          </div>
        ) : null}

        {props.showingAllActions && props.solutionActions.length > 1 ? (
          <div className='alert alert-secondary explain-callout'>
            The shared stages below explain why multiple displayed actions still tie. Click any card above, or use the existing navigation buttons, to inspect one action-specific path.
          </div>
        ) : selectedExplain ? (
          <div className='alert alert-secondary explain-callout'>
            {selectedExplain.note}
          </div>
        ) : null}

        {sharedStages.length > 0 ? (
          <div className='mb-3'>
            <div className='explain-section-label'>Shared focus selection</div>
            {renderStages( sharedStages, props.explainView, 'shared:', props.initiatives )}
          </div>
        ) : null}

        {selectedExplain ? selectedExplain.paths.map( ( path, index ) => (
          <div className='mb-3' key={'path:' + index}>
            <div className='d-flex justify-content-between align-items-start'>
              <div>
                <div className='explain-section-label mb-1'>
                  Path {index + 1}
                </div>
                <div className='font-weight-bold'>
                  {'Focus ' + formatFigureLabel( path.focus, props.initiatives ) + ' from ' + formatHexCoordinate( path.attack_location )}
                </div>
                <div className='small text-muted'>
                  Targets {formatFigureList( path.targets, props.initiatives )}
                </div>
              </div>
              <span className='badge badge-info'>
                {path.move_options.length} tied end hex{path.move_options.length === 1 ? '' : 'es'}
              </span>
            </div>
            <div className='mt-2'>
              {renderStages( path.stages, props.explainView, 'path:' + index + ':', props.initiatives )}
            </div>
          </div>
        ) ) : (
          <div className='small text-muted'>
            Select a single action to inspect its path-specific stages.
          </div>
        )}
      </React.Fragment>
    );
  }

  return (
    <div className='card border-secondary explain-panel'>
      <div className='card-body'>
        <div className='d-flex justify-content-between align-items-start mb-3'>
          <div>
            <div className='h6 mb-1'>Why this move?</div>
            <div className='small text-muted'>
              Compare tied actions, read the rule trace, or inspect the raw payload.
            </div>
          </div>
          <div className='btn-group btn-group-sm explain-mode-group'>
            {VIEW_OPTIONS.map( ( view ) => (
              <button
                key={view[0]}
                type='button'
                className={'btn btn-dark' + ( props.explainView === view[0] ? ' active' : '' )}
                onClick={() => { props.onViewChange( view[0] ); }}
              >
                {view[1]}
              </button>
            ) )}
          </div>
        </div>

        {!props.showingAllActions && props.solutionActions && props.solutionActions.length > 1 ? (
          <div className='mb-3'>
            <button
              type='button'
              className='btn btn-sm btn-outline-light'
              onClick={() => { props.onSelectAction( -1 ); }}
            >
              Back To All Displayed Actions
            </button>
          </div>
        ) : null}

        {body}
      </div>
    </div>
  );
} );


export default ExplainPanel;