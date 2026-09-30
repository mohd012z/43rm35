from tools.ai_review.decision import decide


def test_consensus_without_evidence_cannot_pass():
    result = decide(
        lola="TRUE",
        kernel_ai="TRUE",
        in_ai="TRUE",
        evidence_status="INSUFFICIENT_EVIDENCE",
    )
    assert result == "INSUFFICIENT_EVIDENCE"


def test_agent_disagreement_requires_review():
    result = decide(
        lola="TRUE",
        kernel_ai="FALSE",
        in_ai="UNKNOWN",
        evidence_status="UNKNOWN",
    )
    assert result == "UNKNOWN"


def test_sha_mismatch_is_stale():
    result = decide(
        lola="TRUE",
        kernel_ai="TRUE",
        in_ai="TRUE",
        evidence_status="STALE",
    )
    assert result == "STALE"


def test_counter_evidence_blocks_as_contradicted():
    result = decide(
        lola="TRUE",
        kernel_ai="TRUE",
        in_ai="TRUE",
        evidence_status="CONTRADICTED",
    )
    assert result == "CONTRADICTED"


def test_only_independently_verified_evidence_can_pass():
    result = decide(
        lola="TRUE",
        kernel_ai="TRUE",
        in_ai="TRUE",
        evidence_status="VERIFIED_TRUE",
    )
    assert result == "VERIFIED_TRUE"
