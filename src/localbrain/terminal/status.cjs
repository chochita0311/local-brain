'use strict';

// OSC 133 is explicit shell metadata, not a guess from output or process liveness.
// https://iterm2.com/documentation-escape-codes.html#shell-integrationfinalterm
function shellStatus() {
  const activity = {state: 'unknown', exitCode: null, completion: 0};
  let lastMarker = null;
  function accept(data) {
    if (data === 'A' || data === 'B') {
      activity.state = 'prompt';
      lastMarker = data;
    } else if (data === 'C') {
      activity.state = 'running';
      lastMarker = 'C';
    } else if (data === 'D' || /^D;\d{1,3}$/.test(data)) {
      const code = data === 'D' ? null : Number(data.slice(2));
      if (code !== null && code > 255) return false;
      if (lastMarker === 'C') {
        activity.state = 'finished';
        activity.exitCode = code;
        activity.completion++;
      } else if (lastMarker === 'B') {
        // An aborted command line is not a completed command.
        activity.state = 'prompt';
      } else return false;
      lastMarker = 'D';
    } else return false;
    return true;
  }
  return {activity, accept};
}

module.exports = {shellStatus};
