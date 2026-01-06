"""Qualifier Agent - Lead Scoring"""
class QualifierAgent:
    async def score_lead(self, lead_data, research_results):
        """Score lead 0-100"""
        score = 50  # Base score
        if research_results.get("quality_score", 0) > 80:
            score += 30
        return min(score, 100)
