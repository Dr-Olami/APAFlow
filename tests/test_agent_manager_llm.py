"""
Tests for AgentManager integration with AGENT-003 LLM system.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from smeflow.agents.manager import AgentManager
from smeflow.agents.llm_manager import LLMRequest, LLMResponse, ProviderStrategy
from smeflow.agents.base import AgentType, AgentStatus
from langchain_core.messages import HumanMessage, SystemMessage


class TestAgentManagerLLMIntegration:
    """Test cases for AgentManager LLM integration."""
    
    @pytest.fixture
    def agent_manager(self):
        """Create AgentManager instance."""
        with patch('smeflow.agents.manager.agent_persistence_service'):
            manager = AgentManager(tenant_id="test-tenant", region="NG")
            manager.agents = {}  # Clear any loaded agents
            return manager
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        agent = Mock()
        agent.agent_id = "test-agent-123"
        agent.config = Mock()
        agent.config.tenant_id = "test-tenant"
        agent.config.region = "NG"
        agent.config.agent_type = AgentType.AUTOMATOR
        agent.status = AgentStatus.ACTIVE
        return agent
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for LLM requests."""
        return [
            SystemMessage(content="You are a helpful research assistant."),
            HumanMessage(content="What are the key economic indicators for Nigeria?")
        ]
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_success(self, agent_manager, mock_agent, sample_messages):
        """Test successful LLM request execution."""
        # Add mock agent to manager
        agent_manager.agents[mock_agent.agent_id] = mock_agent
        
        # Mock LLM response
        mock_response = LLMResponse(
            content="Nigeria's key economic indicators include GDP growth rate, inflation rate, unemployment rate, and oil production levels.",
            provider="openai",
            model="gpt-4o",
            input_tokens=25,
            output_tokens=20,
            total_tokens=45,
            cost_usd=0.002,
            cost_local=3.3,
            currency="NGN",
            response_time_ms=750,
            cache_hit=False,
            request_hash="test-hash-123"
        )
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(return_value=mock_response)
            
            result = await agent_manager.execute_llm_request(
                agent_id=mock_agent.agent_id,
                messages=sample_messages,
                tenant_id="test-tenant",
                strategy=ProviderStrategy.BALANCED,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Verify result
            assert result == mock_response
            assert result.provider == "openai"
            assert result.total_tokens == 45
            assert result.cost_usd == 0.002
            assert result.cache_hit is False
            
            # Verify LLM manager was called correctly
            mock_llm_manager.execute_request.assert_called_once()
            call_args = mock_llm_manager.execute_request.call_args[0][0]
            assert isinstance(call_args, LLMRequest)
            assert call_args.tenant_id == "test-tenant"
            assert call_args.agent_id == mock_agent.agent_id
            assert call_args.region == "NG"
            assert call_args.strategy == ProviderStrategy.BALANCED
            assert call_args.temperature == 0.7
            assert call_args.max_tokens == 1000
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_agent_not_found(self, agent_manager, sample_messages):
        """Test LLM request with non-existent agent."""
        with pytest.raises(ValueError, match="Agent non-existent-agent not found"):
            await agent_manager.execute_llm_request(
                agent_id="non-existent-agent",
                messages=sample_messages,
                tenant_id="test-tenant"
            )
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_with_defaults(self, agent_manager, mock_agent, sample_messages):
        """Test LLM request with default parameters."""
        # Add mock agent to manager
        agent_manager.agents[mock_agent.agent_id] = mock_agent
        
        mock_response = LLMResponse(
            content="Default response",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=20,
            output_tokens=15,
            total_tokens=35,
            cost_usd=0.001,
            cost_local=1.65,
            currency="NGN",
            response_time_ms=400,
            cache_hit=True,
            request_hash="default-hash"
        )
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(return_value=mock_response)
            
            result = await agent_manager.execute_llm_request(
                agent_id=mock_agent.agent_id,
                messages=sample_messages,
                tenant_id="test-tenant"
                # Using all defaults
            )
            
            # Verify defaults were used
            call_args = mock_llm_manager.execute_request.call_args[0][0]
            assert call_args.strategy == ProviderStrategy.BALANCED
            assert call_args.temperature == 0.7
            assert call_args.max_tokens is None
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_different_strategies(self, agent_manager, mock_agent, sample_messages):
        """Test LLM request with different provider strategies."""
        agent_manager.agents[mock_agent.agent_id] = mock_agent
        
        strategies_to_test = [
            ProviderStrategy.COST_OPTIMIZED,
            ProviderStrategy.QUALITY_FOCUSED,
            ProviderStrategy.FASTEST
        ]
        
        for strategy in strategies_to_test:
            mock_response = LLMResponse(
                content=f"Response for {strategy.value}",
                provider="openai",
                model="gpt-4o",
                input_tokens=20,
                output_tokens=15,
                total_tokens=35,
                cost_usd=0.001,
                cost_local=1.65,
                currency="NGN",
                response_time_ms=500,
                cache_hit=False,
                request_hash=f"hash-{strategy.value}"
            )
            
            with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
                mock_llm_manager.execute_request = AsyncMock(return_value=mock_response)
                
                result = await agent_manager.execute_llm_request(
                    agent_id=mock_agent.agent_id,
                    messages=sample_messages,
                    tenant_id="test-tenant",
                    strategy=strategy
                )
                
                # Verify strategy was passed correctly
                call_args = mock_llm_manager.execute_request.call_args[0][0]
                assert call_args.strategy == strategy
    
    def test_get_llm_analytics(self, agent_manager):
        """Test LLM analytics retrieval."""
        mock_analytics = {
            "total_requests": 150,
            "total_tokens": 45000,
            "total_cost_usd": 2.5,
            "cache_hit_rate": 0.35,
            "avg_response_time": 650,
            "provider_breakdown": {
                "openai": {"requests": 100, "tokens": 30000, "cost_usd": 1.8},
                "anthropic": {"requests": 50, "tokens": 15000, "cost_usd": 0.7}
            },
            "model_breakdown": {
                "openai:gpt-4o": {"requests": 80, "tokens": 24000, "cost_usd": 1.5},
                "openai:gpt-4o-mini": {"requests": 20, "tokens": 6000, "cost_usd": 0.3},
                "anthropic:claude-3-sonnet": {"requests": 50, "tokens": 15000, "cost_usd": 0.7}
            }
        }
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.get_usage_analytics.return_value = mock_analytics
            
            result = agent_manager.get_llm_analytics(
                tenant_id="test-tenant",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )
            
            assert result == mock_analytics
            mock_llm_manager.get_usage_analytics.assert_called_once_with(
                "test-tenant",
                datetime(2024, 1, 1),
                datetime(2024, 1, 31)
            )
    
    def test_get_tenant_agents(self, agent_manager):
        """Test getting agents for specific tenant."""
        # Create mock agents for different tenants
        agent1 = Mock()
        agent1.config.tenant_id = "test-tenant"
        agent1.config.agent_type = AgentType.AUTOMATOR
        
        agent2 = Mock()
        agent2.config.tenant_id = "test-tenant"
        agent2.config.agent_type = AgentType.AUTOMATOR
        
        agent3 = Mock()
        agent3.config.tenant_id = "other-tenant"
        agent3.config.agent_type = AgentType.MENTOR
        
        agent_manager.agents = {
            "agent1": agent1,
            "agent2": agent2,
            "agent3": agent3
        }
        
        # Get agents for test-tenant
        tenant_agents = agent_manager.get_tenant_agents("test-tenant")
        
        assert len(tenant_agents) == 2
        assert agent1 in tenant_agents
        assert agent2 in tenant_agents
        assert agent3 not in tenant_agents
    
    def test_get_usage_analytics_comprehensive(self, agent_manager):
        """Test comprehensive usage analytics including LLM data."""
        # Mock tenant agents
        agent1 = Mock()
        agent1.config.tenant_id = "test-tenant"
        agent1.config.agent_type = AgentType.AUTOMATOR
        agent1.status = AgentStatus.ACTIVE
        agent1.execution_history = []

        agent2 = Mock()
        agent2.config.tenant_id = "test-tenant"
        agent2.config.agent_type = AgentType.AUTOMATOR
        agent2.status = AgentStatus.INACTIVE
        agent2.execution_history = []
        
        agent_manager.agents = {"agent1": agent1, "agent2": agent2}
        
        # Mock LLM analytics
        mock_llm_analytics = {
            "total_requests": 100,
            "total_tokens": 30000,
            "total_cost_usd": 1.5,
            "cache_hit_rate": 0.4,
            "avg_response_time": 600
        }
        
        with patch.object(agent_manager, 'get_tenant_agents') as mock_get_tenant:
            with patch.object(agent_manager, 'get_llm_analytics') as mock_get_llm:
                mock_get_tenant.return_value = [agent1, agent2]
                mock_get_llm.return_value = mock_llm_analytics
                
                result = agent_manager.get_usage_analytics("test-tenant")
                
                # Verify comprehensive analytics
                assert result["tenant_id"] == "test-tenant"
                assert result["total_agents"] == 2
                assert result["active_agents"] == 1
                assert result["llm_usage"] == mock_llm_analytics
                assert "agents_by_type" in result
                assert result["agents_by_type"][AgentType.AUTOMATOR.value] == 2
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_with_regional_config(self, agent_manager, sample_messages):
        """Test LLM request with different regional configurations."""
        # Create agents for different regions
        ng_agent = Mock()
        ng_agent.agent_id = "ng-agent"
        ng_agent.config.tenant_id = "test-tenant"
        ng_agent.config.region = "NG"
        
        ke_agent = Mock()
        ke_agent.agent_id = "ke-agent"
        ke_agent.config.tenant_id = "test-tenant"
        ke_agent.config.region = "KE"
        
        agent_manager.agents = {
            "ng-agent": ng_agent,
            "ke-agent": ke_agent
        }
        
        mock_response = LLMResponse(
            content="Regional response",
            provider="openai",
            model="gpt-4o",
            input_tokens=20,
            output_tokens=15,
            total_tokens=35,
            cost_usd=0.001,
            cost_local=150.0,  # KES
            currency="KES",
            response_time_ms=500,
            cache_hit=False,
            request_hash="regional-hash"
        )
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(return_value=mock_response)
            
            # Test with Kenyan agent
            await agent_manager.execute_llm_request(
                agent_id="ke-agent",
                messages=sample_messages,
                tenant_id="test-tenant"
            )
            
            # Verify region was passed correctly
            call_args = mock_llm_manager.execute_request.call_args[0][0]
            assert call_args.region == "KE"
            assert call_args.agent_id == "ke-agent"


class TestAgentManagerLLMErrorHandling:
    """Test error handling in AgentManager LLM integration."""
    
    @pytest.fixture
    def agent_manager(self):
        """Create AgentManager instance."""
        with patch('smeflow.agents.manager.agent_persistence_service'):
            manager = AgentManager(tenant_id="test-tenant", region="NG")
            manager.agents = {}
            return manager
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        agent = Mock()
        agent.agent_id = "test-agent"
        agent.config = Mock()
        agent.config.tenant_id = "test-tenant"
        agent.config.region = "NG"
        return agent
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_llm_manager_error(self, agent_manager, mock_agent):
        """Test LLM request when LLM manager raises error."""
        agent_manager.agents[mock_agent.agent_id] = mock_agent
        
        messages = [HumanMessage(content="Test message")]
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(
                side_effect=Exception("All LLM providers failed")
            )
            
            with pytest.raises(Exception, match="All LLM providers failed"):
                await agent_manager.execute_llm_request(
                    agent_id=mock_agent.agent_id,
                    messages=messages,
                    tenant_id="test-tenant"
                )
    
    @pytest.mark.asyncio
    async def test_execute_llm_request_agent_missing_region(self, agent_manager):
        """Test LLM request with agent missing region config."""
        agent = Mock()
        agent.agent_id = "no-region-agent"
        agent.config = Mock()
        agent.config.tenant_id = "test-tenant"
        # No region attribute
        
        agent_manager.agents[agent.agent_id] = agent
        
        messages = [HumanMessage(content="Test message")]
        mock_response = LLMResponse(
            content="Response",
            provider="openai",
            model="gpt-4o",
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
            cost_usd=0.001,
            cost_local=1.65,
            currency="NGN",
            response_time_ms=500,
            cache_hit=False,
            request_hash="no-region-hash"
        )
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(return_value=mock_response)
            
            result = await agent_manager.execute_llm_request(
                agent_id=agent.agent_id,
                messages=messages,
                tenant_id="test-tenant"
            )
            
            # Should default to "NG"
            call_args = mock_llm_manager.execute_request.call_args[0][0]
            assert call_args.region == "NG"
    
    def test_get_llm_analytics_error(self, agent_manager):
        """Test LLM analytics when LLM manager raises error."""
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.get_usage_analytics.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Database error"):
                agent_manager.get_llm_analytics("test-tenant")


class TestAgentManagerLLMPerformance:
    """Test performance aspects of AgentManager LLM integration."""
    
    @pytest.fixture
    def agent_manager(self):
        """Create AgentManager instance."""
        with patch('smeflow.agents.manager.agent_persistence_service'):
            manager = AgentManager(tenant_id="test-tenant", region="NG")
            manager.agents = {}
            return manager
    
    @pytest.mark.asyncio
    async def test_concurrent_llm_requests(self, agent_manager):
        """Test concurrent LLM requests."""
        # Create multiple agents
        agents = []
        for i in range(5):
            agent = Mock()
            agent.agent_id = f"agent-{i}"
            agent.config = Mock()
            agent.config.tenant_id = "test-tenant"
            agent.config.region = "NG"
            agents.append(agent)
            agent_manager.agents[agent.agent_id] = agent
        
        messages = [HumanMessage(content="Concurrent test")]
        
        # Mock responses with different timing
        def create_mock_response(agent_id):
            return LLMResponse(
                content=f"Response for {agent_id}",
                provider="openai",
                model="gpt-4o",
                input_tokens=10,
                output_tokens=10,
                total_tokens=20,
                cost_usd=0.001,
                cost_local=1.65,
                currency="NGN",
                response_time_ms=500,
                cache_hit=False,
                request_hash=f"hash-{agent_id}"
            )
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.execute_request = AsyncMock(
                side_effect=lambda req: create_mock_response(req.agent_id)
            )
            
            # Execute concurrent requests
            tasks = [
                agent_manager.execute_llm_request(
                    agent_id=agent.agent_id,
                    messages=messages,
                    tenant_id="test-tenant"
                )
                for agent in agents
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all requests completed
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result.content == f"Response for agent-{i}"
            
            # Verify all requests were made
            assert mock_llm_manager.execute_request.call_count == 5
    
    def test_get_usage_analytics_large_dataset(self, agent_manager):
        """Test usage analytics with large dataset."""
        # Mock large analytics dataset
        large_analytics = {
            "total_requests": 10000,
            "total_tokens": 5000000,
            "total_cost_usd": 250.0,
            "cache_hit_rate": 0.65,
            "avg_response_time": 450,
            "provider_breakdown": {
                f"provider-{i}": {
                    "requests": 1000,
                    "tokens": 500000,
                    "cost_usd": 25.0
                }
                for i in range(10)
            },
            "model_breakdown": {
                f"provider-{i}:model-{j}": {
                    "requests": 100,
                    "tokens": 50000,
                    "cost_usd": 2.5
                }
                for i in range(10)
                for j in range(10)
            }
        }
        
        with patch('smeflow.agents.manager.llm_manager') as mock_llm_manager:
            mock_llm_manager.get_usage_analytics.return_value = large_analytics
            
            result = agent_manager.get_llm_analytics("test-tenant")
            
            assert result["total_requests"] == 10000
            assert len(result["provider_breakdown"]) == 10
            assert len(result["model_breakdown"]) == 100


if __name__ == "__main__":
    pytest.main([__file__])
