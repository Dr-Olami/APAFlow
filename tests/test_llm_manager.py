"""
Tests for AGENT-003 LLM Manager with fallback mechanisms and cost tracking.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from smeflow.agents.llm_manager import (
    LLMManager, LLMRequest, LLMResponse, ProviderStrategy
)
from smeflow.database.models import LLMUsage, LLMCache, ProviderHealth
from langchain_core.messages import HumanMessage, SystemMessage


class TestLLMManager:
    """Test cases for LLM Manager."""
    
    @pytest.fixture
    def llm_manager(self):
        """Create LLM manager instance."""
        return LLMManager()
    
    @pytest.fixture
    def sample_request(self):
        """Create sample LLM request."""
        return LLMRequest(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="What is the capital of Nigeria?")
            ],
            tenant_id="test-tenant",
            agent_id="test-agent",
            region="NG",
            strategy=ProviderStrategy.BALANCED
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.all.return_value = []
        session.add = Mock()
        session.commit = Mock()
        session.close = Mock()
        return session
    
    def test_generate_request_hash(self, llm_manager, sample_request):
        """Test request hash generation."""
        hash1 = llm_manager._generate_request_hash(sample_request)
        hash2 = llm_manager._generate_request_hash(sample_request)
        
        # Same request should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        
        # Different request should generate different hash
        different_request = LLMRequest(
            messages=[HumanMessage(content="Different message")],
            tenant_id="test-tenant",
            agent_id="test-agent"
        )
        hash3 = llm_manager._generate_request_hash(different_request)
        assert hash1 != hash3
    
    def test_fallback_configurations(self, llm_manager):
        """Test fallback configurations for different strategies."""
        # Test all strategies have configurations
        for strategy in ProviderStrategy:
            assert strategy in llm_manager.fallback_configs
            config = llm_manager.fallback_configs[strategy]
            assert len(config) > 0
            
            # Each config should have provider and model
            for provider, model in config:
                assert isinstance(provider, str)
                assert isinstance(model, str)
    
    def test_regional_currency_mappings(self, llm_manager):
        """Test regional currency mappings."""
        # Test African regions
        assert llm_manager.regional_currencies["NG"] == "NGN"
        assert llm_manager.regional_currencies["KE"] == "KES"
        assert llm_manager.regional_currencies["ZA"] == "ZAR"
        
        # Test global regions
        assert llm_manager.regional_currencies["US"] == "USD"
        assert llm_manager.regional_currencies["GB"] == "GBP"
        assert llm_manager.regional_currencies["EU"] == "EUR"
    
    def test_check_cache_miss(self, llm_manager, sample_request, mock_db_session):
        """Test cache miss scenario."""
        request_hash = llm_manager._generate_request_hash(sample_request)
        
        result = llm_manager._check_cache(request_hash, "test-tenant", mock_db_session)
        
        assert result is None
        mock_db_session.query.assert_called()
    
    def test_check_cache_hit(self, llm_manager, sample_request, mock_db_session):
        """Test cache hit scenario."""
        request_hash = llm_manager._generate_request_hash(sample_request)
        
        # Mock cache entry
        cache_entry = Mock()
        cache_entry.response_data = {
            "content": "Abuja is the capital of Nigeria.",
            "input_tokens": 20,
            "output_tokens": 10,
            "total_tokens": 30,
            "cost_usd": 0.001,
            "cost_local": 1.65,
            "currency": "NGN"
        }
        cache_entry.provider = "openai"
        cache_entry.model = "gpt-4o"
        cache_entry.hit_count = 0
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = cache_entry
        
        result = llm_manager._check_cache(request_hash, "test-tenant", mock_db_session)
        
        assert result is not None
        assert isinstance(result, LLMResponse)
        assert result.content == "Abuja is the capital of Nigeria."
        assert result.cache_hit is True
        assert result.total_tokens == 30
        assert cache_entry.hit_count == 1
    
    def test_get_fallback_order_healthy_providers(self, llm_manager, mock_db_session):
        """Test fallback order with healthy providers."""
        # Mock healthy provider
        health_record = Mock()
        health_record.provider = "openai"
        health_record.is_healthy = True
        health_record.response_time_avg = 500
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [health_record]
        
        order = llm_manager._get_fallback_order(ProviderStrategy.BALANCED, "NG", mock_db_session)
        
        assert len(order) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in order)
    
    def test_get_fallback_order_unhealthy_providers(self, llm_manager, mock_db_session):
        """Test fallback order with unhealthy providers."""
        # Mock unhealthy provider
        health_record = Mock()
        health_record.provider = "openai"
        health_record.is_healthy = False
        health_record.response_time_avg = 2000
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [health_record]
        
        order = llm_manager._get_fallback_order(ProviderStrategy.BALANCED, "NG", mock_db_session)
        
        # Unhealthy providers should be deprioritized
        assert len(order) > 0
    
    @patch('smeflow.agents.llm_manager.LLMProviderFactory')
    async def test_execute_with_provider_success(self, mock_factory, llm_manager, sample_request, mock_db_session):
        """Test successful execution with provider."""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Abuja is the capital of Nigeria."
        mock_llm.ainvoke.return_value = mock_response
        
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.estimate_cost.return_value = 0.001
        
        request_hash = "test-hash"
        
        result = await llm_manager._execute_with_provider(
            sample_request, "openai", "gpt-4o", request_hash, mock_db_session
        )
        
        assert isinstance(result, LLMResponse)
        assert result.content == "Abuja is the capital of Nigeria."
        assert result.provider == "openai"
        assert result.model == "gpt-4o"
        assert result.cache_hit is False
        assert result.cost_usd == 0.001
        
        # Verify database record was created
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_cache_response(self, llm_manager, mock_db_session):
        """Test response caching."""
        response = LLMResponse(
            content="Test response",
            provider="openai",
            model="gpt-4o",
            input_tokens=20,
            output_tokens=10,
            total_tokens=30,
            cost_usd=0.001,
            cost_local=1.65,
            currency="NGN",
            response_time_ms=500,
            cache_hit=False,
            request_hash="test-hash"
        )
        
        llm_manager._cache_response("test-hash", response, "test-tenant", mock_db_session)
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        
        # Verify cache entry was created with correct data
        call_args = mock_db_session.add.call_args[0][0]
        assert hasattr(call_args, 'cache_key')
        assert hasattr(call_args, 'tenant_id')
        assert hasattr(call_args, 'response_data')
    
    def test_update_provider_health_success(self, llm_manager, mock_db_session):
        """Test provider health update on success."""
        # Mock existing health record
        health_record = Mock()
        health_record.success_count = 10
        health_record.error_count = 2
        health_record.response_time_avg = 600
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = health_record
        
        llm_manager._update_provider_health("openai", "NG", True, 500, mock_db_session)
        
        assert health_record.success_count == 11
        assert health_record.response_time_avg == 580  # Updated average
        assert health_record.last_success is not None
        mock_db_session.commit.assert_called()
    
    def test_update_provider_health_failure(self, llm_manager, mock_db_session):
        """Test provider health update on failure."""
        # Mock existing health record
        health_record = Mock()
        health_record.success_count = 10
        health_record.error_count = 2
        health_record.response_time_avg = 600
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = health_record
        
        llm_manager._update_provider_health("openai", "NG", False, None, mock_db_session)
        
        assert health_record.error_count == 3
        assert health_record.last_error is not None
        mock_db_session.commit.assert_called()
    
    def test_update_provider_health_new_provider(self, llm_manager, mock_db_session):
        """Test provider health update for new provider."""
        # No existing health record
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        llm_manager._update_provider_health("anthropic", "NG", True, 400, mock_db_session)
        
        # Should create new health record
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @patch('smeflow.agents.llm_manager.get_db_session')
    def test_get_usage_analytics_no_data(self, mock_get_db, llm_manager):
        """Test usage analytics with no data."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db
        
        result = llm_manager.get_usage_analytics("test-tenant")
        
        assert result["total_requests"] == 0
        assert result["total_tokens"] == 0
        assert result["total_cost_usd"] == 0.0
        assert result["cache_hit_rate"] == 0.0
        mock_db.close.assert_called()
    
    @patch('smeflow.agents.llm_manager.get_db_session')
    def test_get_usage_analytics_with_data(self, mock_get_db, llm_manager):
        """Test usage analytics with data."""
        # Mock usage records
        usage1 = Mock()
        usage1.total_tokens = 100
        usage1.cost_usd = 0.01
        usage1.cache_hit = False
        usage1.response_time_ms = 500
        usage1.provider = "openai"
        usage1.model = "gpt-4o"
        
        usage2 = Mock()
        usage2.total_tokens = 50
        usage2.cost_usd = 0.005
        usage2.cache_hit = True
        usage2.response_time_ms = 0
        usage2.provider = "openai"
        usage2.model = "gpt-4o"
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [usage1, usage2]
        mock_get_db.return_value = mock_db
        
        result = llm_manager.get_usage_analytics("test-tenant")
        
        assert result["total_requests"] == 2
        assert result["total_tokens"] == 150
        assert result["total_cost_usd"] == 0.015
        assert result["cache_hit_rate"] == 0.5
        assert result["avg_response_time"] == 500
        assert "openai" in result["provider_breakdown"]
        assert "openai:gpt-4o" in result["model_breakdown"]
        mock_db.close.assert_called()


class TestLLMRequest:
    """Test cases for LLM Request data structure."""
    
    def test_llm_request_creation(self):
        """Test LLM request creation with defaults."""
        messages = [HumanMessage(content="Test message")]
        request = LLMRequest(
            messages=messages,
            tenant_id="test-tenant"
        )
        
        assert request.messages == messages
        assert request.tenant_id == "test-tenant"
        assert request.agent_id is None
        assert request.region == "NG"
        assert request.strategy == ProviderStrategy.BALANCED
        assert request.max_tokens is None
        assert request.temperature == 0.7
    
    def test_llm_request_with_all_params(self):
        """Test LLM request creation with all parameters."""
        messages = [HumanMessage(content="Test message")]
        request = LLMRequest(
            messages=messages,
            tenant_id="test-tenant",
            agent_id="test-agent",
            region="KE",
            strategy=ProviderStrategy.COST_OPTIMIZED,
            max_tokens=1000,
            temperature=0.5
        )
        
        assert request.agent_id == "test-agent"
        assert request.region == "KE"
        assert request.strategy == ProviderStrategy.COST_OPTIMIZED
        assert request.max_tokens == 1000
        assert request.temperature == 0.5


class TestLLMResponse:
    """Test cases for LLM Response data structure."""
    
    def test_llm_response_creation(self):
        """Test LLM response creation."""
        response = LLMResponse(
            content="Test response",
            provider="openai",
            model="gpt-4o",
            input_tokens=20,
            output_tokens=10,
            total_tokens=30,
            cost_usd=0.001,
            cost_local=1.65,
            currency="NGN",
            response_time_ms=500,
            cache_hit=False,
            request_hash="test-hash"
        )
        
        assert response.content == "Test response"
        assert response.provider == "openai"
        assert response.model == "gpt-4o"
        assert response.total_tokens == 30
        assert response.cost_usd == 0.001
        assert response.cost_local == 1.65
        assert response.currency == "NGN"
        assert response.response_time_ms == 500
        assert response.cache_hit is False


class TestProviderStrategy:
    """Test cases for Provider Strategy enum."""
    
    def test_provider_strategy_values(self):
        """Test provider strategy enum values."""
        assert ProviderStrategy.COST_OPTIMIZED.value == "cost_optimized"
        assert ProviderStrategy.QUALITY_FOCUSED.value == "quality_focused"
        assert ProviderStrategy.BALANCED.value == "balanced"
        assert ProviderStrategy.FASTEST.value == "fastest"
    
    def test_provider_strategy_count(self):
        """Test provider strategy count."""
        strategies = list(ProviderStrategy)
        assert len(strategies) == 4


@pytest.mark.asyncio
class TestLLMManagerIntegration:
    """Integration tests for LLM Manager."""
    
    @pytest.fixture
    def llm_manager(self):
        """Create LLM manager instance."""
        return LLMManager()
    
    @patch('smeflow.agents.llm_manager.get_db_session')
    @patch('smeflow.agents.llm_manager.LLMProviderFactory')
    async def test_execute_request_with_fallback(self, mock_factory, mock_get_db, llm_manager):
        """Test request execution with provider fallback."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db
        
        # Mock first provider failure, second provider success
        mock_llm1 = AsyncMock()
        mock_llm1.ainvoke.side_effect = Exception("Provider 1 failed")
        
        mock_llm2 = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Success response"
        mock_llm2.ainvoke.return_value = mock_response
        
        mock_factory.create_llm.side_effect = [mock_llm1, mock_llm2]
        mock_factory.estimate_cost.return_value = 0.001
        
        request = LLMRequest(
            messages=[HumanMessage(content="Test message")],
            tenant_id="test-tenant",
            strategy=ProviderStrategy.BALANCED
        )
        
        result = await llm_manager.execute_request(request, mock_db)
        
        assert isinstance(result, LLMResponse)
        assert result.content == "Success response"
        
        # Should have tried both providers
        assert mock_factory.create_llm.call_count == 2
    
    @patch('smeflow.agents.llm_manager.get_db_session')
    async def test_execute_request_all_providers_fail(self, mock_get_db, llm_manager):
        """Test request execution when all providers fail."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db
        
        with patch('smeflow.agents.llm_manager.LLMProviderFactory') as mock_factory:
            # Mock all providers failing
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("All providers failed")
            mock_factory.create_llm.return_value = mock_llm
            
            request = LLMRequest(
                messages=[HumanMessage(content="Test message")],
                tenant_id="test-tenant"
            )
            
            with pytest.raises(Exception, match="All LLM providers failed"):
                await llm_manager.execute_request(request, mock_db)


if __name__ == "__main__":
    pytest.main([__file__])
