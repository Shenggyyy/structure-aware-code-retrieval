"""Deterministic v2 response contracts for exact, already validated QA answers."""


def _object(properties: dict) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _enum(values: list, kind: str = "string") -> dict:
    return {"type": kind, "enum": values}


def _array(values: list, kind: str = "string", *, minimum: int = 0) -> dict:
    # Empty enum is not a valid provider schema. maxItems=0 expresses an empty list.
    return {
        "type": "array",
        "items": _enum(values, kind) if values else {"type": kind},
        "minItems": minimum,
        "maxItems": len(values),
    }


def response_contract(answer: dict, evidence: list[dict], reference: dict) -> dict:
    """Catalog full output IDs and legal states without modifying any source material."""
    packed = [f"packed:{source['id']}" for source in evidence]
    sources = [f"reference:{source['id']}" for source in reference["reference_evidence"]]
    claims = [
        {
            "claim_index": index,
            "citation_evidence_ids": [f"packed:{value}" for value in claim["citations"]],
        }
        for index, claim in enumerate(answer["claims"])
    ]
    cited = {value for claim in claims for value in claim["citation_evidence_ids"]}
    indices = list(range(len(claims)))
    answered = answer["status"] == "answered"
    dimensions = {}
    for dimension in ("correctness", "completeness", "citation_support"):
        if answered:
            states = [
                {"status": "scored", "scores": [0, 1, 2, 3]},
                {"status": "unsure", "scores": [None]},
            ]
        elif dimension != "completeness":
            states = [{"status": "not_applicable", "scores": [None]}]
        elif reference["expected_status"] == "answered":
            states = [
                {"status": "scored", "scores": [0]},
                {"status": "unsure", "scores": [None]},
            ]
        else:
            states = [
                {"status": "not_applicable", "scores": [None]},
                {"status": "unsure", "scores": [None]},
            ]
        allowed = [value for value in packed if value in cited]
        if dimension != "citation_support":
            allowed = packed + sources
        dimensions[dimension] = {
            "states": states,
            "evidence_ids": allowed,
            "claim_indices": indices,
        }
    pairs = [
        {"decision": "not_abstained" if answered else decision, "sufficiency": sufficiency}
        for decision, sufficiency in (
            ("unnecessary", "sufficient"),
            ("appropriate", "insufficient"),
            ("unsure", "unsure"),
        )
        if packed or sufficiency == "insufficient"
    ]
    return {
        "version": 2,
        "packed_evidence_ids": packed,
        "reference_evidence_ids": sources,
        "claims": claims,
        "dimensions": dimensions,
        "abstention": {"allowed_pairs": pairs, "evidence_ids": packed},
        "reference_rules": {
            "usable": {
                "completeness": dimensions["completeness"]["states"]
                if answered
                else [dimensions["completeness"]["states"][0]],
                "reference_issues": "May be empty; verify reference adequacy from sources.",
            },
            "inadequate_or_conflicting": {
                "completeness": [{"status": "unsure", "scores": [None]}],
                "reference_issues": "At least one nonblank explanation is required.",
            },
        },
    }


def build_schema(answer: dict, evidence: list[dict], reference: dict, rubric_id: str) -> dict:
    """Use only the supported strict-schema subset; cross-field semantics stay on host."""
    contract = response_contract(answer, evidence, reference)
    properties = {"rubric_id": _enum([rubric_id])}
    for dimension, rules in contract["dimensions"].items():
        branches = []
        for state in rules["states"]:
            # Separate score zero from positive scores to require evidence for positive claims.
            score_sets = [[0], [1, 2, 3]] if len(state["scores"]) == 4 else [state["scores"]]
            for scores in score_sets:
                positive = scores[0] is not None and scores[0] > 0
                cited_claims = dimension == "citation_support" and state["status"] == "scored"
                branches.append(
                    _object(
                        {
                            "status": _enum([state["status"]]),
                            "score": _enum(scores, "null" if scores == [None] else "integer"),
                            "rationale": {"type": "string", "minLength": 1},
                            "evidence_ids": _array(rules["evidence_ids"], minimum=int(positive)),
                            "claim_indices": _array(
                                rules["claim_indices"],
                                "integer",
                                minimum=int(positive or cited_claims),
                            ),
                        }
                    )
                )
        properties[dimension] = {"anyOf": branches}
    properties["abstention"] = {
        "anyOf": [
            _object(
                {
                    "decision": _enum([pair["decision"]]),
                    "packed_context_sufficiency": _enum([pair["sufficiency"]]),
                    "rationale": {"type": "string", "minLength": 1},
                    "evidence_ids": _array(contract["abstention"]["evidence_ids"]),
                }
            )
            for pair in contract["abstention"]["allowed_pairs"]
        ]
    }
    properties["reference_status"] = _enum(["usable", "inadequate", "conflicting"])
    properties["reference_issues"] = {
        "type": "array",
        "items": {"type": "string", "minLength": 1},
    }
    return _object(properties)
