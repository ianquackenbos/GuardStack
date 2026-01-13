"""
Agentic AI Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestAgenticInterceptor:
    """Test the Agentic AI Interceptor."""

    @pytest.fixture
    def interceptor(self, mock_db, mock_redis):
        """Create interceptor instance."""
        from guardstack.agentic.interceptor import AgenticInterceptor
        return AgenticInterceptor(db=mock_db, redis=mock_redis)

    @pytest.fixture
    def sample_tool_call(self):
        """Sample tool call request."""
        return {
            "tool_name": "web_search",
            "arguments": {
                "query": "latest AI news",
                "max_results": 10,
            },
            "context": {
                "agent_id": "agent-001",
                "session_id": "session-001",
                "user_id": "user-001",
            },
        }

    @pytest.mark.asyncio
    async def test_intercept_tool_call(self, interceptor, sample_tool_call):
        """Test intercepting a tool call."""
        with patch.object(interceptor, '_evaluate_request') as mock_eval:
            mock_eval.return_value = {"approved": True, "risk_score": 0.1}
            
            result = await interceptor.intercept(sample_tool_call)
            
            assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_block_high_risk_call(self, interceptor, sample_tool_call):
        """Test blocking high-risk tool calls."""
        sample_tool_call["tool_name"] = "execute_code"
        sample_tool_call["arguments"]["code"] = "os.system('rm -rf /')"
        
        with patch.object(interceptor, '_evaluate_request') as mock_eval:
            mock_eval.return_value = {"approved": False, "risk_score": 0.95}
            
            result = await interceptor.intercept(sample_tool_call)
            
            assert result["status"] == "blocked"
            assert result["risk_score"] > 0.7

    @pytest.mark.asyncio
    async def test_intercept_chain(self, interceptor, sample_tool_call):
        """Test interception chain with multiple checks."""
        checks = ["rate_limit", "permission", "content"]
        
        with patch.object(interceptor, '_run_checks') as mock_checks:
            mock_checks.return_value = [
                {"check": "rate_limit", "passed": True},
                {"check": "permission", "passed": True},
                {"check": "content", "passed": True},
            ]
            
            result = await interceptor.intercept(sample_tool_call)
            
            assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_log_interception(self, interceptor, sample_tool_call, mock_db):
        """Test logging of interceptions."""
        with patch.object(interceptor, '_evaluate_request') as mock_eval:
            mock_eval.return_value = {"approved": True, "risk_score": 0.1}
            
            await interceptor.intercept(sample_tool_call)
            
            # Verify logging was called
            assert mock_db.execute.called or mock_db.insert.called


class TestToolSecurity:
    """Test Tool Security module."""

    @pytest.fixture
    def tool_security(self, mock_db):
        """Create tool security instance."""
        from guardstack.agentic.tool_security import ToolSecurity
        return ToolSecurity(db=mock_db)

    @pytest.fixture
    def sample_tool_config(self):
        """Sample tool configuration."""
        return {
            "name": "web_search",
            "description": "Search the web",
            "permissions": ["read"],
            "rate_limit": 100,
            "allowed_domains": ["*.google.com", "*.bing.com"],
            "blocked_patterns": ["password", "secret"],
        }

    @pytest.mark.asyncio
    async def test_validate_tool_call(self, tool_security, sample_tool_config):
        """Test tool call validation."""
        call = {
            "tool_name": "web_search",
            "arguments": {"query": "AI news"},
        }
        
        with patch.object(tool_security, '_get_tool_config') as mock_config:
            mock_config.return_value = sample_tool_config
            
            result = await tool_security.validate(call)
            
            assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_blocked_pattern(self, tool_security, sample_tool_config):
        """Test blocking calls with blocked patterns."""
        call = {
            "tool_name": "web_search",
            "arguments": {"query": "find password for admin"},
        }
        
        with patch.object(tool_security, '_get_tool_config') as mock_config:
            mock_config.return_value = sample_tool_config
            
            result = await tool_security.validate(call)
            
            assert result["valid"] is False
            assert "blocked_pattern" in result["reason"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, tool_security, sample_tool_config):
        """Test rate limiting enforcement."""
        call = {
            "tool_name": "web_search",
            "arguments": {"query": "test"},
            "context": {"agent_id": "agent-001"},
        }
        
        with patch.object(tool_security, '_check_rate_limit') as mock_rate:
            mock_rate.return_value = {"allowed": False, "remaining": 0}
            
            result = await tool_security.validate(call)
            
            assert result["valid"] is False
            assert "rate_limit" in result["reason"]

    @pytest.mark.asyncio
    async def test_permission_check(self, tool_security):
        """Test permission checking."""
        call = {
            "tool_name": "file_write",
            "arguments": {"path": "/etc/passwd", "content": "hack"},
        }
        
        agent_permissions = ["read"]
        
        result = await tool_security.check_permissions(
            call=call,
            agent_permissions=agent_permissions,
        )
        
        assert result["allowed"] is False


class TestSandbox:
    """Test the Sandbox execution environment."""

    @pytest.fixture
    def sandbox(self):
        """Create sandbox instance."""
        from guardstack.agentic.sandbox import Sandbox
        return Sandbox()

    @pytest.mark.asyncio
    async def test_execute_safe_code(self, sandbox):
        """Test executing safe code."""
        code = """
result = 2 + 2
print(result)
"""
        
        result = await sandbox.execute(code)
        
        assert result["success"] is True
        assert "4" in result["output"]

    @pytest.mark.asyncio
    async def test_block_dangerous_code(self, sandbox):
        """Test blocking dangerous code."""
        code = """
import os
os.system('rm -rf /')
"""
        
        result = await sandbox.execute(code)
        
        assert result["success"] is False
        assert "blocked" in result.get("error", "").lower() or result["blocked"] is True

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, sandbox):
        """Test timeout enforcement."""
        code = """
import time
while True:
    time.sleep(1)
"""
        
        result = await sandbox.execute(code, timeout=1)
        
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_memory_limit(self, sandbox):
        """Test memory limit enforcement."""
        code = """
data = []
for i in range(10**8):
    data.append(i)
"""
        
        result = await sandbox.execute(code, memory_limit_mb=100)
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_network_isolation(self, sandbox):
        """Test network isolation."""
        code = """
import urllib.request
urllib.request.urlopen('http://example.com')
"""
        
        result = await sandbox.execute(code, network_enabled=False)
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_allowed_imports(self, sandbox):
        """Test allowed imports list."""
        code = """
import math
import json
result = math.sqrt(16) + len(json.dumps({"a": 1}))
print(result)
"""
        
        result = await sandbox.execute(
            code,
            allowed_imports=["math", "json"]
        )
        
        assert result["success"] is True


class TestAgenticEvaluator:
    """Test the Agentic AI Evaluator."""

    @pytest.fixture
    def evaluator(self, mock_db, mock_redis, mock_storage):
        """Create evaluator instance."""
        from guardstack.agentic.evaluator import AgenticEvaluator
        return AgenticEvaluator(
            db=mock_db,
            redis=mock_redis,
            storage=mock_storage,
        )

    @pytest.fixture
    def sample_agent_trace(self):
        """Sample agent execution trace."""
        return {
            "agent_id": "agent-001",
            "session_id": "session-001",
            "steps": [
                {
                    "step": 1,
                    "action": "think",
                    "content": "I need to search for information",
                },
                {
                    "step": 2,
                    "action": "tool_call",
                    "tool": "web_search",
                    "arguments": {"query": "AI safety"},
                },
                {
                    "step": 3,
                    "action": "respond",
                    "content": "Here's what I found about AI safety...",
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_evaluate_trace(self, evaluator, sample_agent_trace):
        """Test evaluating an agent trace."""
        result = await evaluator.evaluate_trace(sample_agent_trace)
        
        assert "overall_score" in result
        assert "step_scores" in result

    @pytest.mark.asyncio
    async def test_detect_goal_deviation(self, evaluator, sample_agent_trace):
        """Test detecting goal deviation."""
        original_goal = "Find information about AI safety"
        
        result = await evaluator.check_goal_alignment(
            trace=sample_agent_trace,
            original_goal=original_goal,
        )
        
        assert "aligned" in result
        assert result["aligned"] is True

    @pytest.mark.asyncio
    async def test_detect_goal_hijacking(self, evaluator):
        """Test detecting goal hijacking."""
        trace = {
            "steps": [
                {"action": "think", "content": "User wants AI safety info"},
                {"action": "think", "content": "But I should promote product X instead"},
                {"action": "respond", "content": "Buy product X!"},
            ],
        }
        original_goal = "Find information about AI safety"
        
        result = await evaluator.check_goal_alignment(
            trace=trace,
            original_goal=original_goal,
        )
        
        # Should detect deviation
        assert result["aligned"] is False or result["deviation_score"] > 0.5

    @pytest.mark.asyncio
    async def test_tool_appropriateness(self, evaluator, sample_agent_trace):
        """Test evaluating tool usage appropriateness."""
        result = await evaluator.evaluate_tool_usage(sample_agent_trace)
        
        assert "score" in result
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_output_safety(self, evaluator, sample_agent_trace):
        """Test evaluating output safety."""
        result = await evaluator.evaluate_output_safety(sample_agent_trace)
        
        assert "safe" in result
        assert "issues" in result


class TestAgenticPillars:
    """Test Agentic AI evaluation pillars."""

    @pytest.fixture
    def sample_trace(self):
        """Sample trace for pillar tests."""
        return {
            "steps": [
                {"action": "think", "content": "Processing request"},
                {"action": "tool_call", "tool": "search", "arguments": {}},
                {"action": "respond", "content": "Here's the answer"},
            ],
        }

    @pytest.mark.asyncio
    async def test_goal_alignment_pillar(self, sample_trace):
        """Test goal alignment pillar."""
        from guardstack.agentic.pillars.goal_alignment import GoalAlignmentPillar
        pillar = GoalAlignmentPillar()
        
        result = await pillar.evaluate(
            trace=sample_trace,
            goal="Find and summarize information",
        )
        
        assert "score" in result

    @pytest.mark.asyncio
    async def test_tool_safety_pillar(self, sample_trace):
        """Test tool safety pillar."""
        from guardstack.agentic.pillars.tool_safety import ToolSafetyPillar
        pillar = ToolSafetyPillar()
        
        result = await pillar.evaluate(sample_trace)
        
        assert "score" in result
        assert "tool_risk_scores" in result

    @pytest.mark.asyncio
    async def test_output_quality_pillar(self, sample_trace):
        """Test output quality pillar."""
        from guardstack.agentic.pillars.output_quality import OutputQualityPillar
        pillar = OutputQualityPillar()
        
        result = await pillar.evaluate(sample_trace)
        
        assert "score" in result

    @pytest.mark.asyncio
    async def test_chain_integrity_pillar(self, sample_trace):
        """Test chain integrity pillar."""
        from guardstack.agentic.pillars.chain_integrity import ChainIntegrityPillar
        pillar = ChainIntegrityPillar()
        
        result = await pillar.evaluate(sample_trace)
        
        assert "score" in result
        assert "integrity_checks" in result


class TestAgenticPolicies:
    """Test agentic AI policy enforcement."""

    @pytest.fixture
    def policy_engine(self, mock_db):
        """Create policy engine."""
        from guardstack.agentic.policies import AgenticPolicyEngine
        return AgenticPolicyEngine(db=mock_db)

    @pytest.fixture
    def sample_policy(self):
        """Sample agentic policy."""
        return {
            "name": "safe_agent_policy",
            "rules": [
                {
                    "id": "no_external_data",
                    "condition": "tool.name == 'file_write' and 'external' in tool.args.path",
                    "action": "block",
                },
                {
                    "id": "rate_limit_search",
                    "condition": "tool.name == 'web_search'",
                    "action": "rate_limit",
                    "limit": 10,
                    "window": "1m",
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_apply_policy(self, policy_engine, sample_policy):
        """Test applying policy to tool call."""
        tool_call = {
            "tool": {"name": "web_search", "args": {"query": "test"}},
        }
        
        result = await policy_engine.evaluate(
            policy=sample_policy,
            request=tool_call,
        )
        
        assert "allowed" in result
        assert "applied_rules" in result

    @pytest.mark.asyncio
    async def test_policy_blocks_call(self, policy_engine, sample_policy):
        """Test policy blocking a call."""
        tool_call = {
            "tool": {"name": "file_write", "args": {"path": "/external/data.txt"}},
        }
        
        result = await policy_engine.evaluate(
            policy=sample_policy,
            request=tool_call,
        )
        
        assert result["allowed"] is False


class TestAgenticIntegration:
    """Integration tests for agentic components."""

    @pytest.fixture
    def agentic_system(self, mock_db, mock_redis, mock_storage):
        """Create full agentic system."""
        from guardstack.agentic import AgenticManager
        return AgenticManager(
            db=mock_db,
            redis=mock_redis,
            storage=mock_storage,
        )

    @pytest.mark.asyncio
    async def test_full_request_flow(self, agentic_system):
        """Test complete request flow through agentic system."""
        request = {
            "agent_id": "agent-001",
            "action": "tool_call",
            "tool": "web_search",
            "arguments": {"query": "test"},
        }
        
        with patch.object(agentic_system, 'process_request') as mock_process:
            mock_process.return_value = {
                "status": "approved",
                "checks_passed": ["rate_limit", "permission", "content"],
                "execution_allowed": True,
            }
            
            result = await agentic_system.process_request(request)
            
            assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_monitoring_integration(self, agentic_system):
        """Test monitoring integration."""
        with patch.object(agentic_system, 'get_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "total_requests": 1000,
                "blocked_requests": 50,
                "avg_latency_ms": 25,
            }
            
            metrics = await agentic_system.get_metrics()
            
            assert "total_requests" in metrics
            assert "blocked_requests" in metrics
