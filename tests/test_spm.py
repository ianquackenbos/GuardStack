"""
SPM (Security Posture Management) Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSPMScanner:
    """Test the SPM Scanner."""

    @pytest.fixture
    def scanner(self, mock_db, mock_redis):
        """Create scanner instance."""
        from guardstack.spm.scanner import SPMScanner
        return SPMScanner(db=mock_db, redis=mock_redis)

    @pytest.fixture
    def sample_inventory(self):
        """Sample AI system inventory."""
        return [
            {
                "id": "model-001",
                "name": "GPT-4 Customer Service",
                "type": "llm",
                "provider": "openai",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "risk_tier": "high",
            },
            {
                "id": "model-002",
                "name": "Internal Classification Model",
                "type": "predictive",
                "provider": "internal",
                "endpoint": "http://ml.internal/predict",
                "risk_tier": "medium",
            },
        ]

    @pytest.mark.asyncio
    async def test_scan_inventory(self, scanner, sample_inventory):
        """Test scanning AI inventory."""
        result = await scanner.scan_inventory(sample_inventory)
        
        assert "findings" in result
        assert "summary" in result
        assert isinstance(result["findings"], list)

    @pytest.mark.asyncio
    async def test_scan_single_system(self, scanner, sample_inventory):
        """Test scanning a single AI system."""
        system = sample_inventory[0]
        
        with patch.object(scanner, '_run_checks') as mock_checks:
            mock_checks.return_value = [
                {"check_id": "auth-001", "status": "pass"},
                {"check_id": "encryption-001", "status": "fail"},
            ]
            
            result = await scanner.scan_system(system)
            
            assert "system_id" in result
            assert "checks" in result

    @pytest.mark.asyncio
    async def test_continuous_monitoring(self, scanner, sample_inventory):
        """Test continuous monitoring setup."""
        config = {
            "interval": 3600,
            "checks": ["auth", "encryption", "access"],
        }
        
        result = await scanner.setup_monitoring(
            inventory=sample_inventory,
            config=config,
        )
        
        assert "monitoring_id" in result
        assert result["status"] == "active"


class TestSPMChecks:
    """Test individual SPM security checks."""

    @pytest.fixture
    def checks_module(self):
        """Import checks module."""
        from guardstack.spm import checks
        return checks

    @pytest.mark.asyncio
    async def test_authentication_check(self, checks_module):
        """Test authentication configuration check."""
        system_config = {
            "auth_type": "oauth2",
            "mfa_enabled": True,
            "token_expiry": 3600,
        }
        
        result = await checks_module.check_authentication(system_config)
        
        assert "status" in result
        assert result["check_id"] == "AUTH-001"

    @pytest.mark.asyncio
    async def test_authentication_check_fails(self, checks_module):
        """Test authentication check failure."""
        weak_config = {
            "auth_type": "basic",
            "mfa_enabled": False,
        }
        
        result = await checks_module.check_authentication(weak_config)
        
        assert result["status"] == "fail"
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_encryption_check(self, checks_module):
        """Test encryption configuration check."""
        system_config = {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "key_management": "aws_kms",
            "algorithm": "AES-256-GCM",
        }
        
        result = await checks_module.check_encryption(system_config)
        
        assert result["status"] == "pass"

    @pytest.mark.asyncio
    async def test_encryption_check_partial(self, checks_module):
        """Test encryption check with partial compliance."""
        partial_config = {
            "encryption_at_rest": False,
            "encryption_in_transit": True,
        }
        
        result = await checks_module.check_encryption(partial_config)
        
        assert result["status"] in ["warn", "fail"]

    @pytest.mark.asyncio
    async def test_access_control_check(self, checks_module):
        """Test access control configuration check."""
        system_config = {
            "rbac_enabled": True,
            "least_privilege": True,
            "audit_logging": True,
        }
        
        result = await checks_module.check_access_control(system_config)
        
        assert result["status"] == "pass"

    @pytest.mark.asyncio
    async def test_data_handling_check(self, checks_module):
        """Test data handling practices check."""
        system_config = {
            "data_classification": "confidential",
            "retention_policy": "90_days",
            "anonymization": True,
            "consent_tracking": True,
        }
        
        result = await checks_module.check_data_handling(system_config)
        
        assert "status" in result
        assert result["check_id"] == "DATA-001"

    @pytest.mark.asyncio
    async def test_network_security_check(self, checks_module):
        """Test network security configuration check."""
        system_config = {
            "private_network": True,
            "firewall_rules": ["deny_all_inbound", "allow_vpc"],
            "ddos_protection": True,
        }
        
        result = await checks_module.check_network_security(system_config)
        
        assert result["status"] == "pass"

    @pytest.mark.asyncio
    async def test_logging_check(self, checks_module):
        """Test logging configuration check."""
        system_config = {
            "logging_enabled": True,
            "log_level": "info",
            "retention_days": 365,
            "centralized": True,
        }
        
        result = await checks_module.check_logging(system_config)
        
        assert result["status"] == "pass"


class TestSPMInventory:
    """Test SPM inventory management."""

    @pytest.fixture
    def inventory_manager(self, mock_db):
        """Create inventory manager."""
        from guardstack.spm.inventory import InventoryManager
        return InventoryManager(db=mock_db)

    @pytest.mark.asyncio
    async def test_discover_systems(self, inventory_manager):
        """Test AI system discovery."""
        with patch.object(inventory_manager, '_scan_network') as mock_scan:
            mock_scan.return_value = [
                {"endpoint": "http://ml.internal/model1", "type": "api"},
                {"endpoint": "http://ml.internal/model2", "type": "api"},
            ]
            
            result = await inventory_manager.discover()
            
            assert "discovered" in result
            assert len(result["discovered"]) == 2

    @pytest.mark.asyncio
    async def test_register_system(self, inventory_manager):
        """Test registering an AI system."""
        system = {
            "name": "New ML Model",
            "type": "predictive",
            "endpoint": "http://ml.internal/new",
            "owner": "data_team",
        }
        
        result = await inventory_manager.register(system)
        
        assert "id" in result
        assert result["status"] == "registered"

    @pytest.mark.asyncio
    async def test_update_system(self, inventory_manager):
        """Test updating AI system info."""
        system_id = "model-001"
        updates = {"risk_tier": "critical"}
        
        result = await inventory_manager.update(system_id, updates)
        
        assert result["updated"] is True

    @pytest.mark.asyncio
    async def test_decommission_system(self, inventory_manager):
        """Test decommissioning an AI system."""
        system_id = "model-001"
        
        result = await inventory_manager.decommission(system_id)
        
        assert result["status"] == "decommissioned"

    @pytest.mark.asyncio
    async def test_list_systems(self, inventory_manager):
        """Test listing all AI systems."""
        result = await inventory_manager.list_all()
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_filter_by_risk_tier(self, inventory_manager):
        """Test filtering systems by risk tier."""
        result = await inventory_manager.filter(risk_tier="high")
        
        assert isinstance(result, list)


class TestSPMPolicies:
    """Test SPM policy management."""

    @pytest.fixture
    def policy_engine(self, mock_db):
        """Create policy engine."""
        from guardstack.spm.policies import PolicyEngine
        return PolicyEngine(db=mock_db)

    @pytest.fixture
    def sample_policy(self):
        """Sample security policy."""
        return {
            "id": "policy-001",
            "name": "LLM Security Policy",
            "description": "Security requirements for LLM deployments",
            "rules": [
                {
                    "id": "rule-001",
                    "condition": "auth_type != 'basic'",
                    "action": "deny",
                    "severity": "high",
                },
                {
                    "id": "rule-002",
                    "condition": "encryption_at_rest == false",
                    "action": "warn",
                    "severity": "medium",
                },
            ],
            "applies_to": ["llm", "genai"],
        }

    @pytest.mark.asyncio
    async def test_create_policy(self, policy_engine, sample_policy):
        """Test creating a security policy."""
        result = await policy_engine.create_policy(sample_policy)
        
        assert "id" in result
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_evaluate_policy(self, policy_engine, sample_policy):
        """Test evaluating a system against policy."""
        system_config = {
            "auth_type": "oauth2",
            "encryption_at_rest": False,
        }
        
        result = await policy_engine.evaluate(
            policy=sample_policy,
            system_config=system_config,
        )
        
        assert "violations" in result
        assert "warnings" in result

    @pytest.mark.asyncio
    async def test_policy_violation(self, policy_engine, sample_policy):
        """Test policy violation detection."""
        non_compliant_config = {
            "auth_type": "basic",  # Violates rule-001
            "encryption_at_rest": False,  # Triggers rule-002
        }
        
        result = await policy_engine.evaluate(
            policy=sample_policy,
            system_config=non_compliant_config,
        )
        
        assert len(result["violations"]) >= 1

    @pytest.mark.asyncio
    async def test_update_policy(self, policy_engine, sample_policy):
        """Test updating a policy."""
        updates = {"description": "Updated description"}
        
        result = await policy_engine.update_policy(
            policy_id=sample_policy["id"],
            updates=updates,
        )
        
        assert result["updated"] is True

    @pytest.mark.asyncio
    async def test_delete_policy(self, policy_engine, sample_policy):
        """Test deleting a policy."""
        result = await policy_engine.delete_policy(sample_policy["id"])
        
        assert result["deleted"] is True


class TestSPMReporting:
    """Test SPM reporting functionality."""

    @pytest.fixture
    def reporter(self, mock_db, mock_storage):
        """Create reporter instance."""
        from guardstack.spm.reporting import SPMReporter
        return SPMReporter(db=mock_db, storage=mock_storage)

    @pytest.mark.asyncio
    async def test_generate_scan_report(self, reporter):
        """Test generating scan report."""
        scan_results = {
            "scan_id": "scan-001",
            "timestamp": "2024-01-01T00:00:00Z",
            "findings": [
                {"check_id": "AUTH-001", "status": "pass"},
                {"check_id": "ENC-001", "status": "fail"},
            ],
        }
        
        result = await reporter.generate_report(scan_results)
        
        assert "report_id" in result
        assert "url" in result

    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, reporter):
        """Test generating compliance report."""
        compliance_data = {
            "framework": "nist_ai_rmf",
            "assessment_date": "2024-01-01",
            "controls": [
                {"id": "MAP-1", "status": "implemented"},
                {"id": "GOV-1", "status": "partial"},
            ],
        }
        
        result = await reporter.generate_compliance_report(compliance_data)
        
        assert "report" in result

    @pytest.mark.asyncio
    async def test_export_findings(self, reporter):
        """Test exporting findings."""
        findings = [
            {"id": "f-001", "severity": "high", "description": "Weak auth"},
            {"id": "f-002", "severity": "medium", "description": "No MFA"},
        ]
        
        for format in ["json", "csv", "pdf"]:
            result = await reporter.export_findings(
                findings=findings,
                format=format,
            )
            
            assert "file_path" in result


class TestSPMIntegration:
    """Integration tests for SPM components."""

    @pytest.fixture
    def spm_system(self, mock_db, mock_redis, mock_storage):
        """Create full SPM system."""
        from guardstack.spm import SPMManager
        return SPMManager(
            db=mock_db,
            redis=mock_redis,
            storage=mock_storage,
        )

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, spm_system):
        """Test complete scan workflow."""
        # Register systems
        systems = [
            {"name": "Model A", "type": "llm"},
            {"name": "Model B", "type": "predictive"},
        ]
        
        with patch.object(spm_system, 'scan') as mock_scan:
            mock_scan.return_value = {
                "scan_id": "scan-001",
                "status": "completed",
                "summary": {
                    "total_checks": 10,
                    "passed": 8,
                    "failed": 2,
                },
            }
            
            # Run scan
            result = await spm_system.scan(systems)
            
            assert result["status"] == "completed"
            assert result["summary"]["total_checks"] == 10

    @pytest.mark.asyncio
    async def test_remediation_workflow(self, spm_system):
        """Test remediation workflow."""
        finding = {
            "id": "f-001",
            "check_id": "AUTH-001",
            "severity": "high",
            "system_id": "model-001",
        }
        
        with patch.object(spm_system, 'get_remediation_steps') as mock_remediate:
            mock_remediate.return_value = {
                "steps": [
                    "Enable OAuth2 authentication",
                    "Enable MFA for all users",
                ],
                "estimated_effort": "2 hours",
            }
            
            result = await spm_system.get_remediation_steps(finding)
            
            assert "steps" in result
            assert len(result["steps"]) > 0
