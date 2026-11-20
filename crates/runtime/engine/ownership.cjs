'use strict';

function sameProcess(now, before) {
  return Boolean(now && !now.dead && now.pid === before.pid && now.born === before.born
    && now.group === before.group && now.session === before.session
    && (before.ownerParent === undefined || now.parent === before.ownerParent));
}

// null means ownership cannot be proved; an empty array means no owned work remains.
function ownedProcesses(owner, known, lost, table) {
  if (!owner) return null;
  if (!owner.born) {
    return table.some(item => item.pid === owner.pid || (!item.dead && item.session === owner.pid)) ? null : [];
  }
  const root = table.find(item => item.pid === owner.pid);
  if (root && (!sameProcess({...root, dead: false}, owner) || root.parent !== owner.parent)) return null;
  const anchored = known.some(before => sameProcess(table.find(now => now.pid === before.pid), before));
  if (lost && !root && !anchored) {
    return table.some(item => !item.dead && item.session === owner.pid) ? null : [];
  }
  const ids = new Set([owner.pid]);
  let size;
  do {
    size = ids.size;
    for (const item of table) if (ids.has(item.parent)) ids.add(item.pid);
  } while (size !== ids.size);
  return table.filter(item => !item.dead && (ids.has(item.pid) || item.session === owner.pid))
    .map(item => item.pid === owner.pid ? {...item, ownerParent: owner.parent} : item);
}

function signalTargets(records, table) {
  const current = new Map(table.map(item => [item.pid, item]));
  return records.filter(item => sameProcess(current.get(item.pid), item));
}

module.exports = {sameProcess, ownedProcesses, signalTargets};
