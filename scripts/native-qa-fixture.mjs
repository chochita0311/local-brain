// Launch only the opt-in Rust example against a new task-owned synthetic root.
import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {join} from 'node:path';
export function fixture(repository, runtime, edition = 'web', mode = '') {
  const executable = process.env.LOCALBRAIN_QA_EXECUTABLE || join(repository,'target/debug/examples/ui-state-fixture');
  if (!existsSync(executable)) throw new Error('Build the native fixture first: cargo build --locked -p localbrain-api --example ui-state-fixture');
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('LOCALBRAIN_')));
  Object.assign(env,{HOME:join(runtime,'home'),ZDOTDIR:join(runtime,'home'),SHELL:'/bin/sh',LOCALBRAIN_TERMINAL_LAUNCHER:'process'});
  if (mode === 'terminal') {
    env.LOCALBRAIN_TERMINAL_BUNDLE = process.env.LOCALBRAIN_TERMINAL_TEST_BUNDLE;
    env.LOCALBRAIN_TERMINAL_RUNTIME = join(env.LOCALBRAIN_TERMINAL_BUNDLE,'bin/localbrain-runtime');
  }
  return spawn(executable,[runtime,edition,mode],{cwd:repository,env,stdio:['ignore','ignore','pipe']});
}
