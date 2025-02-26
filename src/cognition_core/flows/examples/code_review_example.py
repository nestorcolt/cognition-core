from cognition.flow import CognitionFlow, start, listen
from pydantic import BaseModel
from typing import List, Dict

class PullRequest(BaseModel):
    repo: str
    pr_number: int
    files_changed: List[str]
    diff_content: str
    author: str

class CodeReviewState(BaseModel):
    pr: PullRequest
    static_analysis: Dict = {}
    security_scan: Dict = {}
    review_comments: List[Dict] = []
    approval_status: str = "pending"

class EnterpriseCodeReviewFlow(CognitionFlow[CodeReviewState]):
    """Enterprise code review automation flow"""

    @start()
    def analyze_code(self):
        """Run static code analysis"""
        result = self.crews["code_analyzer"].kickoff(
            inputs={
                "files": self.state.pr.files_changed,
                "diff": self.state.pr.diff_content
            }
        )
        self.state.static_analysis = result.analysis
        return result

    @listen(analyze_code)
    def security_scan(self, analysis_result):
        """Perform security vulnerability scan"""
        result = self.crews["security_scanner"].kickoff(
            inputs={
                "analysis": analysis_result,
                "files": self.state.pr.files_changed
            }
        )
        self.state.security_scan = result.vulnerabilities
        return result

    @listen(security_scan)
    def pattern_analysis(self, security_result):
        """Analyze code patterns and suggest improvements"""
        return self.crews["pattern_analyzer"].kickoff(
            inputs={
                "static_analysis": self.state.static_analysis,
                "security_scan": security_result,
                "diff": self.state.pr.diff_content
            }
        )

    @listen(pattern_analysis)
    def generate_review(self, pattern_result):
        """Generate comprehensive review comments"""
        review = self.crews["review_generator"].kickoff(
            inputs={
                "analysis": self.state.static_analysis,
                "security": self.state.security_scan,
                "patterns": pattern_result,
                "author": self.state.pr.author
            }
        )
        self.state.review_comments = review.comments
        return review 