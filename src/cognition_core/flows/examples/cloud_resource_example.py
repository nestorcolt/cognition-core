from crewai.flow.flow import start, listen, router
from cognition_core.flow import CognitionFlow
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class ResourceRequest(BaseModel):
    service_type: str  # e.g., "ec2", "rds"
    specifications: Dict[str, Any]
    environment: str  # e.g., "dev", "prod"
    requester: str

class CloudResourceState(BaseModel):
    request: Optional[ResourceRequest] = None
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    approvals: List[str] = Field(default_factory=list)
    provision_status: str = "pending"
    
class EnterpriseCloudFlow(CognitionFlow[CloudResourceState]):
    """Enterprise-grade cloud resource provisioning flow"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            state_type=CloudResourceState,
            *args, 
            **kwargs
        )
    
    @start()
    def assess_request(self):
        """Analyze request for risks and compliance"""
        result = self.crews["risk_analyzer"].kickoff(
            inputs={
                "request": self.state.request.dict(),
                "environment": self.state.request.environment
            }
        )
        self.state.risk_assessment = result.analysis
        return result.risk_level

    @router(assess_request)
    def route_by_risk(self, risk_level: float):
        if risk_level > 0.7:
            return "high_risk"
        elif risk_level > 0.4:
            return "medium_risk"
        return "low_risk"

    @listen("high_risk")
    def request_approval(self):
        """Get manager approval for high-risk requests"""
        return self.crews["approval_manager"].kickoff(
            inputs={
                "request": self.state.request.dict(),
                "risk_assessment": self.state.risk_assessment
            }
        )

    @listen("medium_risk", "low_risk")
    def auto_provision(self):
        """Automatically provision approved or low-risk resources"""
        return self.crews["provisioner"].kickoff(
            inputs={
                "request": self.state.request.dict(),
                "environment": self.state.request.environment
            }
        ) 