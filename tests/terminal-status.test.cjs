'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {shellStatus} = require('../src/localbrain/terminal/status.cjs');

test('a quiet live shell and ordinary output do not establish command state', () => {
  const status = shellStatus();
  assert.deepEqual(status.activity, {state: 'unknown', exitCode: null, completion: 0});
  for (const message of ['done', '', 'D;0', 'D', 'D;-1', 'D;256', 'D;0;extra', 'A;command=text']) status.accept(message);
  assert.deepEqual(status.activity, {state: 'unknown', exitCode: null, completion: 0});
});

test('reported execution and completion survive the following prompt without double counting', () => {
  const status = shellStatus();
  status.accept('A'); status.accept('B');
  assert.equal(status.activity.state, 'prompt');
  status.accept('C');
  assert.equal(status.activity.state, 'running');
  status.accept('D;7'); status.accept('D;0');
  assert.deepEqual(status.activity, {state: 'finished', exitCode: 7, completion: 1});
  status.accept('A'); status.accept('B');
  assert.deepEqual(status.activity, {state: 'prompt', exitCode: 7, completion: 1});
  status.accept('C'); status.accept('D;0');
  assert.deepEqual(status.activity, {state: 'finished', exitCode: 0, completion: 2});
});

test('aborted command line is not completion and omitted exit result stays unknown', () => {
  const status = shellStatus();
  status.accept('A'); status.accept('B'); status.accept('D;0');
  assert.deepEqual(status.activity, {state: 'prompt', exitCode: null, completion: 0});
  status.accept('C'); status.accept('D');
  assert.deepEqual(status.activity, {state: 'finished', exitCode: null, completion: 1});
  status.accept('C'); assert.equal(status.accept('D;999'), false);
  assert.equal(status.activity.state, 'running');
});

test('shell descriptions preserve missing signals, process exit and unseen versus seen completion', async () => {
  const {terminalStatus} = await import('../src/localbrain/static/terminal-state.js');
  const live = {state: 'running', activity: {state: 'unknown', completion: 0, exitCode: null}};
  assert.equal(terminalStatus(live).key, 'unknown');
  assert.equal(terminalStatus(live).icon, 'circle');
  assert.match(terminalStatus(live).label, /미확인/);
  const reported = {...live, activity: {state: 'prompt', completion: 2, exitCode: 0}};
  assert.equal(terminalStatus(reported, 1).key, 'done');
  assert.equal(terminalStatus(reported, 2).key, 'idle');
  assert.equal(terminalStatus(reported, 2).icon, 'circle');
  assert.equal(terminalStatus({...reported, activity: {...reported.activity, state: 'running'}}, 1).key, 'working');
  assert.equal(terminalStatus({...reported, state: 'exited', exitCode: 0}, 1).key, 'exited');
  assert.equal(terminalStatus({...reported, error: 'termination unconfirmed'}, 1).key, 'error');
  const missingResult = {...reported, activity: {...reported.activity, exitCode: null}};
  assert.equal(terminalStatus(missingResult, 1).label.includes('미확인'), true);
  assert.equal(terminalStatus(missingResult, 1).icon, 'circle');
  assert.equal(terminalStatus({...missingResult, activity:{...missingResult.activity,state:'finished'}}, 2).icon, 'circle');
});

test('program title frames stay independent of shell running and do not consume ordinary title text', async () => {
  const {programTitle, terminalStatus} = await import('../src/localbrain/static/terminal-state.js');
  const running = {state:'running',activity:{state:'running',completion:0}};
  const frames = ['⠋ Synthetic Agent', '⠙ Synthetic Agent', 'Synthetic Agent'];
  assert.deepEqual(frames.map(name=>programTitle(name)), [
    {indicator:'⠋',title:'Synthetic Agent'}, {indicator:'⠙',title:'Synthetic Agent'}, {indicator:'',title:'Synthetic Agent'}
  ]);
  for (const name of frames) assert.equal(terminalStatus({...running,name}).key, 'working');
  for (const name of ['ordinary title','title ⠋ in text','⠋joined title','']) assert.deepEqual(programTitle(name), {indicator:'',title:name});
});

test('unselected marks require reported prompt/running and aggregate mixed panes without inventing idle', async () => {
  const {terminalIndicator} = await import('../src/localbrain/static/terminal-state.js');
  const term = activity => ({state:'running',activity:{state:activity}});
  const unknown=term('unknown'), prompt=term('prompt'), running=term('running');
  assert.equal(terminalIndicator([unknown]).icon, null);
  assert.equal(terminalIndicator([prompt]).icon, 'view_ring');
  assert.equal(terminalIndicator([running]).icon, 'view_dot');
  assert.equal(terminalIndicator([prompt,prompt]).icon, 'view_ring');
  assert.equal(terminalIndicator([prompt,unknown]).icon, null);
  assert.equal(terminalIndicator([unknown,running,prompt]).icon, 'view_dot');
  assert.equal(terminalIndicator([{...running,state:'exited'},prompt]).icon, null);
  assert.equal(terminalIndicator([term('finished')]).icon, null);
  assert.equal(terminalIndicator([]).icon, null);
});

test('selection/hidden marks take precedence while program title activity remains independent', async () => {
  const {terminalIndicator,programTitle} = await import('../src/localbrain/static/terminal-state.js');
  for (const state of ['unknown','prompt','running','finished']) {
    const terms=[{state:'running',name:'⠋ Agent',activity:{state}}];
    assert.equal(terminalIndicator(terms,{current:true}).icon, 'check');
    assert.equal(terminalIndicator(terms,{hidden:true,current:true}).icon, 'view_diamond');
    assert.equal(programTitle(terms[0].name).indicator, '⠋');
  }
});

test('confirmed shell cleanup retires every exit code, preserving genuine faults', async () => {
  const {cleanShellExit} = await import('../src/localbrain/static/terminal-state.js');
  const exited = {state:'exited',exitCode:0};
  for (const exitCode of [0,7,null]) assert.equal(cleanShellExit({...exited,exitCode}), true);
  for (const change of [{state:'running'}, {closing:true}, {error:'unknown child'}, {inputError:'partial input'}]) {
    assert.equal(cleanShellExit({...exited,...change}), false);
  }
});

test('view order survives new/removed tabs without changing manager arrays', async () => {
  const {orderedTabs} = await import('../src/localbrain/static/terminal-state.js');
  const tabs = [{id:'a'},{id:'b'},{id:'new'}];
  assert.deepEqual(orderedTabs(tabs,['gone','b','a']).map(tab=>tab.id), ['b','a','new']);
  assert.deepEqual(tabs.map(tab=>tab.id), ['a','b','new']);
});

test('workspace membership keeps empty groups and different-root hidden tabs in view order', async () => {
  const {workspaceGroups} = await import('../src/localbrain/static/terminal-state.js');
  const tabs = [{id:'a', cwd:'/demo/a', terminals:['one']}, {id:'b', cwd:'/demo/a', hidden:true, terminals:['two']}, {id:'c', cwd:'/demo/b', terminals:['three']}];
  const workspaces = {items:[{id:'mixed', name:'Mixed', cwd:'', tabs:['c','a','b']}, {id:'empty', name:'Later', cwd:'/demo/a', tabs:[]}]};
  const groups = workspaceGroups(workspaces, tabs);
  assert.deepEqual(groups.map(group => [group.id, group.tabs.map(tab => tab.id)]), [['mixed',['a','b','c']],['empty',[]]]);
  assert.equal(groups[0].cwd, '');
});

test('a delayed list response cannot regress newer stream status within one generation', async () => {
  const {latestTerminal} = await import('../src/localbrain/static/terminal-state.js');
  const stream = {id:'one',seq:12,activity:{state:'running',completion:2}};
  const stale = {id:'one',seq:11,activity:{state:'prompt',completion:2}};
  assert.equal(latestTerminal(stream,stale), stream);
  const exit = {id:'one',seq:13,state:'exited'};
  assert.equal(latestTerminal(stream,exit), exit);
  assert.equal(latestTerminal(undefined,stale), stale);
});
