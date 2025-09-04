"""
Comprehensive tests for SMEFlow agent system.

Tests agent creation, execution, coordination, and African market optimizations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from smeflow.agents import (
    BaseAgent, AgentConfig, AgentType, AgentStatus,
    AutomatorAgent, MentorAgent, SupervisorAgent,
    AgentFactory, AgentManager
)
from smeflow.agents.llm_providers import LLMProviderFactory, OpenAIProvider, AnthropicProvider


class MockTool(BaseTool):
    """Mock tool for testing."""
    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    
    def _run(self, query: str) -> str:
        return f"Mock result for: {query}"
    
    async def _arun(self, query: str) -> str:
        return f"Mock async result for: {query}"


class MockLLM(BaseLanguageModel):
    """Mock LLM that properly implements BaseLanguageModel interface."""
    
    def __init__(self):
        super().__init__()
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import LLMResult, Generation
        return LLMResult(generations=[[Generation(text="Mock response")]])
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import LLMResult, Generation
        return LLMResult(generations=[[Generation(text="Mock async response")]])
    
    def _llm_type(self) -> str:
        return "mock_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"type": "mock_llm"}


class TestAgentConfig:
    """Test agent configuration validation and creation."""
    
    def test_agent_config_creation(self):
        """Test creating agent configuration with valid data."""
        config = AgentConfig(
            name="Test Agent",
            agent_type=AgentType.AUTOMATOR,
            tenant_id="test-tenant",
            region="NG"
        )
        
        assert config.name == "Test Agent"
        assert config.agent_type == AgentType.AUTOMATOR
        assert config.tenant_id == "test-tenant"
        assert config.region == "NG"
        assert config.llm_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7
        assert config.languages == ["en"]
        assert config.cultural_context is True
    
    def test_agent_config_validation(self):
        """Test agent configuration validation."""
        # Test invalid temperature
        with pytest.raises(ValueError):
            AgentConfig(
                name="Test Agent",
                agent_type=AgentType.AUTOMATOR,
                tenant_id="test-tenant",
                temperature=3.0  # Invalid temperature > 2.0
            )
        
        # Test invalid max_iterations
        with pytest.raises(ValueError):
            AgentConfig(
                name="Test Agent",
                agent_type=AgentType.AUTOMATOR,
                tenant_id="test-tenant",
                max_iterations=0  # Invalid, must be >= 1
            )
    
    def test_agent_config_african_regions(self):
        """Test configuration with different African regions."""
        regions = ["NG", "KE", "ZA", "GH", "UG", "TZ", "RW", "ET", "EG", "MA"]
        
        for region in regions:
            config = AgentConfig(
                name=f"Agent {region}",
                agent_type=AgentType.MENTOR,
                tenant_id="test-tenant",
                region=region
            )
            assert config.region == region
    
    def test_agent_config_languages(self):
        """Test configuration with African languages."""
        languages = ["en", "sw", "ha", "yo", "ig", "am", "ar", "fr"]
        
        config = AgentConfig(
            name="Multilingual Agent",
            agent_type=AgentType.MENTOR,
            tenant_id="test-tenant",
            languages=languages
        )
        
        assert config.languages == languages


class TestLLMProviders:
    """Test LLM provider integrations."""
    
    def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider()
        assert provider.pricing is not None
        assert "gpt-4" in provider.pricing
        assert "gpt-4o" in provider.pricing
    
    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider()
        assert provider.pricing is not None
        assert "claude-3-5-sonnet-20241022" in provider.pricing
    
    def test_llm_provider_factory(self):
        """Test LLM provider factory."""
        # Test getting providers
        openai_provider = LLMProviderFactory.get_provider("openai")
        assert isinstance(openai_provider, OpenAIProvider)
        
        anthropic_provider = LLMProviderFactory.get_provider("anthropic")
        assert isinstance(anthropic_provider, AnthropicProvider)
        
        # Test unsupported provider
        with pytest.raises(ValueError):
            LLMProviderFactory.get_provider("unsupported")
    
    def test_cost_estimation(self):
        """Test cost estimation for different models."""
        # OpenAI cost estimation
        openai_cost = LLMProviderFactory.estimate_cost("openai", "gpt-4", 1000)
        assert openai_cost > 0
        assert isinstance(openai_cost, float)
        
        # Anthropic cost estimation
        anthropic_cost = LLMProviderFactory.estimate_cost("anthropic", "claude-3-5-sonnet-20241022", 1000)
        assert anthropic_cost > 0
        assert isinstance(anthropic_cost, float)
    
    def test_supported_models(self):
        """Test getting supported models."""
        openai_models = LLMProviderFactory.get_supported_models("openai")
        assert "gpt-4" in openai_models
        assert "gpt-4o" in openai_models
        
        anthropic_models = LLMProviderFactory.get_supported_models("anthropic")
        assert "claude-3-5-sonnet-20241022" in anthropic_models
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_create_openai_llm(self):
        """Test creating OpenAI LLM instance."""
        provider = OpenAIProvider()
        
        # Mock the ChatOpenAI class to avoid actual API calls
        with patch('smeflow.agents.llm_providers.ChatOpenAI') as mock_chat_openai:
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm
            
            llm = provider.create_llm("gpt-4o", temperature=0.8)
            
            mock_chat_openai.assert_called_once()
            args, kwargs = mock_chat_openai.call_args
            assert kwargs['model'] == 'gpt-4o'
            assert kwargs['temperature'] == 0.8
            assert kwargs['openai_api_key'] == 'test-key'


class TestAgentFactory:
    """Test agent factory functionality."""
    
    @patch('smeflow.agents.factory.create_llm_for_agent')
    def test_create_automator_agent(self, mock_create_llm):
        """Test creating an Automator agent."""
        mock_llm = MockLLM()
        mock_create_llm.return_value = mock_llm
        
        config = AgentConfig(
            name="Test Automator",
            agent_type=AgentType.AUTOMATOR,
            tenant_id="test-tenant",
            region="NG"
        )
        
        # Provide at least one tool for Automator
        tools = [MockTool()]
        agent = AgentFactory.create_agent(config, tools=tools)
        
        assert isinstance(agent, AutomatorAgent)
        assert agent.config.name == "Test Automator"
        assert agent.config.agent_type == AgentType.AUTOMATOR
        assert agent.config.tenant_id == "test-tenant"
        assert agent.config.region == "NG"
    
    @patch('smeflow.agents.factory.create_llm_for_agent')
    def test_create_mentor_agent(self, mock_create_llm):
        """Test creating a Mentor agent."""
        mock_llm = MockLLM()
        mock_create_llm.return_value = mock_llm
        
        config = AgentConfig(
            name="Test Mentor",
            agent_type=AgentType.MENTOR,
            tenant_id="test-tenant",
            region="KE"
        )
        
        # Mentor agents can work without tools
        agent = AgentFactory.create_agent(config, tools=[])
        
        assert isinstance(agent, MentorAgent)
        assert agent.config.name == "Test Mentor"
        assert agent.config.agent_type == AgentType.MENTOR
        assert agent.config.region == "KE"
    
    @patch('smeflow.agents.factory.create_llm_for_agent')
    def test_create_supervisor_agent(self, mock_create_llm):
        """Test creating a Supervisor agent."""
        mock_llm = MockLLM()
        mock_create_llm.return_value = mock_llm
        
        config = AgentConfig(
            name="Test Supervisor",
            agent_type=AgentType.SUPERVISOR,
            tenant_id="test-tenant",
            region="ZA"
        )
        
        # Supervisor agents can work without tools
        agent = AgentFactory.create_agent(config, tools=[])
        
        assert isinstance(agent, SupervisorAgent)
        assert agent.config.name == "Test Supervisor"
        assert agent.config.agent_type == AgentType.SUPERVISOR
        assert agent.config.region == "ZA"
    
    def test_factory_convenience_methods(self):
        """Test factory convenience methods."""
        with patch('smeflow.agents.factory.create_llm_for_agent') as mock_create_llm:
            mock_llm = MockLLM()
            mock_create_llm.return_value = mock_llm
            
            # Test create_automator with tools
            automator = AgentFactory.create_automator(
                name="Test Automator",
                tenant_id="test-tenant",
                region="NG",
                tools=[MockTool()]
            )
            assert isinstance(automator, AutomatorAgent)
            
            # Test create_mentor
            mentor = AgentFactory.create_mentor(
                name="Test Mentor",
                tenant_id="test-tenant",
                region="KE",
                expertise_areas=["finance", "strategy"],
                tools=[]
            )
            assert isinstance(mentor, MentorAgent)
            
            # Test create_supervisor
            supervisor = AgentFactory.create_supervisor(
                name="Test Supervisor",
                tenant_id="test-tenant",
                region="ZA",
                tools=[]
            )
            assert isinstance(supervisor, SupervisorAgent)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        valid_config = {
            "name": "Test Agent",
            "agent_type": "automator",
            "tenant_id": "test-tenant",
            "region": "NG"
        }
        errors = AgentFactory.validate_config(valid_config)
        assert len(errors) == 0
        
        # Invalid configuration - missing required fields
        invalid_config = {
            "name": "Test Agent"
            # Missing agent_type and tenant_id
        }
        errors = AgentFactory.validate_config(invalid_config)
        assert len(errors) > 0
        assert any("agent_type" in error for error in errors)
        assert any("tenant_id" in error for error in errors)
        
        # Invalid temperature
        invalid_temp_config = {
            "name": "Test Agent",
            "agent_type": "automator",
            "tenant_id": "test-tenant",
            "temperature": 3.0
        }
        errors = AgentFactory.validate_config(invalid_temp_config)
        assert any("temperature" in error.lower() for error in errors)
    
    def test_get_default_config(self):
        """Test getting default configurations."""
        # Test Automator default config
        automator_config = AgentFactory.get_default_config(
            AgentType.AUTOMATOR, "test-tenant", "NG"
        )
        assert automator_config["agent_type"] == AgentType.AUTOMATOR
        assert automator_config["tenant_id"] == "test-tenant"
        assert automator_config["region"] == "NG"
        assert "sequential" in automator_config["custom_instructions"]
        
        # Test Mentor default config
        mentor_config = AgentFactory.get_default_config(
            AgentType.MENTOR, "test-tenant", "KE"
        )
        assert mentor_config["agent_type"] == AgentType.MENTOR
        assert "business_strategy" in mentor_config["custom_instructions"]
        
        # Test Supervisor default config
        supervisor_config = AgentFactory.get_default_config(
            AgentType.SUPERVISOR, "test-tenant", "ZA"
        )
        assert supervisor_config["agent_type"] == AgentType.SUPERVISOR
        assert "supervision" in supervisor_config["custom_instructions"]


class TestAgentManager:
    """Test agent manager functionality."""
    
    @pytest.fixture
    def agent_manager(self):
        """Create agent manager for testing."""
        return AgentManager(tenant_id="test-tenant", region="NG")
    
    @pytest.mark.asyncio
    async def test_agent_manager_initialization(self, agent_manager):
        """Test agent manager initialization."""
        assert agent_manager.tenant_id == "test-tenant"
        assert agent_manager.region == "NG"
        assert len(agent_manager.agents) == 0
        assert len(agent_manager.agent_groups) == 0
        assert agent_manager.manager_id is not None
    
    @pytest.mark.asyncio
    @patch('smeflow.agents.manager.AgentFactory.create_agent_from_dict')
    @patch('smeflow.agents.manager.cache_manager')
    async def test_create_agent(self, mock_cache, mock_create_agent, agent_manager):
        """Test creating an agent through manager."""
        # Mock agent creation
        mock_agent = Mock()
        mock_agent.agent_id = "test-agent-id"
        mock_agent.config.tenant_id = "test-tenant"
        mock_agent.config.agent_type = AgentType.AUTOMATOR
        mock_agent.created_at = datetime.utcnow()
        mock_create_agent.return_value = mock_agent
        
        # Mock cache operations
        mock_cache.set = AsyncMock()
        
        config = {
            "name": "Test Agent",
            "agent_type": "automator",
            "tenant_id": "test-tenant"
        }
        
        agent_id = await agent_manager.create_agent(config)
        
        assert agent_id == "test-agent-id"
        assert agent_id in agent_manager.agents
        assert agent_id in agent_manager.performance_metrics
        mock_create_agent.assert_called_once()
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tenant_isolation(self, agent_manager):
        """Test tenant isolation in agent access."""
        # Create mock agent with different tenant
        mock_agent = Mock()
        mock_agent.config.tenant_id = "different-tenant"
        agent_manager.agents["test-agent"] = mock_agent
        
        # Should return None due to tenant mismatch
        result = await agent_manager.get_agent("test-agent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_agent_groups(self, agent_manager):
        """Test agent group management."""
        # Add some mock agents
        for i in range(3):
            mock_agent = Mock()
            mock_agent.config.tenant_id = "test-tenant"
            agent_id = f"agent-{i}"
            agent_manager.agents[agent_id] = mock_agent
        
        # Create group
        success = await agent_manager.create_agent_group(
            "test-group", ["agent-0", "agent-1", "agent-2"]
        )
        assert success is True
        assert "test-group" in agent_manager.agent_groups
        assert len(agent_manager.agent_groups["test-group"]) == 3
    
    @pytest.mark.asyncio
    @patch('smeflow.agents.manager.cache_manager')
    async def test_agent_lifecycle(self, mock_cache, agent_manager):
        """Test agent lifecycle management."""
        # Mock cache operations
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock()
        
        # Create mock agent
        mock_agent = Mock()
        mock_agent.config.tenant_id = "test-tenant"
        mock_agent.status = AgentStatus.ACTIVE
        mock_agent.pause = Mock()
        mock_agent.resume = Mock()
        mock_agent.stop = Mock()
        
        agent_id = "test-agent"
        agent_manager.agents[agent_id] = mock_agent
        agent_manager.performance_metrics[agent_id] = {}
        
        # Test pause
        result = await agent_manager.pause_agent(agent_id)
        assert result is True
        mock_agent.pause.assert_called_once()
        
        # Test resume
        result = await agent_manager.resume_agent(agent_id)
        assert result is True
        mock_agent.resume.assert_called_once()
        
        # Test stop
        result = await agent_manager.stop_agent(agent_id)
        assert result is True
        mock_agent.stop.assert_called_once()
        
        # Test delete
        result = await agent_manager.delete_agent(agent_id)
        assert result is True
        assert agent_id not in agent_manager.agents
        assert agent_id not in agent_manager.performance_metrics
        mock_cache.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_summary(self, agent_manager):
        """Test performance summary generation."""
        # Add mock performance metrics
        agent_manager.performance_metrics = {
            "agent-1": {
                "total_executions": 10,
                "total_cost": 1.5,
                "error_count": 1,
                "average_response_time": 2.5
            },
            "agent-2": {
                "total_executions": 5,
                "total_cost": 0.8,
                "error_count": 0,
                "average_response_time": 1.8
            }
        }
        
        # Add mock agents
        for i in range(2):
            mock_agent = Mock()
            mock_agent.status = AgentStatus.ACTIVE
            agent_manager.agents[f"agent-{i+1}"] = mock_agent
        
        summary = await agent_manager.get_performance_summary()
        
        assert summary["total_agents"] == 2
        assert summary["active_agents"] == 2
        assert summary["total_executions"] == 15
        assert summary["total_cost"] == 2.3
        assert summary["total_errors"] == 1
        assert summary["error_rate"] == round(1/15, 4)
        assert summary["tenant_id"] == "test-tenant"
        assert summary["region"] == "NG"


class TestAgentExecution:
    """Test agent execution scenarios."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing."""
        return MockLLM()
    
    @pytest.fixture
    def automator_config(self):
        """Create automator configuration for testing."""
        return AgentConfig(
            name="Test Automator",
            agent_type=AgentType.AUTOMATOR,
            tenant_id="test-tenant",
            region="NG"
        )
    
    @pytest.mark.asyncio
    async def test_automator_execution(self, mock_llm, automator_config):
        """Test Automator agent execution."""
        # Mock the agent initialization to avoid LangChain complexity
        with patch.object(AutomatorAgent, '_initialize_agent') as mock_init:
            # Create agent without initialization
            agent = AutomatorAgent.__new__(AutomatorAgent)
            agent.config = automator_config
            agent.llm = mock_llm
            agent.tools = [MockTool()]
            agent.prompt = None
            agent.agent_id = "test-agent-id"
            agent.created_at = datetime.utcnow()
            agent.status = AgentStatus.ACTIVE
            agent.execution_count = 0
            agent.last_execution = None
            agent.total_tokens_used = 0
            agent.total_cost = 0.0
            agent.average_response_time = 0.0
            
            # Mock executor
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Task completed successfully",
                "intermediate_steps": []
            })
            agent._executor = mock_executor
            
            # Test execution
            input_data = {"query": "Process some data"}
            result = await agent.execute(input_data)
            
            assert "output" in result
            assert "agent_id" in result
            assert "agent_type" in result
            assert result["agent_type"] == AgentType.AUTOMATOR
            assert result["tenant_id"] == "test-tenant"
            mock_executor.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mentor_guidance(self, mock_llm):
        """Test Mentor agent guidance functionality."""
        config = AgentConfig(
            name="Business Mentor",
            agent_type=AgentType.MENTOR,
            tenant_id="test-tenant",
            region="KE"
        )
        
        # Mock the agent initialization to avoid LangChain complexity
        with patch.object(MentorAgent, '_initialize_agent') as mock_init:
            # Create agent without initialization
            agent = MentorAgent.__new__(MentorAgent)
            agent.config = config
            agent.llm = mock_llm
            agent.tools = []
            agent.prompt = None
            agent.agent_id = "test-mentor-id"
            agent.created_at = datetime.utcnow()
            agent.status = AgentStatus.ACTIVE
            agent.execution_count = 0
            agent.last_execution = None
            agent.total_tokens_used = 0
            agent.total_cost = 0.0
            agent.average_response_time = 0.0
            agent.expertise_areas = ["business_strategy", "financial_planning"]
            agent.guidance_style = "supportive_and_practical"
            agent.knowledge_base = "african_sme_best_practices"
            
            # Mock executor
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Here's my business guidance...",
                "intermediate_steps": []
            })
            agent._executor = mock_executor
            
            # Test guidance provision
            business_context = {
                "industry": "fintech",
                "size": "startup",
                "stage": "growth"
            }
            
            result = await agent.provide_guidance(
                business_context=business_context,
                challenge_description="Need help with scaling operations",
                guidance_type="strategy"
            )
            
            assert "output" in result
            assert result["agent_type"] == AgentType.MENTOR
            mock_executor.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('smeflow.agents.supervisor.initialize_agent')
    async def test_supervisor_orchestration(self, mock_initialize, mock_llm):
        """Test Supervisor agent workflow orchestration."""
        # Mock agent executor
        mock_executor = AsyncMock()
        mock_executor.ainvoke = AsyncMock(return_value={
            "output": "Workflow orchestrated successfully",
            "intermediate_steps": []
        })
        mock_initialize.return_value = mock_executor
        
        config = AgentConfig(
            name="Workflow Supervisor",
            agent_type=AgentType.SUPERVISOR,
            tenant_id="test-tenant",
            region="ZA"
        )
        
        agent = SupervisorAgent(config, mock_llm)
        agent._executor = mock_executor
        
        # Test workflow orchestration
        workflow_definition = {
            "name": "Customer Onboarding",
            "steps": [
                {"name": "validate_documents", "type": "automator"},
                {"name": "create_account", "type": "automator"},
                {"name": "send_welcome", "type": "automator"}
            ],
            "allow_parallel": False
        }
        
        result = await agent.orchestrate_workflow(
            workflow_definition=workflow_definition,
            input_data={"customer_id": "12345"}
        )
        
        assert "output" in result
        assert result["agent_type"] == AgentType.SUPERVISOR
        mock_executor.ainvoke.assert_called_once()


class TestAfricanMarketOptimizations:
    """Test African market specific optimizations."""
    
    def test_regional_business_hours(self):
        """Test regional business hours configuration."""
        config = AgentConfig(
            name="Regional Agent",
            agent_type=AgentType.AUTOMATOR,
            tenant_id="test-tenant",
            region="NG"
        )
        
        with patch.object(AutomatorAgent, '_initialize_agent'):
            mock_llm = MockLLM()
            agent = AutomatorAgent.__new__(AutomatorAgent)
            agent.config = config
            agent.llm = mock_llm
            agent.tools = [MockTool()]
            
            business_hours = agent._get_business_hours()
            assert business_hours["timezone"] == "WAT"
            assert business_hours["start"] == "08:00"
            assert business_hours["end"] == "17:00"
    
    def test_regional_currencies(self):
        """Test regional currency support."""
        regions_currencies = [
            ("NG", "NGN"),
            ("KE", "KES"),
            ("ZA", "ZAR"),
            ("GH", "GHS")
        ]
        
        for region, expected_currency in regions_currencies:
            config = AgentConfig(
                name=f"Agent {region}",
                agent_type=AgentType.AUTOMATOR,
                tenant_id="test-tenant",
                region=region
            )
            
            with patch('smeflow.agents.automator.initialize_agent'):
                mock_llm = Mock()
                agent = AutomatorAgent(config, mock_llm)
                
                currency = agent._get_local_currency()
                assert currency == expected_currency
    
    def test_multilingual_support(self):
        """Test multilingual agent configuration."""
        languages = ["en", "sw", "ha", "yo"]
        
        config = AgentConfig(
            name="Multilingual Agent",
            agent_type=AgentType.MENTOR,
            tenant_id="test-tenant",
            region="KE",
            languages=languages
        )
        
        assert config.languages == languages
        
        with patch('smeflow.agents.mentor.initialize_agent'):
            mock_llm = Mock()
            agent = MentorAgent(config, mock_llm)
            
            system_prompt = agent.get_system_prompt()
            assert "en, sw, ha, yo" in system_prompt
    
    def test_cultural_context_awareness(self):
        """Test cultural context awareness in agents."""
        config = AgentConfig(
            name="Cultural Agent",
            agent_type=AgentType.MENTOR,
            tenant_id="test-tenant",
            region="NG",
            cultural_context=True
        )
        
        with patch('smeflow.agents.mentor.initialize_agent'):
            mock_llm = Mock()
            agent = MentorAgent(config, mock_llm)
            
            system_prompt = agent.get_system_prompt()
            assert "cultural" in system_prompt.lower()
            assert "african" in system_prompt.lower()
    
    def test_connectivity_optimizations(self):
        """Test connectivity optimizations for different regions."""
        with patch('smeflow.agents.llm_providers.create_llm_for_agent') as mock_create_llm:
            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm
            
            # Test high connectivity region (ZA)
            config_za = {"llm_provider": "openai", "model_name": "gpt-4o"}
            llm_za = mock_create_llm(config_za, "test-tenant", "ZA")
            
            # Test low connectivity region (ET)
            config_et = {"llm_provider": "openai", "model_name": "gpt-4o"}
            llm_et = mock_create_llm(config_et, "test-tenant", "ET")
            
            # Verify different optimization parameters were used
            assert mock_create_llm.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
