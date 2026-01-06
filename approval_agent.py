"""Approval Agent - Human-in-the-Loop"""
class ApprovalAgent:
    async def request_approval(self, state):
        """Request human approval via Slack"""
        score = state.get("lead_score", 0)
        if score >= 90:
            return True  # Auto-approve
        # Would send Slack notification here
        return False  # Pending approval
