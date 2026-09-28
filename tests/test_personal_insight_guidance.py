import copy
import unittest

from localbrain.personal_insight_evidence import MANIFEST_VERSION
from localbrain.personal_insight_guidance import (
    CORE_VERSION,
    GUIDE_ROOT,
    PLAYBOOKS,
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
                "events": [{
                    "source_key": "codex-company",
                    "event_id": f"event-{index}",
                    "role": "user",
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
        "outcome": "findings",
        "findings": [finding],
        "no_finding_reason": "",
        "additional_evidence": {"kind": "none", "question": "", "evidence_ids": []},
        "limits": "표본으로 실제 학습 성과를 확인할 수 없다.",
    }


class PersonalInsightGuidanceTests(unittest.TestCase):
    def test_all_versioned_resources_exist_and_are_selectively_loaded(self):
        self.assertEqual(len(PLAYBOOKS), 11)
        for playbook_id, _ in PLAYBOOKS:
            content = (GUIDE_ROOT / "playbooks" / f"{playbook_id}-v1.md").read_text()
            for field in (
                "Trigger", "Exclude", "Evidence questions", "Benign alternative",
                "Intervention", "Output sketch", "Follow-up", "Current-source limit",
            ):
                self.assertIn(field, content, (playbook_id, field))
        bundle = build_guide_bundle(manifest(question="왜 같은 개념을 다시 물어보지?"))
        self.assertEqual(bundle["core_version"], CORE_VERSION)
        self.assertLessEqual(len(bundle["playbooks"]), 4)
        self.assertIn("learning_explanation", [item["id"] for item in bundle["playbooks"]])
        self.assertEqual(len(bundle["core_sha256"]), 64)
        self.assertIn("answer the person's actual question first", guide_text(bundle))

    def test_noncode_and_harness_routing_are_distinct(self):
        noncode = build_guide_bundle(manifest(question="내 글을 독자가 더 쉽게 이해하게 하려면?"))
        self.assertNotIn(
            "assistant_configuration", [item["id"] for item in noncode["playbooks"]]
        )
        harness = build_guide_bundle(manifest(
            question="스킬 라우팅과 AGENTS.md 설정을 어떻게 개선해?",
            excerpts=("The skill used the wrong instruction",),
        ))
        self.assertIn(
            "assistant_configuration", [item["id"] for item in harness["playbooks"]]
        )

    def test_question_priority_and_broad_fallback(self):
        question_led = build_guide_bundle(manifest(
            question="토큰 비용을 어떻게 줄여?",
            excerpts=(
                "Verify the answer and test the artifact against the source",
                "Check the result, explain the error, and document the decision",
            ),
        ))
        self.assertEqual(question_led["playbooks"][0]["id"], "task_fit_effort")
        fallback = build_guide_bundle(manifest(excerpts=("hello", "another message")))
        self.assertEqual(fallback["route_reason"], "broad_fallback_no_lexical_cue")
        self.assertEqual(len(fallback["playbooks"]), 4)

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

    def test_invalid_claims_and_shapes_are_rejected(self):
        source = manifest(question="왜 같은 개념을 다시 물어보지?")
        bundle = build_guide_bundle(source)
        base = valid_result(valid_finding(
            "learning_explanation", ["codex-company:event-1", "codex-company:event-2"]
        ))
        changes = [
            lambda result: result.update(extra="unknown"),
            lambda result: result["findings"][0].update(type_id="assistant_configuration"),
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


if __name__ == "__main__":
    unittest.main()
