import assert from "node:assert/strict";
import test from "node:test";

import {
  buildWorkflowLayout,
  clampWorkflowZoom,
  consumeWorkflowRestorationSnapshot,
  sanitizeWorkflowRestorationSnapshot,
  storeWorkflowRestorationSnapshot,
  workflowAnchoredScroll,
  workflowPath,
  workflowWheelOwnsZoom,
  workflowZoomFromWheel,
} from "../src/localbrain/static/workflow-map.js";


const payload = {
  status: "ready",
  selected_episode_key: "episode-c",
  episodes: [
    { episode_key: "episode-d", session_id: 4, title: "Branch", last_observed_at: "2026-09-14T04:00:00Z", workflow_destination: "/sessions/4/workflow" },
    { episode_key: "episode-b", session_id: 2, title: "Middle", last_observed_at: "2026-09-14T02:00:00Z", workflow_destination: "/sessions/2/workflow" },
    { episode_key: "episode-e", session_id: 5, title: "Branch next", last_observed_at: "2026-09-14T05:00:00Z", workflow_destination: "/sessions/5/workflow" },
    { episode_key: "episode-a", session_id: 1, title: "Start", last_observed_at: "2026-09-14T01:00:00Z", workflow_destination: "/sessions/1/workflow" },
    { episode_key: "episode-c", session_id: 3, title: "Main next", last_observed_at: "2026-09-14T03:00:00Z", workflow_destination: "/sessions/3/workflow" },
  ],
  relations: [
    { relation_id: "relation-1", source_episode_key: "episode-a", target_episode_key: "episode-b", kind: "continues", label: "continues", authority_label: "규칙 기반 후보" },
    { relation_id: "relation-2", source_episode_key: "episode-b", target_episode_key: "episode-c", kind: "continues", label: "continues", authority_label: "규칙 기반 후보" },
    { relation_id: "relation-3", source_episode_key: "episode-b", target_episode_key: "episode-d", kind: "branches-from", label: "branches from", authority_label: "규칙 기반 후보" },
    { relation_id: "relation-4", source_episode_key: "episode-d", target_episode_key: "episode-e", kind: "continues", label: "continues", authority_label: "규칙 기반 후보" },
  ],
};

const geometry = {
  nodeWidth: 200,
  nodeHeight: 100,
  columnGap: 50,
  laneGap: 30,
  stagePadding: 20,
  axisSize: 20,
};

test("fixed workflow layout is repeatable and branches use a stable lane", () => {
  const first = buildWorkflowLayout(payload, "wide", geometry);
  const second = buildWorkflowLayout(payload, "wide", geometry);
  assert.deepEqual(first, second);
  assert.deepEqual(
    first.episodes.map((episode) => episode.episode_key),
    ["episode-a", "episode-b", "episode-c", "episode-d", "episode-e"],
  );
  const byKey = Object.fromEntries(
    first.episodes.map((episode) => [episode.episode_key, episode]),
  );
  assert.equal(byKey["episode-a"].lane, byKey["episode-c"].lane);
  assert.notEqual(byKey["episode-c"].lane, byKey["episode-d"].lane);
  assert.equal(byKey["episode-e"].branchOwner, "episode-d");
  assert.deepEqual(first.branchGroups["episode-d"], ["episode-e"]);
  assert.ok(byKey["episode-a"].x < byKey["episode-e"].x);
});

test("compact layout preserves topology while time becomes vertical", () => {
  const wide = buildWorkflowLayout(payload, "wide", geometry);
  const compact = buildWorkflowLayout(payload, "compact", geometry);
  assert.deepEqual(
    compact.relations.map((relation) => relation.kind),
    wide.relations.map((relation) => relation.kind),
  );
  assert.ok(compact.episodes[0].y < compact.episodes.at(-1).y);
  assert.equal(compact.episodes[0].x, compact.episodes[2].x);
  assert.notEqual(compact.episodes[2].x, compact.episodes[3].x);
});

test("focus path illuminates ancestry and own descendants but not sibling branch", () => {
  const mainLeaf = workflowPath(payload, "episode-c");
  assert.deepEqual(mainLeaf.episodeKeys, ["episode-a", "episode-b", "episode-c"]);
  assert.deepEqual(mainLeaf.relationIds, ["relation-1", "relation-2"]);

  const fork = workflowPath(payload, "episode-b");
  assert.deepEqual(
    fork.episodeKeys,
    ["episode-a", "episode-b", "episode-c", "episode-d", "episode-e"],
  );
  assert.deepEqual(
    fork.relationIds,
    ["relation-1", "relation-2", "relation-3", "relation-4"],
  );
});

test("zoom is bounded, pointer anchored, and ordinary wheel is not owned", () => {
  assert.equal(clampWorkflowZoom(-10), 0.55);
  assert.equal(clampWorkflowZoom(10), 1.8);
  assert.equal(clampWorkflowZoom(Number.NaN), 1);
  assert.ok(workflowZoomFromWheel(1, -100) > 1);
  assert.ok(workflowZoomFromWheel(1, 100) < 1);
  assert.equal(workflowAnchoredScroll(100, 50, 1, 2), 250);
  assert.equal(workflowWheelOwnsZoom({ ctrlKey: false, metaKey: false }), false);
  assert.equal(workflowWheelOwnsZoom({ ctrlKey: true, metaKey: false }), true);
  assert.equal(workflowWheelOwnsZoom({ ctrlKey: false, metaKey: true }), true);
});

test("malformed projections fail closed for the textual fallback", () => {
  assert.throws(
    () => buildWorkflowLayout({ ...payload, selected_episode_key: "absent" }),
    /Selected Workflow Episode is absent/,
  );
  assert.throws(
    () => buildWorkflowLayout({ ...payload, relations: [{ ...payload.relations[0], target_episode_key: "absent" }] }),
    /Invalid Workflow relation/,
  );
});

test("correction restoration is bounded, one-shot, and omits content fields", () => {
  const episodeKey = `session:${"a".repeat(64)}`;
  const relationId = `workflow-relation-${"b".repeat(64)}`;
  const now = 1_800_000_000_000;
  const candidate = {
    version: "localbrain.workflow-correction-restore.v1",
    pathname: "/sessions/11/workflow",
    createdAt: now,
    selectedEpisodeKey: episodeKey,
    expandedBranchKeys: [episodeKey, episodeKey, "not-an-episode"],
    scale: 99,
    viewportScrollLeft: -20,
    viewportScrollTop: 240,
    traceScrollTop: 80,
    outerScrollX: 10,
    outerScrollY: 360,
    openDisclosureKeys: [
      `evidence:${episodeKey}:atlassian`,
      "evidence:invalid:private",
    ],
    focusKind: "relation",
    focusKey: relationId,
    resultCode: "workflow-corrected",
    title: "must not persist",
    note: "must not persist",
    evidence: { body: "must not persist" },
  };
  const clean = sanitizeWorkflowRestorationSnapshot(
    candidate, candidate.pathname, now,
  );
  assert.equal(clean.scale, 1.8);
  assert.equal(clean.viewportScrollLeft, 0);
  assert.deepEqual(clean.expandedBranchKeys, [episodeKey]);
  assert.deepEqual(clean.openDisclosureKeys, [`evidence:${episodeKey}:atlassian`]);
  assert.equal(Object.hasOwn(clean, "title"), false);
  assert.equal(Object.hasOwn(clean, "note"), false);
  assert.equal(Object.hasOwn(clean, "evidence"), false);

  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
  assert.equal(storeWorkflowRestorationSnapshot(storage, candidate), true);
  assert.deepEqual(
    consumeWorkflowRestorationSnapshot(storage, candidate.pathname, now),
    clean,
  );
  assert.equal(
    consumeWorkflowRestorationSnapshot(storage, candidate.pathname, now),
    null,
  );
});

test("restoration rejects another path, expired state, and invalid boundary focus", () => {
  const episodeKey = `session:${"a".repeat(64)}`;
  const base = {
    version: "localbrain.workflow-correction-restore.v1",
    pathname: "/sessions/11/workflow",
    createdAt: 10_000,
    selectedEpisodeKey: episodeKey,
    expandedBranchKeys: [],
    scale: 1,
    viewportScrollLeft: 0,
    viewportScrollTop: 0,
    traceScrollTop: 0,
    outerScrollX: 0,
    outerScrollY: 0,
    openDisclosureKeys: [],
    focusKind: "lifecycle",
    focusKey: episodeKey,
    resultCode: "workflow-undone",
  };
  assert.equal(
    sanitizeWorkflowRestorationSnapshot(base, "/sessions/12/workflow", 10_000),
    null,
  );
  assert.equal(
    sanitizeWorkflowRestorationSnapshot(base, base.pathname, 10_000 + 120_001),
    null,
  );
  assert.equal(
    sanitizeWorkflowRestorationSnapshot(
      { ...base, focusKey: "private-path" }, base.pathname, 10_000,
    ),
    null,
  );
});
