"""
Predictive AI Evaluator Tests
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch


class TestPredictiveAIEvaluator:
    """Test the Predictive AI Evaluator."""

    @pytest.fixture
    def evaluator(self, mock_db, mock_redis, mock_storage):
        """Create evaluator instance."""
        from guardstack.predictive.evaluator import PredictiveAIEvaluator
        return PredictiveAIEvaluator(
            db=mock_db,
            redis=mock_redis,
            storage=mock_storage,
        )

    @pytest.fixture
    def sample_dataset(self):
        """Sample test dataset."""
        np.random.seed(42)
        n_samples = 100
        return {
            "X": np.random.randn(n_samples, 10),
            "y": np.random.randint(0, 2, n_samples),
            "sensitive_attrs": {
                "gender": np.random.choice(["M", "F"], n_samples),
                "age_group": np.random.choice(["young", "middle", "old"], n_samples),
            },
        }

    @pytest.fixture
    def sample_predictions(self, sample_dataset):
        """Sample model predictions."""
        n_samples = len(sample_dataset["y"])
        return {
            "predictions": np.random.randint(0, 2, n_samples),
            "probabilities": np.random.rand(n_samples),
        }

    @pytest.mark.asyncio
    async def test_evaluate_basic(self, evaluator, sample_model, sample_dataset, sample_predictions):
        """Test basic evaluation flow."""
        with patch.object(evaluator, '_run_pillar_evaluations') as mock_run:
            mock_run.return_value = {
                "accuracy": {"score": 0.85, "status": "pass"},
                "fairness": {"score": 0.80, "status": "pass"},
                "robustness": {"score": 0.75, "status": "pass"},
                "explainability": {"score": 0.82, "status": "pass"},
            }
            
            result = await evaluator.evaluate(
                model=sample_model,
                dataset=sample_dataset,
                predictions=sample_predictions,
            )
            
            assert result is not None
            assert "overall_score" in result
            assert "pillar_results" in result

    @pytest.mark.asyncio
    async def test_evaluate_all_pillars(self, evaluator, sample_model, sample_dataset, sample_predictions):
        """Test evaluation with all 8 pillars."""
        config = {
            "pillars": [
                "accuracy", "fairness", "robustness", "explainability",
                "privacy", "security", "reliability", "governance",
            ],
        }
        
        with patch.object(evaluator, '_run_pillar_evaluations') as mock_run:
            mock_run.return_value = {
                "accuracy": {"score": 0.85},
                "fairness": {"score": 0.80},
                "robustness": {"score": 0.75},
                "explainability": {"score": 0.82},
                "privacy": {"score": 0.88},
                "security": {"score": 0.90},
                "reliability": {"score": 0.78},
                "governance": {"score": 0.85},
            }
            
            result = await evaluator.evaluate(
                model=sample_model,
                dataset=sample_dataset,
                predictions=sample_predictions,
                config=config,
            )
            
            assert len(result.get("pillar_results", {})) == 8


class TestAccuracyPillar:
    """Test the Accuracy Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create accuracy pillar instance."""
        from guardstack.predictive.pillars.accuracy import AccuracyPillar
        return AccuracyPillar()

    @pytest.fixture
    def binary_classification_data(self):
        """Binary classification test data."""
        return {
            "y_true": np.array([0, 0, 1, 1, 0, 1, 0, 1, 1, 0]),
            "y_pred": np.array([0, 1, 1, 1, 0, 0, 0, 1, 1, 0]),
            "y_prob": np.array([0.2, 0.6, 0.8, 0.9, 0.3, 0.4, 0.1, 0.85, 0.9, 0.15]),
        }

    @pytest.mark.asyncio
    async def test_calculate_accuracy(self, pillar, binary_classification_data):
        """Test accuracy calculation."""
        result = await pillar.calculate_accuracy(
            y_true=binary_classification_data["y_true"],
            y_pred=binary_classification_data["y_pred"],
        )
        
        # 8 correct out of 10
        assert result["accuracy"] == 0.8

    @pytest.mark.asyncio
    async def test_calculate_precision_recall(self, pillar, binary_classification_data):
        """Test precision and recall calculation."""
        result = await pillar.calculate_precision_recall(
            y_true=binary_classification_data["y_true"],
            y_pred=binary_classification_data["y_pred"],
        )
        
        assert "precision" in result
        assert "recall" in result
        assert 0 <= result["precision"] <= 1
        assert 0 <= result["recall"] <= 1

    @pytest.mark.asyncio
    async def test_calculate_f1_score(self, pillar, binary_classification_data):
        """Test F1 score calculation."""
        result = await pillar.calculate_f1(
            y_true=binary_classification_data["y_true"],
            y_pred=binary_classification_data["y_pred"],
        )
        
        assert "f1" in result
        assert 0 <= result["f1"] <= 1

    @pytest.mark.asyncio
    async def test_calculate_auc_roc(self, pillar, binary_classification_data):
        """Test AUC-ROC calculation."""
        result = await pillar.calculate_auc_roc(
            y_true=binary_classification_data["y_true"],
            y_prob=binary_classification_data["y_prob"],
        )
        
        assert "auc_roc" in result
        assert 0 <= result["auc_roc"] <= 1

    @pytest.mark.asyncio
    async def test_full_evaluation(self, pillar, binary_classification_data):
        """Test full accuracy evaluation."""
        result = await pillar.evaluate(
            y_true=binary_classification_data["y_true"],
            y_pred=binary_classification_data["y_pred"],
            y_prob=binary_classification_data["y_prob"],
        )
        
        assert "score" in result
        assert "metrics" in result
        assert "accuracy" in result["metrics"]


class TestFairnessPillar:
    """Test the Predictive Fairness Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create fairness pillar instance."""
        from guardstack.predictive.pillars.fairness import FairnessPillar
        return FairnessPillar()

    @pytest.fixture
    def fairness_data(self):
        """Test data with sensitive attributes."""
        np.random.seed(42)
        n = 100
        return {
            "y_true": np.random.randint(0, 2, n),
            "y_pred": np.random.randint(0, 2, n),
            "sensitive_attr": np.random.choice(["A", "B"], n),
        }

    @pytest.mark.asyncio
    async def test_demographic_parity(self, pillar, fairness_data):
        """Test demographic parity calculation."""
        result = await pillar.calculate_demographic_parity(
            y_pred=fairness_data["y_pred"],
            sensitive_attr=fairness_data["sensitive_attr"],
        )
        
        assert "demographic_parity_difference" in result
        assert "demographic_parity_ratio" in result

    @pytest.mark.asyncio
    async def test_equalized_odds(self, pillar, fairness_data):
        """Test equalized odds calculation."""
        result = await pillar.calculate_equalized_odds(
            y_true=fairness_data["y_true"],
            y_pred=fairness_data["y_pred"],
            sensitive_attr=fairness_data["sensitive_attr"],
        )
        
        assert "equalized_odds_difference" in result

    @pytest.mark.asyncio
    async def test_calibration_by_group(self, pillar, fairness_data):
        """Test calibration across groups."""
        y_prob = np.random.rand(len(fairness_data["y_true"]))
        
        result = await pillar.calculate_calibration(
            y_true=fairness_data["y_true"],
            y_prob=y_prob,
            sensitive_attr=fairness_data["sensitive_attr"],
        )
        
        assert "calibration_difference" in result

    @pytest.mark.asyncio
    async def test_full_fairness_evaluation(self, pillar, fairness_data):
        """Test full fairness evaluation."""
        result = await pillar.evaluate(
            y_true=fairness_data["y_true"],
            y_pred=fairness_data["y_pred"],
            sensitive_attr=fairness_data["sensitive_attr"],
        )
        
        assert "score" in result
        assert "metrics" in result


class TestRobustnessPillar:
    """Test the Robustness Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create robustness pillar instance."""
        from guardstack.predictive.pillars.robustness import RobustnessPillar
        return RobustnessPillar()

    @pytest.fixture
    def model_function(self):
        """Mock model prediction function."""
        def predict(X):
            return (X.sum(axis=1) > 0).astype(int)
        return predict

    @pytest.mark.asyncio
    async def test_noise_robustness(self, pillar, model_function):
        """Test robustness to noise."""
        X = np.random.randn(50, 10)
        
        result = await pillar.test_noise_robustness(
            model_fn=model_function,
            X=X,
            noise_levels=[0.01, 0.05, 0.1],
        )
        
        assert "noise_sensitivity" in result
        assert isinstance(result["noise_sensitivity"], list)

    @pytest.mark.asyncio
    async def test_adversarial_robustness(self, pillar, model_function):
        """Test adversarial robustness."""
        X = np.random.randn(50, 10)
        
        result = await pillar.test_adversarial_robustness(
            model_fn=model_function,
            X=X,
            epsilon=0.1,
        )
        
        assert "adversarial_accuracy" in result
        assert "attack_success_rate" in result

    @pytest.mark.asyncio
    async def test_distribution_shift(self, pillar, model_function):
        """Test performance under distribution shift."""
        X_train = np.random.randn(100, 10)
        X_shift = np.random.randn(100, 10) + 0.5  # Shifted distribution
        
        result = await pillar.test_distribution_shift(
            model_fn=model_function,
            X_original=X_train,
            X_shifted=X_shift,
        )
        
        assert "performance_degradation" in result


class TestExplainabilityPillar:
    """Test the Explainability Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create explainability pillar instance."""
        from guardstack.predictive.pillars.explainability import ExplainabilityPillar
        return ExplainabilityPillar()

    @pytest.fixture
    def mock_model(self):
        """Mock ML model."""
        model = MagicMock()
        model.predict = lambda X: np.ones(len(X))
        model.predict_proba = lambda X: np.column_stack([
            np.zeros(len(X)) + 0.3,
            np.ones(len(X)) * 0.7
        ])
        model.feature_importances_ = np.array([0.3, 0.2, 0.15, 0.1, 0.1, 0.05, 0.05, 0.03, 0.01, 0.01])
        return model

    @pytest.mark.asyncio
    async def test_feature_importance(self, pillar, mock_model):
        """Test feature importance extraction."""
        feature_names = [f"feature_{i}" for i in range(10)]
        
        result = await pillar.get_feature_importance(
            model=mock_model,
            feature_names=feature_names,
        )
        
        assert "importance" in result
        assert len(result["importance"]) == 10

    @pytest.mark.asyncio
    async def test_shap_values(self, pillar, mock_model):
        """Test SHAP value calculation."""
        X = np.random.randn(10, 10)
        
        with patch('shap.TreeExplainer') as mock_shap:
            mock_explainer = MagicMock()
            mock_explainer.shap_values.return_value = np.random.randn(10, 10)
            mock_shap.return_value = mock_explainer
            
            result = await pillar.calculate_shap_values(
                model=mock_model,
                X=X,
            )
            
            assert "shap_values" in result or "error" in result

    @pytest.mark.asyncio
    async def test_local_explanation(self, pillar, mock_model):
        """Test local explanation for single prediction."""
        X_single = np.random.randn(1, 10)
        feature_names = [f"feature_{i}" for i in range(10)]
        
        result = await pillar.explain_prediction(
            model=mock_model,
            X=X_single,
            feature_names=feature_names,
        )
        
        assert "explanation" in result


class TestPrivacyPillarPredictive:
    """Test the Privacy Pillar for Predictive AI."""

    @pytest.fixture
    def pillar(self):
        """Create privacy pillar instance."""
        from guardstack.predictive.pillars.privacy import PrivacyPillar
        return PrivacyPillar()

    @pytest.mark.asyncio
    async def test_membership_inference_attack(self, pillar):
        """Test membership inference attack detection."""
        # Mock training and test data
        X_train = np.random.randn(100, 10)
        X_test = np.random.randn(100, 10)
        
        model = MagicMock()
        model.predict_proba = lambda X: np.column_stack([
            np.random.rand(len(X)),
            np.random.rand(len(X))
        ])
        
        result = await pillar.test_membership_inference(
            model=model,
            X_train=X_train,
            X_test=X_test,
        )
        
        assert "vulnerability_score" in result
        assert "attack_accuracy" in result

    @pytest.mark.asyncio
    async def test_differential_privacy_check(self, pillar):
        """Test differential privacy compliance check."""
        model_config = {
            "epsilon": 1.0,
            "delta": 1e-5,
            "mechanism": "gaussian",
        }
        
        result = await pillar.check_differential_privacy(model_config)
        
        assert "is_compliant" in result
        assert "privacy_budget" in result


class TestReliabilityPillar:
    """Test the Reliability Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create reliability pillar instance."""
        from guardstack.predictive.pillars.reliability import ReliabilityPillar
        return ReliabilityPillar()

    @pytest.mark.asyncio
    async def test_calibration_check(self, pillar):
        """Test model calibration check."""
        y_true = np.random.randint(0, 2, 100)
        y_prob = np.random.rand(100)
        
        result = await pillar.check_calibration(
            y_true=y_true,
            y_prob=y_prob,
        )
        
        assert "expected_calibration_error" in result
        assert "max_calibration_error" in result

    @pytest.mark.asyncio
    async def test_consistency_check(self, pillar):
        """Test prediction consistency."""
        model = MagicMock()
        model.predict = lambda X: np.ones(len(X))
        
        X = np.random.randn(50, 10)
        
        result = await pillar.check_consistency(
            model=model,
            X=X,
            n_runs=5,
        )
        
        assert "consistency_score" in result


class TestGovernancePillar:
    """Test the Governance Pillar evaluator."""

    @pytest.fixture
    def pillar(self):
        """Create governance pillar instance."""
        from guardstack.predictive.pillars.governance import GovernancePillar
        return GovernancePillar()

    @pytest.fixture
    def model_metadata(self):
        """Sample model metadata."""
        return {
            "name": "test_model",
            "version": "1.0.0",
            "owner": "data_science_team",
            "created_at": "2024-01-01T00:00:00Z",
            "training_data": {
                "source": "internal_db",
                "size": 10000,
                "features": 50,
            },
            "intended_use": "Customer churn prediction",
            "limitations": "Not suitable for real-time scoring",
            "ethical_considerations": "May have demographic biases",
        }

    @pytest.mark.asyncio
    async def test_documentation_check(self, pillar, model_metadata):
        """Test model documentation completeness."""
        result = await pillar.check_documentation(model_metadata)
        
        assert "completeness_score" in result
        assert "missing_fields" in result

    @pytest.mark.asyncio
    async def test_lineage_tracking(self, pillar, model_metadata):
        """Test model lineage tracking."""
        lineage = {
            "parent_model": None,
            "training_job": "job-123",
            "data_version": "v2.0",
        }
        
        result = await pillar.check_lineage(lineage)
        
        assert "lineage_complete" in result

    @pytest.mark.asyncio
    async def test_compliance_check(self, pillar, model_metadata):
        """Test regulatory compliance check."""
        result = await pillar.check_compliance(
            model_metadata=model_metadata,
            frameworks=["gdpr", "ccpa"],
        )
        
        assert "compliance_status" in result
        assert "gaps" in result


class TestSecurityPillarPredictive:
    """Test the Security Pillar for Predictive AI."""

    @pytest.fixture
    def pillar(self):
        """Create security pillar instance."""
        from guardstack.predictive.pillars.security import SecurityPillar
        return SecurityPillar()

    @pytest.mark.asyncio
    async def test_model_extraction_attack(self, pillar):
        """Test model extraction attack vulnerability."""
        model = MagicMock()
        model.predict = lambda X: np.ones(len(X))
        
        result = await pillar.test_model_extraction(
            model=model,
            n_queries=100,
        )
        
        assert "vulnerability_score" in result

    @pytest.mark.asyncio
    async def test_data_poisoning_detection(self, pillar):
        """Test data poisoning detection."""
        X = np.random.randn(100, 10)
        y = np.random.randint(0, 2, 100)
        
        # Add some poisoned samples
        X_poisoned = np.vstack([X, np.random.randn(5, 10) * 10])
        y_poisoned = np.concatenate([y, np.array([1, 1, 1, 1, 1])])
        
        result = await pillar.detect_data_poisoning(
            X=X_poisoned,
            y=y_poisoned,
        )
        
        assert "poisoning_detected" in result
        assert "suspicious_samples" in result
