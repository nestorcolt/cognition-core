import pytest
from unittest.mock import Mock, patch
from cognition.flows.examples.cloud_resource_example import (
    EnterpriseCloudFlow,
    ResourceRequest,
    CloudResourceState
)

@pytest.fixture
def mock_crews():
    """Mock crew responses for testing"""
    return {
        "risk_analyzer": Mock(
            kickoff=Mock(return_value=Mock(
                analysis={"risk_factors": ["public_access"]},
                risk_level=0.8
            ))
        ),
        "approval_manager": Mock(
            kickoff=Mock(return_value=Mock(
                approved=True,
                approver="manager@company.com"
            ))
        ),
        "provisioner": Mock(
            kickoff=Mock(return_value=Mock(
                status="success",
                resource_id="i-123456"
            ))
        )
    }

@pytest.fixture
def test_request():
    """Sample resource request"""
    return ResourceRequest(
        service_type="ec2",
        specifications={"instance_type": "t2.micro"},
        environment="dev",
        requester="developer@company.com"
    )

@pytest.fixture
def flow_with_mocks(mock_crews):
    """Initialize flow with mock crews"""
    flow = EnterpriseCloudFlow()
    flow.crews = mock_crews
    flow.state = CloudResourceState(
        request=test_request()
    )
    return flow

def test_assess_request_high_risk(flow_with_mocks):
    """Test high-risk resource assessment"""
    result = flow_with_mocks.assess_request()
    
    # Verify risk analyzer was called with correct inputs
    flow_with_mocks.crews["risk_analyzer"].kickoff.assert_called_once()
    
    # Check risk level returned
    assert result == 0.8
    
    # Verify state was updated
    assert "risk_factors" in flow_with_mocks.state.risk_assessment

def test_high_risk_approval_flow(flow_with_mocks):
    """Test complete high-risk approval flow"""
    # Trigger assessment
    flow_with_mocks.assess_request()
    
    # Request approval
    result = flow_with_mocks.request_approval()
    
    # Verify approval manager was called
    flow_with_mocks.crews["approval_manager"].kickoff.assert_called_once()
    assert result.approved is True

def test_auto_provision_flow(flow_with_mocks):
    """Test auto-provision flow for medium/low risk"""
    # Mock risk analyzer to return low risk
    flow_with_mocks.crews["risk_analyzer"].kickoff.return_value = Mock(
        analysis={"risk_factors": []},
        risk_level=0.2
    )
    
    # Trigger assessment
    flow_with_mocks.assess_request()
    
    # Auto provision
    result = flow_with_mocks.auto_provision()
    
    # Verify provisioner was called with correct inputs
    flow_with_mocks.crews["provisioner"].kickoff.assert_called_once()
    assert result.status == "success"
    assert result.resource_id == "i-123456"

def test_risk_routing(flow_with_mocks):
    """Test risk-based routing logic"""
    test_cases = [
        (0.8, "high_risk"),
        (0.5, "medium_risk"),
        (0.2, "low_risk")
    ]
    
    for risk_level, expected_route in test_cases:
        route = flow_with_mocks.route_by_risk(risk_level)
        assert route == expected_route

@pytest.mark.asyncio
async def test_flow_execution(flow_with_mocks):
    """Test complete flow execution"""
    with patch('cognition.flow.CognitionFlow.kickoff') as mock_kickoff:
        mock_kickoff.return_value = {"status": "success", "resource_id": "i-123456"}
        
        result = await flow_with_mocks.kickoff(
            inputs={
                "service_type": "ec2",
                "specifications": {"instance_type": "t2.micro"},
                "environment": "dev"
            }
        )
        
        assert result["status"] == "success"
        assert result["resource_id"] == "i-123456" 