# Predictive AI Evaluation (8 Pillars)

GuardStack evaluates traditional predictive ML models using eight comprehensive safety and security pillars, inspired by responsible AI frameworks and regulatory requirements.

## Overview

| Pillar | Focus Area | Key Tools |
|--------|------------|-----------|
| **Explain** | Model interpretability | SHAP, LIME, Captum |
| **Actions** | Recourse & remediation | DiCE, Alibi |
| **Fairness** | Bias detection | Fairlearn, AIF360 |
| **Robustness** | Adversarial resilience | IBM ART |
| **Trace** | Lineage & provenance | Custom tracking |
| **Testing** | Metamorphic testing | MT framework |
| **Imitation** | Model extraction defense | Privacy analysis |
| **Privacy** | Differential privacy | TF Privacy, PySyft |

---

## 1. Explain (Interpretability)

### Purpose
Ensure model decisions can be understood and explained to stakeholders, auditors, and affected individuals.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Feature Attribution** | Identify most influential features | Top 5 features explain >60% variance |
| **Local Explanations** | Per-prediction explanations | Available for 100% of predictions |
| **Global Explanations** | Model-wide patterns | Documented and validated |
| **Consistency** | Stable explanations | <10% variance across runs |

### Tools Used
- **SHAP**: SHapley Additive exPlanations for feature importance
- **LIME**: Local Interpretable Model-agnostic Explanations
- **Captum**: PyTorch model interpretability

### Example Configuration

```yaml
explain:
  enabled: true
  methods:
    - shap_kernel
    - lime_tabular
  sample_size: 1000
  background_samples: 100
  top_features: 10
```

### Sample Output

```json
{
  "pillar": "explain",
  "score": 85,
  "metrics": {
    "feature_attribution_coverage": 0.92,
    "explanation_consistency": 0.88,
    "top_features": [
      {"name": "income", "importance": 0.35},
      {"name": "credit_history", "importance": 0.28},
      {"name": "employment_length", "importance": 0.15}
    ]
  },
  "findings": [],
  "recommendations": []
}
```

---

## 2. Actions (Recourse)

### Purpose
Provide affected individuals with actionable steps to change unfavorable outcomes.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Recourse Availability** | % of negative outcomes with path to positive | >90% |
| **Actionability** | Features in recourse are changeable | 100% immutable features excluded |
| **Cost** | Average effort required | <3 feature changes |
| **Validity** | Recourse actually works | >95% success rate |

### Tools Used
- **DiCE**: Diverse Counterfactual Explanations
- **Alibi**: Counterfactual explanations
- **Carla**: Counterfactual and recourse library

### Example Configuration

```yaml
actions:
  enabled: true
  counterfactual_method: dice
  num_counterfactuals: 5
  immutable_features:
    - age
    - gender
    - race
  actionable_features:
    - income
    - credit_score
    - employment_status
```

---

## 3. Fairness (Bias Detection)

### Purpose
Detect and measure bias across protected demographic groups.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Demographic Parity** | Equal positive rates | Ratio >0.8 |
| **Equalized Odds** | Equal TPR/FPR | Difference <0.1 |
| **Calibration** | Consistent probabilities | Error <5% |
| **Individual Fairness** | Similar treatment for similar individuals | >95% |

### Protected Attributes
- Race/Ethnicity
- Gender
- Age
- Disability status
- Socioeconomic status

### Tools Used
- **Fairlearn**: Microsoft's fairness assessment toolkit
- **AIF360**: IBM AI Fairness 360

### Example Configuration

```yaml
fairness:
  enabled: true
  protected_attributes:
    - gender
    - race
    - age_group
  metrics:
    - demographic_parity
    - equalized_odds
    - calibration_error
  threshold_ratio: 0.8
```

### Sample Output

```json
{
  "pillar": "fairness",
  "score": 72,
  "metrics": {
    "demographic_parity": {
      "gender": {"male": 0.65, "female": 0.58, "ratio": 0.89},
      "race": {"white": 0.68, "black": 0.52, "ratio": 0.76}
    },
    "equalized_odds_difference": 0.12
  },
  "findings": [
    {
      "severity": "high",
      "message": "Significant disparity detected for race attribute",
      "details": "Black applicants approved at 76% rate of white applicants"
    }
  ],
  "recommendations": [
    "Apply threshold adjustment for race-based disparities",
    "Review training data for historical bias"
  ]
}
```

---

## 4. Robustness (Adversarial Testing)

### Purpose
Evaluate model resilience against adversarial attacks and input perturbations.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Evasion Resistance** | Resists adversarial examples | >95% accuracy under attack |
| **Noise Tolerance** | Handles input noise | <5% accuracy drop |
| **Boundary Stability** | Stable decision boundaries | Consistent within ε |
| **Certified Defense** | Provable robustness bounds | Certificate coverage >80% |

### Attack Types Tested
- **FGSM**: Fast Gradient Sign Method
- **PGD**: Projected Gradient Descent
- **C&W**: Carlini & Wagner
- **DeepFool**: Minimal perturbation attacks
- **Boundary Attack**: Decision-based attacks

### Tools Used
- **IBM ART**: Adversarial Robustness Toolbox
- **Foolbox**: Adversarial attack library
- **CleverHans**: Adversarial example library

### Example Configuration

```yaml
robustness:
  enabled: true
  attacks:
    - fgsm:
        eps: 0.3
    - pgd:
        eps: 0.3
        steps: 40
    - deepfool:
        max_iter: 100
  noise_levels: [0.01, 0.05, 0.1]
  sample_size: 500
```

---

## 5. Trace (Lineage & Provenance)

### Purpose
Track model development history, data lineage, and deployment provenance.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Data Lineage** | Complete training data history | 100% traceable |
| **Model Versioning** | Version control for all artifacts | Full history |
| **Reproducibility** | Can recreate model from specs | 100% reproducible |
| **Audit Trail** | All actions logged | Complete log |

### Tracked Artifacts
- Training datasets
- Feature engineering code
- Model architecture
- Hyperparameters
- Training logs
- Evaluation metrics
- Deployment configurations

### Example Configuration

```yaml
trace:
  enabled: true
  data_lineage:
    track_sources: true
    track_transformations: true
  model_versioning:
    backend: mlflow
    registry_url: http://mlflow:5000
  audit_logging:
    enabled: true
    retention_days: 365
```

---

## 6. Testing (Metamorphic Testing)

### Purpose
Apply metamorphic testing principles to identify hidden bugs and edge cases.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Metamorphic Relations** | Properties that should hold | >95% satisfied |
| **Invariance Tests** | Unchanged predictions for semantic equivalents | >99% |
| **Edge Cases** | Handles boundary inputs | No crashes |
| **Consistency** | Deterministic outputs | 100% reproducible |

### Metamorphic Relations
- **Permutation Invariance**: Reordering features shouldn't change prediction
- **Scale Invariance**: Scaling inputs proportionally shouldn't change prediction
- **Symmetry**: Swapping symmetric features shouldn't change prediction
- **Monotonicity**: Increasing a feature should increase/decrease output predictably

### Example Configuration

```yaml
testing:
  enabled: true
  metamorphic_relations:
    - type: permutation
      features: [feature_a, feature_b]
    - type: monotonicity
      feature: income
      direction: positive
  edge_cases:
    - null_values
    - extreme_values
    - out_of_distribution
  num_tests: 1000
```

---

## 7. Imitation (Model Extraction Defense)

### Purpose
Protect against model extraction attacks that steal model functionality.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Query Resistance** | Resists extraction via queries | >1M queries needed |
| **Confidence Masking** | Obscured probability scores | Minimal info leak |
| **Watermarking** | Detectable in stolen models | Embedded markers |
| **Rate Limiting** | Query rate controls | Enforced limits |

### Defense Mechanisms
- Confidence score rounding
- Noise injection
- Watermark embedding
- Query rate limiting
- Anomaly detection

### Example Configuration

```yaml
imitation:
  enabled: true
  defenses:
    confidence_rounding:
      enabled: true
      decimal_places: 2
    noise_injection:
      enabled: true
      scale: 0.01
    watermarking:
      enabled: true
      method: frontier_stitching
  query_monitoring:
    enabled: true
    alert_threshold: 10000
```

---

## 8. Privacy (Data Protection)

### Purpose
Ensure model doesn't leak training data or enable membership inference.

### Evaluations

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Membership Inference** | Can't determine training membership | AUC <0.55 |
| **Attribute Inference** | Can't infer sensitive attributes | AUC <0.55 |
| **Model Inversion** | Can't reconstruct training data | PSNR <20dB |
| **Differential Privacy** | Formal privacy guarantees | ε <10 |

### Privacy Mechanisms
- Differential privacy (DP-SGD)
- Gradient clipping
- Noise addition
- K-anonymity verification
- PATE (Private Aggregation of Teacher Ensembles)

### Tools Used
- **TensorFlow Privacy**: Differential privacy for TF
- **Opacus**: DP for PyTorch
- **PySyft**: Secure computation

### Example Configuration

```yaml
privacy:
  enabled: true
  differential_privacy:
    enabled: true
    epsilon: 8.0
    delta: 1e-5
  membership_inference:
    attack_model: shadow_models
    num_shadow_models: 10
  attribute_inference:
    sensitive_attributes:
      - income
      - health_status
```

---

## Running a Full Predictive Evaluation

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "your-model-id",
    "evaluation_type": "predictive",
    "config": {
      "pillars": ["explain", "actions", "fairness", "robustness", 
                  "trace", "testing", "imitation", "privacy"],
      "test_dataset_path": "s3://data/test_data.parquet",
      "sample_size": 5000,
      "protected_attributes": ["gender", "race", "age_group"]
    }
  }'
```

### Via Python

```python
from guardstack import GuardStackClient

client = GuardStackClient()

evaluation = client.evaluations.create(
    model_id="your-model-id",
    evaluation_type="predictive",
    pillars=[
        "explain", "actions", "fairness", "robustness",
        "trace", "testing", "imitation", "privacy"
    ],
    config={
        "test_dataset_path": "s3://data/test_data.parquet",
        "sample_size": 5000,
        "protected_attributes": ["gender", "race", "age_group"],
        "fairness": {
            "threshold_ratio": 0.8
        },
        "robustness": {
            "attacks": ["fgsm", "pgd"],
            "eps": 0.3
        }
    }
)

# Start evaluation
client.evaluations.start(evaluation.id)

# Get results
results = client.evaluations.get_results(evaluation.id)
print(f"Overall Score: {results.overall_score}")
```

---

## Scoring & Thresholds

### Default Thresholds

| Score | Status | Action Required |
|-------|--------|-----------------|
| ≥80 | 🟢 Pass | Ready for production |
| 50-79 | 🟡 Warn | Review and remediate |
| <50 | 🔴 Fail | Block deployment |

### Pillar Weights

Default weights for overall score calculation:

| Pillar | Weight | Rationale |
|--------|--------|-----------|
| Fairness | 20% | Regulatory priority |
| Privacy | 15% | Data protection |
| Robustness | 15% | Security critical |
| Explain | 15% | Transparency |
| Actions | 10% | User empowerment |
| Trace | 10% | Auditability |
| Testing | 10% | Quality assurance |
| Imitation | 5% | IP protection |

### Custom Weights

```python
evaluation = client.evaluations.create(
    model_id="your-model-id",
    evaluation_type="predictive",
    config={
        "pillar_weights": {
            "fairness": 0.30,
            "privacy": 0.25,
            "robustness": 0.20,
            "explain": 0.10,
            "actions": 0.05,
            "trace": 0.05,
            "testing": 0.03,
            "imitation": 0.02
        }
    }
)
```
