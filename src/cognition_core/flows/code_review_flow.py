from cognition_core.flow import CognitionFlow, start, listen
from pydantic import BaseModel


class CodeReviewState(BaseModel):
    repo: str = ""
    pr_number: int = 0
    changes: list = []
    review_status: str = "pending"


class CodeReviewFlow(CognitionFlow[CodeReviewState]):
    """Flow for automated code review and quality checks"""

    @start()
    def analyze_changes(self):
        """Analyze code changes"""
        result = self.crews["code_analyzer"].kickoff(
            inputs={"repo": self.state.repo, "changes": self.state.changes}
        )
        self.state.analysis = result.analysis
        return result

    @listen(analyze_changes)
    def security_check(self, analysis):
        """Perform security analysis"""
        return self.crews["security"].kickoff(inputs={"analysis": analysis})

    @listen(security_check)
    def generate_review(self, security_report):
        """Generate final review comments"""
        return self.crews["reviewer"].kickoff(
            inputs={"analysis": self.state.analysis, "security": security_report}
        )
