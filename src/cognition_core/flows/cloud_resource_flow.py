from cognition_core.flow import CognitionFlow, start, listen, router
from pydantic import BaseModel

class CloudResourceState(BaseModel):
    resource_type: str = ""
    region: str = ""
    status: str = ""
    metadata: dict = {}

class CloudResourceFlow(CognitionFlow[CloudResourceState]):
    """Flow for managing cloud resources with approval gates"""

    @start()
    def analyze_request(self):
        """Analyze incoming resource request"""
        result = self.crews["analyzer"].kickoff(
            inputs={"request": self.state.resource_type}
        )
        return result.recommendation

    @router(analyze_request)
    def route_request(self, recommendation):
        """Route based on analysis"""
        if recommendation.get("risk_level") > 0.7:
            return "high_risk"
        return "standard"

    @listen("high_risk")
    def handle_high_risk(self):
        """Handle high-risk resource requests"""
        return self.crews["approval"].kickoff(
            inputs={"request": self.state}
        )

    @listen("standard")
    def provision_resource(self):
        """Provision the requested resource"""
        return self.crews["provisioner"].kickoff(
            inputs={"resource": self.state}
        ) 