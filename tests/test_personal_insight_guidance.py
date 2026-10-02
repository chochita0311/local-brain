import copy
from hashlib import sha256
import unittest

from localbrain.personal_insight_evidence import MANIFEST_VERSION
from localbrain.personal_insight_guidance import (
    CORE_VERSION,
    GUIDE_ROOT,
    PLAYBOOK_IDS,
    PLAYBOOK_VERSIONS,
    LEGACY_REPORT_VERSION,
    REPORT_VERSION,
    build_guide_bundle,
    guide_text,
    result_schema,
    validate_guided_result,
)


def manifest(question=None, excerpts=("Please explain this term", "Why did this happen")):
    mode = "ask" if question is not None else "discover"
    return {
        "version": MANIFEST_VERSION,
        "scope": {"mode": mode, "question": question},
        "sessions": [
            {
                "session_id": index,
                "message_count": 3,
                "events": [{
                    "source_key": "codex-company",
                    "event_id": f"event-{index}",
                    "role": "user",
                    "message_index": 1,
                    "text_length": len(excerpt),
                    "excerpt_start": 0,
                    "excerpt_end": len(excerpt),
                    "excerpt": excerpt,
                }],
            }
            for index, excerpt in enumerate(excerpts, 1)
        ],
    }


def valid_finding(type_id, evidence_ids):
    return {
        "title": "설명을 이해하기 쉽게 요청하는 방법",
        "type_id": type_id,
        "type_reason": "설명 내용을 실제로 이해하려는 목표와 재질문을 기준으로 선택했다.",
        "owner_goal": "새 개념을 이해하기",
        "pattern_scope": "recurring_pattern",
        "observation": "두 세션에서 설명을 다시 요청했다.",
        "evidence_ids": evidence_ids,
        "counterevidence_ids": [],
        "counterexample_status": "not_observed",
        "counterexample_check": "다른 세션에서 설명 없이 적용한 사례가 있는지 살펴봤다.",
        "alternative": "새 개념을 탐구하는 정상적인 학습일 수 있다.",
        "coverage_limit": "표본에는 전체 대화와 학습 결과가 없다.",
        "action": "다음에는 짧은 예시를 먼저 요청해 본다.",
        "benefit_hypothesis": "개념을 적용하기 쉬워질 수 있다.",
        "effort_or_tradeoff": "설명에 몇 문장이 더 필요하다.",
        "follow_up": "새 예시에 스스로 적용할 수 있는지 확인한다.",
        "handoff": {
            "goal": "새 개념 이해",
            "proposed_change": "작은 예시로 설명 요청",
            "scope": "다음 학습 세션 하나",
            "constraints": "정확한 출처를 유지",
            "first_steps": "질문에 예시 요청을 추가",
            "success_check": "다른 예시에 적용 여부 확인",
        },
        "outcome_state": "not_confirmed",
    }


def valid_result(finding):
    return {
        "result_version": REPORT_VERSION,
        "title": "학습 방식 점검",
        "summary": "두 세션의 질문을 검토했다.",
        "selection_reason": "두 학습 질문을 후보로 살펴보되 정상적인 탐구일 가능성도 검토했다.",
        "selection_evidence_ids": ["codex-company:event-1"],
        "outcome": "findings",
        "findings": [finding],
        "no_finding_reason": "",
        "additional_evidence": {"kind": "none", "question": "", "evidence_ids": [], "message_requests": []},
        "limits": "표본으로 실제 학습 성과를 확인할 수 없다.",
    }


class PersonalInsightGuidanceTests(unittest.TestCase):
    def test_all_versioned_resources_are_available_without_keyword_exclusion(self):
        self.assertEqual(len(PLAYBOOK_IDS), 11)
        for playbook_id in PLAYBOOK_IDS:
            version = PLAYBOOK_VERSIONS[playbook_id]
            content = (GUIDE_ROOT / "playbooks" / f"{playbook_id}-{version}.md").read_text()
            for field in (
                "Trigger", "Exclude", "Evidence questions", "Benign alternative",
                "Intervention", "Output sketch", "Follow-up", "Current-source limit",
            ):
                self.assertIn(field, content, (playbook_id, field))
        for source in (
            manifest(question="내 글을 더 쉽게 이해하게 하려면?"),
            manifest(excerpts=("확인 메일, 설정 메뉴, 검색 접근 — 면담 주제",)),
            manifest(excerpts=("hello",)),
        ):
            bundle = build_guide_bundle(source)
            self.assertEqual(bundle["core_version"], CORE_VERSION)
            self.assertEqual(bundle["report_version"], REPORT_VERSION)
            self.assertEqual([item["id"] for item in bundle["playbooks"]], list(PLAYBOOK_IDS))
            self.assertEqual(bundle["route_reason"], "owner_goal_and_observed_friction")
            self.assertEqual(len(bundle["core_sha256"]), 64)
            self.assertIn("answer the person's actual question first", guide_text(bundle))
        self.assertEqual(PLAYBOOK_VERSIONS["request_feedback"], "v4")

    def test_invalid_scope_is_still_rejected(self):
        for change in ({"mode": "other"}, {"mode": "ask", "question": ""},
                       {"mode": "discover", "question": "unexpected"}):
            source = manifest()
            source["scope"].update(change)
            with self.assertRaises(ValueError):
                build_guide_bundle(source)

    def test_valid_finding_has_stable_identity_and_provenance(self):
        source = manifest(question="왜 같은 개념을 다시 물어보지?")
        bundle = build_guide_bundle(source)
        selected = [item["id"] for item in bundle["playbooks"]]
        schema = result_schema(selected)
        self.assertFalse(schema["additionalProperties"])
        result = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        accepted = validate_guided_result(result, source, bundle)
        self.assertEqual(accepted, validate_guided_result(result, source, bundle))
        self.assertEqual(len(accepted["findings"][0]["finding_id"]), 16)
        self.assertEqual(accepted["guide"]["core_version"], CORE_VERSION)
        self.assertEqual(
            [item["id"] for item in accepted["guide"]["playbooks"]], selected
        )

    def test_no_finding_and_bounded_additional_evidence(self):
        source = manifest()
        bundle = build_guide_bundle(source)
        result = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        result["outcome"] = "no_actionable_finding"
        result["findings"] = []
        result["no_finding_reason"] = "표본만으로 개선을 제안할 수 없다."
        self.assertEqual(validate_guided_result(result, source, bundle)["findings"], [])

        result["outcome"] = "needs_evidence"
        result["additional_evidence"] = {
            "kind": "conversation_neighbors",
            "question": "해당 질문 앞뒤 맥락을 확인할 수 있나요?",
            "evidence_ids": ["codex-company:event-1"],
            "message_requests": [{"anchor_evidence_id": "codex-company:event-1", "message_index": 0}],
        }
        self.assertEqual(
            validate_guided_result(result, source, bundle)["outcome"], "needs_evidence"
        )

    def test_ambiguous_volume_signal_can_end_without_a_change(self):
        source = manifest(excerpts=(
            "This session used many tokens.",
            "The discussion took a long time.",
        ))
        bundle = build_guide_bundle(source)
        result = valid_result(valid_finding(
            bundle["playbooks"][0]["id"],
            ["codex-company:event-1", "codex-company:event-2"],
        ))
        result.update(
            outcome="no_actionable_finding",
            findings=[],
            no_finding_reason="사용량과 길이만으로 개선할 문제를 판단할 수 없다.",
        )
        accepted = validate_guided_result(result, source, bundle)
        self.assertEqual(accepted["findings"], [])
        self.assertIn("Counts, tokens, price, and Session length alone", bundle["core"])

    def test_additional_evidence_citation_limit_is_visible_and_enforced(self):
        source = manifest(excerpts=tuple(f"Explain example {index}" for index in range(6)))
        bundle = build_guide_bundle(source)
        refs = [f"codex-company:event-{index}" for index in range(1, 7)]
        result = valid_result(valid_finding("learning_explanation", refs[:2]))
        result.update(outcome="needs_evidence", findings=[], no_finding_reason="현재 결과를 확인할 수 없다.")
        result["additional_evidence"] = {
            "kind": "outcome",
            "question": "선택한 질문의 현재 결과를 확인할 수 있나요?",
            "evidence_ids": refs,
            "message_requests": [],
        }
        with self.assertRaises(ValueError):
            validate_guided_result(result, source, bundle)
        result["additional_evidence"]["evidence_ids"] = refs[:5]
        accepted = validate_guided_result(result, source, bundle)
        self.assertEqual(len(accepted["additional_evidence"]["evidence_ids"]), 5)
        self.assertIn("at most five unique admitted IDs", guide_text(bundle))

    def test_invalid_claims_and_shapes_are_rejected(self):
        source = manifest(question="왜 같은 개념을 다시 물어보지?")
        bundle = build_guide_bundle(source)
        base = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        changes = [
            lambda result: result.update(extra="unknown"),
            lambda result: result["findings"][0].update(type_id="unknown_type"),
            lambda result: result["findings"][0].update(evidence_ids=["codex-company:unknown"]),
            lambda result: result["findings"][0].update(evidence_ids=["codex-company:event-1"]),
            lambda result: result["findings"][0].update(outcome_state="confirmed"),
            lambda result: result["findings"][0].update(title="x" * 161),
            lambda result: result.update(findings=result["findings"] * 4),
            lambda result: result.update(outcome="needs_evidence"),
            lambda result: result["findings"][0].update(counterexample_status="observed"),
            lambda result: result["findings"][0].update(
                counterexample_status="observed",
                counterevidence_ids=["codex-company:event-1"],
            ),
        ]
        for change in changes:
            candidate = copy.deepcopy(base)
            change(candidate)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_guided_result(candidate, source, bundle)

    def test_single_observation_is_valid_only_as_an_explicit_scope(self):
        source = manifest(question="왜 같은 개념을 다시 물어보지?")
        bundle = build_guide_bundle(source)
        result = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1"]
        ))
        result["findings"][0]["pattern_scope"] = "single_observation"
        accepted = validate_guided_result(result, source, bundle)
        self.assertEqual(accepted["findings"][0]["pattern_scope"], "single_observation")
        self.assertIn("One ambiguous phrase cannot justify", bundle["core"])

    def test_conversation_request_rejects_supplied_or_invalid_targets(self):
        source = manifest()
        bundle = build_guide_bundle(source)
        value = valid_result(valid_finding("request_feedback", ["codex-company:event-1"]))
        value.update(outcome="needs_evidence", findings=[], no_finding_reason="원래 답변이 빠져 있다.")
        ref = "codex-company:event-1"
        value["additional_evidence"] = {
            "kind": "conversation_neighbors", "question": "처음 답변이 무엇이었는지 확인한다.",
            "evidence_ids": [ref], "message_requests": [{"anchor_evidence_id": ref, "message_index": 0}],
        }
        validate_guided_result(value, source, bundle)
        for index in (1, -1, 3, True, 1.5, "0", None):
            candidate = copy.deepcopy(value)
            candidate["additional_evidence"]["message_requests"][0]["message_index"] = index
            with self.subTest(index=index), self.assertRaises(ValueError):
                validate_guided_result(candidate, source, bundle)
        for targets in ([], value["additional_evidence"]["message_requests"] * 2,
                        [{"anchor_evidence_id": "codex-company:event-2", "message_index": 0}],
                        [{"anchor_evidence_id": ref, "message_index": 0, "extra": True}]):
            candidate = copy.deepcopy(value)
            candidate["additional_evidence"]["message_requests"] = targets
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                validate_guided_result(candidate, source, bundle)
        # A partially supplied turn can legitimately be requested in full.
        value["additional_evidence"]["message_requests"][0]["message_index"] = 1
        source["sessions"][0]["events"][0]["text_length"] += 10
        validate_guided_result(value, source, bundle)
        for field in ("message_count",):
            old_source = copy.deepcopy(source)
            del old_source["sessions"][0][field]
            with self.assertRaises(ValueError):
                validate_guided_result(value, old_source, bundle)
        value["additional_evidence"]["kind"] = "outcome"
        with self.assertRaises(ValueError):
            validate_guided_result(value, source, bundle)

    def test_selection_and_type_explanations_are_bounded_and_cited(self):
        source = manifest()
        bundle = build_guide_bundle(source)
        value = valid_result(valid_finding("request_feedback", ["codex-company:event-1", "codex-company:event-2"]))
        changes = (
            lambda v: v.update(selection_reason=""),
            lambda v: v.update(selection_reason="x" * 2001),
            lambda v: v.update(selection_evidence_ids=[]),
            lambda v: v.update(selection_evidence_ids=["unknown"]),
            lambda v: v["findings"][0].update(type_reason=""),
            lambda v: v["findings"][0].update(type_reason="x" * 1001),
        )
        for change in changes:
            candidate = copy.deepcopy(value)
            change(candidate)
            with self.assertRaises(ValueError):
                validate_guided_result(candidate, source, bundle)

    def test_historical_reports_keep_their_frozen_contract(self):
        source = manifest()
        value = valid_result(valid_finding("learning_explanation", ["codex-company:event-1", "codex-company:event-2"]))
        value["result_version"] = LEGACY_REPORT_VERSION
        del value["selection_reason"], value["selection_evidence_ids"]
        del value["additional_evidence"]["message_requests"]
        del value["findings"][0]["type_reason"]
        for version in ("personal-improvement-core-v2", "personal-improvement-core-v3"):
            bundle = build_guide_bundle(source)
            bundle["core_version"] = version
            del bundle["report_version"]
            self.assertEqual(validate_guided_result(value, source, bundle)["result_version"], LEGACY_REPORT_VERSION)
            schema = result_schema(["learning_explanation"], report_version=LEGACY_REPORT_VERSION)
            self.assertNotIn("selection_reason", schema["required"])
            bundle["report_version"] = REPORT_VERSION
            with self.assertRaises(ValueError):
                validate_guided_result(value, source, bundle)
        with self.assertRaises(ValueError):
            validate_guided_result(value, source, build_guide_bundle(source))

    def test_previous_core_v4_keeps_report_v3_after_prose_numbering_correction(self):
        source = manifest()
        value = valid_result(valid_finding("learning_explanation", ["codex-company:event-1", "codex-company:event-2"]))
        bundle = build_guide_bundle(source)
        bundle["core_version"] = "personal-improvement-core-v4"
        del bundle["report_version"]
        self.assertEqual(validate_guided_result(value, source, bundle)["result_version"], REPORT_VERSION)
        current = (GUIDE_ROOT / "core-v5.md").read_text()
        previous = (GUIDE_ROOT / "core-v4.md").read_text()
        added = [line for line in current.splitlines() if line not in previous.splitlines()]
        self.assertEqual(len(added), 2)  # Version heading and one prose-position rule.
        self.assertIn("The product alone assigns human-readable positions", current)

    def test_previous_core_v5_keeps_its_report_contract(self):
        source = manifest()
        value = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        bundle = build_guide_bundle(source)
        bundle["core_version"] = "personal-improvement-core-v5"
        del bundle["report_version"]
        self.assertEqual(validate_guided_result(value, source, bundle)["result_version"], REPORT_VERSION)

    def test_decision_guidance_preserves_evidence_routes_and_abstention(self):
        bundle = build_guide_bundle(manifest())
        self.assertEqual(bundle["core_version"], "personal-improvement-core-v8")
        self.assertIn("specific comparison or behavior", bundle["core"])
        self.assertIn("how the answer would change the decision", bundle["core"])
        self.assertIn("An omitted position does not reveal its speaker", bundle["core"])
        self.assertIn("a declared supplement is already included", bundle["core"])
        playbook = next(p for p in bundle["playbooks"] if p["id"] == "request_feedback")
        self.assertEqual(playbook["version"], "v4")
        self.assertIn("A later owner correction explicitly names the intended result", playbook["content"])
        self.assertIn("does not establish how clearly the absent original request", playbook["content"])
        self.assertIn("A vague complaint plus an assistant apology", playbook["content"])
        self.assertIn("already accepted with no further friction remains excluded", playbook["content"])
        self.assertIn("after its underlying work and before the response is sent", playbook["content"])
        self.assertIn("or deciding whether execution may proceed", playbook["content"])

    def test_previous_core_v6_keeps_its_report_contract(self):
        source = manifest()
        value = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        bundle = build_guide_bundle(source)
        bundle["core_version"] = "personal-improvement-core-v6"
        bundle["core"] = (GUIDE_ROOT / "core-v6.md").read_text()
        bundle["core_sha256"] = sha256(bundle["core"].encode()).hexdigest()
        del bundle["report_version"]
        self.assertEqual(validate_guided_result(value, source, bundle)["result_version"], REPORT_VERSION)

    def test_application_guidance_preserves_existing_rules_and_report_shape(self):
        bundle = build_guide_bundle(manifest())
        core = (GUIDE_ROOT / "core-v7.md").read_text()
        section, after = core.split("## Make the application route concrete\n", 1)
        application, result = after.split("## Result\n", 1)
        previous = (GUIDE_ROOT / "core-v6.md").read_text()
        self.assertEqual(
            (section + "## Result\n" + result).replace("core · v7", "core · v6", 1), previous
        )
        for detail in (
            "change mechanism and its target", "reviewable proposed wording",
            "who sets it up, who performs it, when it activates",
            "one-time setup steps", "repeated work", "loading as unverified",
            "conditional adoption route", "repeat it in every prompt",
            "A setup once per Session still creates recurring work",
        ):
            self.assertIn(detail, application)
        current_application = bundle["core"].split(
            "## Make the application route concrete\n", 1
        )[1].split("## Result\n", 1)[0]
        self.assertEqual(current_application, application)
        self.assertEqual(bundle["report_version"], "personal-improvement-report-v3")
        handoff = result_schema(list(PLAYBOOK_IDS))["properties"]["findings"]["items"]["properties"]["handoff"]
        self.assertEqual(set(handoff["required"]), {
            "goal", "proposed_change", "scope", "constraints", "first_steps", "success_check"
        })

    def test_previous_core_v7_keeps_its_report_contract(self):
        source = manifest()
        value = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        bundle = build_guide_bundle(source)
        bundle["core_version"] = "personal-improvement-core-v7"
        bundle["core"] = (GUIDE_ROOT / "core-v7.md").read_text()
        bundle["core_sha256"] = sha256(bundle["core"].encode()).hexdigest()
        del bundle["report_version"]
        self.assertEqual(validate_guided_result(value, source, bundle)["result_version"], REPORT_VERSION)

    def test_proposal_follow_through_changes_only_the_decision_section(self):
        bundle = build_guide_bundle(manifest())
        current = bundle["core"]
        previous = (GUIDE_ROOT / "core-v7.md").read_text()
        before, decision_and_after = current.split(
            "## Decide what the evidence supports\n", 1
        )
        old_before, old_decision_and_after = previous.split(
            "## Decide what the evidence supports\n", 1
        )
        decision, after = decision_and_after.split(
            "## Choose a candidate and then its type\n", 1
        )
        _, old_after = old_decision_and_after.split(
            "## Choose a candidate and then its type\n", 1
        )
        self.assertEqual(before.replace("core · v8", "core · v7", 1), old_before)
        self.assertEqual(after, old_after)
        for detail in (
            "a mentioned method is not an applied method",
            "a conceptually new method is not required",
            "Unknown application must not become",
            "selected but not yet applied", "applied with outcome unknown",
            "owner-reported effective", "deferred/declined",
            "A proposal-only sample does not establish that need",
            "Do not tell the owner to install the same method again",
            "a no-new-finding answer must still answer the current question",
            "only if it changes the justified next action",
        ):
            self.assertIn(detail, decision)
        self.assertEqual(bundle["report_version"], REPORT_VERSION)
        self.assertEqual(bundle["core_sha256"], sha256(current.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
