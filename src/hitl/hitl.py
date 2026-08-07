"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 11: Confidence Router
  TODO 12: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 11: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )
        else:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason="Low confidence — escalating",
                priority="high",
                requires_human=True,
            )


# ============================================================
# TODO 12: Design 3 HITL decision points + a review lifecycle
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-Value Money Transfer Approval",
        "trigger": "User requests external money transfer exceeding 50,000,000 VND or high-risk recipient account",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Sender account, Receiver account & bank, Amount, User transaction history summary, Risk score",
        "example": "Customer asks to transfer 100,000,000 VND to an external bank account for the first time.",
        "approval_path": "Approve -> Execute transfer via Gateway; Reject -> Notify user & cancel; Timeout (5m) -> Auto-reject transaction",
        "audit_fields": "correlation_id, intent='transfer_money', diff={'amount': 100000000, 'target': '0123456789'}, reviewer_id, verdict, timestamp",
    },
    {
        "id": 2,
        "name": "Account Closure & Credential Reset",
        "trigger": "Action type matches 'close_account', 'change_password', or 'update_personal_info'",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Account ID, Request type, OTP verification status, Customer identity verification diff",
        "example": "Customer submits request to update primary phone number and close savings account.",
        "approval_path": "Approve -> Trigger bank core API update; Reject -> Retain existing details; Timeout (10m) -> Fail closed",
        "audit_fields": "correlation_id, intent='update_personal_info', diff={'old_phone': '0901...', 'new_phone': '0909...'}, reviewer_id, verdict, timestamp",
    },
    {
        "id": 3,
        "name": "Ambiguous or Low Confidence Financial Advice",
        "trigger": "LLM response confidence score falls below 0.7 for complex product inquiries",
        "hitl_model": "human-on-the-loop",
        "context_needed": "User prompt, Draft LLM response, Retrieved RAG financial product docs, Confidence metrics",
        "example": "Customer asks a complex tax/loan calculation question where RAG context is partially ambiguous.",
        "approval_path": "Approve draft -> Send to user; Edit -> Reviewer rewrites response; Reject -> Route to human support chat",
        "audit_fields": "correlation_id, intent='loan_query', confidence=0.58, draft_text, final_text, reviewer_id, verdict, timestamp",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
