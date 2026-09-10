import React from 'react';

// Human friendly headings for each phase the solver reports steps for.
// These line up with the sections of the Gloomhaven AI flowchart
// (see GloomIA_Flowchart.png): Find Focus, Optimize Location To Attack
// Focus, Find Best Group / Optimize Location To Attack Best Group, and
// Get Closer.
const PHASE_LABELS = {
  focus: 'Find Focus',
  attack_location: 'Optimize Location to Attack Focus',
  group: 'Find Best Group',
  movement: 'Get Closer',
  result: 'Result',
};

function groupStepsByPhase( steps ) {
  var groups = [];
  steps.forEach( ( step ) => {
    var last_group = groups[groups.length - 1];
    if ( last_group && last_group.phase === step.phase ) {
      last_group.steps.push( step );
    }
    else {
      groups.push( { phase: step.phase, steps: [step] } );
    }
  } );
  return groups;
}

export default class ExplanationPanel extends React.PureComponent {
  render() {
    const steps = this.props.steps;
    if ( !steps || steps.length === 0 ) {
      return null;
    }

    const groups = groupStepsByPhase( steps );

    return (
      <div className='explanation-panel mt-2 mx-4 p-3 rounded'>
        <h6 className='mb-3'>
          How the solver reached this solution
        </h6>
        {groups.map( ( group, group_index ) => (
          <div key={group_index} className='mb-3'>
            <div className='explanation-phase-label text-uppercase small font-weight-bold mb-1'>
              {group_index + 1}. {PHASE_LABELS[group.phase] || group.phase}
            </div>
            <ol className='pl-4 mb-0'>
              {group.steps.map( ( step, step_index ) => (
                <li key={step_index} className='mb-2'>
                  <div className='explanation-step-title'>{step.title}</div>
                  <div className='explanation-step-detail small'>{step.detail}</div>
                </li>
              ) )}
            </ol>
          </div>
        ) )}
      </div>
    );
  }
}
