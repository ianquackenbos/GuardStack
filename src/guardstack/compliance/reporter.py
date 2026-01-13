"""
Compliance Reporter

Generates compliance reports in various formats.
"""

import io
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .assessor import AssessmentResult
from .frameworks import get_framework, ControlStatus


class ComplianceReporter:
    """Generates compliance reports."""
    
    def __init__(self, storage=None, templates_dir: str | None = None):
        self.storage = storage
        self.templates_dir = Path(templates_dir) if templates_dir else None
    
    async def generate_report(
        self,
        assessment: AssessmentResult,
        format: str = "json",
        include_evidence: bool = True,
    ) -> dict:
        """
        Generate a compliance report.
        
        Args:
            assessment: The assessment result
            format: Output format (json, html, pdf)
            include_evidence: Whether to include detailed evidence
            
        Returns:
            Dict with report_id and file_path or content
        """
        if format == "json":
            return await self._generate_json_report(assessment, include_evidence)
        elif format == "html":
            return await self._generate_html_report(assessment, include_evidence)
        elif format == "pdf":
            return await self._generate_pdf_report(assessment, include_evidence)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _generate_json_report(
        self,
        assessment: AssessmentResult,
        include_evidence: bool,
    ) -> dict:
        """Generate JSON format report."""
        framework = get_framework(assessment.framework_id)
        
        report = {
            "report_type": "compliance_assessment",
            "generated_at": datetime.utcnow().isoformat(),
            "framework": {
                "id": assessment.framework_id,
                "name": framework.name if framework else assessment.framework_id,
                "version": framework.version if framework else "unknown",
            },
            "model_id": assessment.model_id,
            "assessment_date": assessment.timestamp.isoformat(),
            "summary": {
                "overall_coverage": round(assessment.overall_coverage * 100, 1),
                "controls_assessed": assessment.controls_assessed,
                "controls_implemented": assessment.controls_implemented,
                "controls_partial": assessment.controls_partial,
                "controls_not_implemented": assessment.controls_not_implemented,
                "controls_not_applicable": assessment.controls_not_applicable,
            },
            "control_details": self._format_control_details(
                assessment, framework, include_evidence
            ),
            "gaps": assessment.gaps,
            "recommendations": assessment.recommendations,
        }
        
        report_id = f"compliance-{assessment.model_id}-{assessment.framework_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        if self.storage:
            path = f"reports/compliance/{report_id}.json"
            await self.storage.upload(
                path,
                json.dumps(report, indent=2).encode(),
                content_type="application/json",
            )
            return {"report_id": report_id, "file_path": path, "format": "json"}
        
        return {"report_id": report_id, "content": report, "format": "json"}
    
    async def _generate_html_report(
        self,
        assessment: AssessmentResult,
        include_evidence: bool,
    ) -> dict:
        """Generate HTML format report."""
        framework = get_framework(assessment.framework_id)
        
        html = self._render_html_template(assessment, framework, include_evidence)
        
        report_id = f"compliance-{assessment.model_id}-{assessment.framework_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        if self.storage:
            path = f"reports/compliance/{report_id}.html"
            await self.storage.upload(
                path,
                html.encode(),
                content_type="text/html",
            )
            return {"report_id": report_id, "file_path": path, "format": "html"}
        
        return {"report_id": report_id, "content": html, "format": "html"}
    
    async def _generate_pdf_report(
        self,
        assessment: AssessmentResult,
        include_evidence: bool,
    ) -> dict:
        """Generate PDF format report."""
        # First generate HTML, then convert to PDF
        framework = get_framework(assessment.framework_id)
        html = self._render_html_template(assessment, framework, include_evidence)
        
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html).write_pdf()
        except ImportError:
            # Fallback: return HTML if weasyprint not available
            return await self._generate_html_report(assessment, include_evidence)
        
        report_id = f"compliance-{assessment.model_id}-{assessment.framework_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        if self.storage:
            path = f"reports/compliance/{report_id}.pdf"
            await self.storage.upload(
                path,
                pdf_bytes,
                content_type="application/pdf",
            )
            return {"report_id": report_id, "file_path": path, "format": "pdf"}
        
        return {"report_id": report_id, "content": pdf_bytes, "format": "pdf"}
    
    def _format_control_details(
        self,
        assessment: AssessmentResult,
        framework,
        include_evidence: bool,
    ) -> list[dict]:
        """Format control details for report."""
        if not framework:
            return []
        
        details = []
        for category in framework.get_categories():
            category_details = {
                "category_id": category.id,
                "category_name": category.name,
                "controls": [],
            }
            
            for control in category.controls:
                status = assessment.control_results.get(control.id, ControlStatus.NOT_ASSESSED)
                control_detail = {
                    "id": control.id,
                    "name": control.name,
                    "description": control.description,
                    "status": status.value,
                    "status_label": self._get_status_label(status),
                    "requirements": control.requirements,
                }
                
                if include_evidence:
                    control_detail["evidence"] = assessment.evidence.get(control.id, [])
                
                category_details["controls"].append(control_detail)
            
            details.append(category_details)
        
        return details
    
    def _get_status_label(self, status: ControlStatus) -> str:
        """Get human-readable status label."""
        labels = {
            ControlStatus.NOT_ASSESSED: "Not Assessed",
            ControlStatus.IMPLEMENTED: "Implemented",
            ControlStatus.PARTIAL: "Partially Implemented",
            ControlStatus.NOT_IMPLEMENTED: "Not Implemented",
            ControlStatus.NOT_APPLICABLE: "Not Applicable",
        }
        return labels.get(status, "Unknown")
    
    def _get_status_color(self, status: ControlStatus) -> str:
        """Get color for status display."""
        colors = {
            ControlStatus.NOT_ASSESSED: "#6c757d",  # Gray
            ControlStatus.IMPLEMENTED: "#28a745",    # Green
            ControlStatus.PARTIAL: "#ffc107",        # Yellow
            ControlStatus.NOT_IMPLEMENTED: "#dc3545", # Red
            ControlStatus.NOT_APPLICABLE: "#6c757d",  # Gray
        }
        return colors.get(status, "#6c757d")
    
    def _render_html_template(
        self,
        assessment: AssessmentResult,
        framework,
        include_evidence: bool,
    ) -> str:
        """Render HTML template for report."""
        framework_name = framework.name if framework else assessment.framework_id
        framework_version = framework.version if framework else "N/A"
        
        # Control details HTML
        controls_html = ""
        if framework:
            for category in framework.get_categories():
                controls_html += f"""
                <div class="category">
                    <h3>{category.name}</h3>
                    <p class="category-desc">{category.description}</p>
                    <table class="controls-table">
                        <thead>
                            <tr>
                                <th>Control ID</th>
                                <th>Name</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for control in category.controls:
                    status = assessment.control_results.get(control.id, ControlStatus.NOT_ASSESSED)
                    status_label = self._get_status_label(status)
                    status_color = self._get_status_color(status)
                    
                    controls_html += f"""
                            <tr>
                                <td><code>{control.id}</code></td>
                                <td>{control.name}</td>
                                <td><span class="status-badge" style="background-color: {status_color}">{status_label}</span></td>
                            </tr>
                    """
                
                controls_html += """
                        </tbody>
                    </table>
                </div>
                """
        
        # Gaps HTML
        gaps_html = ""
        if assessment.gaps:
            gaps_html = "<ul class='gaps-list'>"
            for gap in assessment.gaps:
                gaps_html += f"""
                <li>
                    <strong>{gap['control_id']}: {gap['control_name']}</strong>
                    <ul>
                """
                for req in gap.get('requirements', []):
                    gaps_html += f"<li>{req}</li>"
                gaps_html += "</ul></li>"
            gaps_html += "</ul>"
        else:
            gaps_html = "<p class='no-gaps'>No significant gaps identified.</p>"
        
        # Recommendations HTML
        recommendations_html = ""
        if assessment.recommendations:
            for rec in assessment.recommendations[:10]:  # Top 10
                priority_class = "priority-high" if rec.get("priority") == "high" else "priority-medium"
                recommendations_html += f"""
                <div class="recommendation {priority_class}">
                    <h4>{rec['title']}</h4>
                    <p>{rec['description']}</p>
                    <p><strong>Control:</strong> {rec['control_name']} ({rec['control_id']})</p>
                    <p><strong>Current Score:</strong> {rec['current_score']:.2f} → <strong>Target:</strong> {rec['target_score']:.2f}</p>
                    <ul>
                """
                for action in rec.get('actions', []):
                    recommendations_html += f"<li>{action}</li>"
                recommendations_html += "</ul></div>"
        else:
            recommendations_html = "<p>No recommendations at this time.</p>"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Report - {framework_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        .header {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1a73e8;
            margin: 0 0 10px 0;
        }}
        .header .meta {{
            color: #666;
            font-size: 0.9em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #1a73e8;
        }}
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        .coverage-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .coverage-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1a73e8, #34a853);
            transition: width 0.3s;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #1a73e8;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        .category {{
            margin-bottom: 30px;
        }}
        .category h3 {{
            color: #333;
            margin-bottom: 5px;
        }}
        .category-desc {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        .controls-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .controls-table th, .controls-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        .controls-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .gaps-list {{
            list-style-type: none;
            padding: 0;
        }}
        .gaps-list > li {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }}
        .gaps-list > li ul {{
            margin-top: 10px;
            color: #666;
        }}
        .no-gaps {{
            color: #28a745;
            font-weight: 500;
        }}
        .recommendation {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .recommendation.priority-high {{
            border-left: 4px solid #dc3545;
        }}
        .recommendation.priority-medium {{
            border-left: 4px solid #ffc107;
        }}
        .recommendation h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.85em;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .report-container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>Compliance Assessment Report</h1>
            <div class="meta">
                <p><strong>Framework:</strong> {framework_name} (v{framework_version})</p>
                <p><strong>Model ID:</strong> {assessment.model_id}</p>
                <p><strong>Assessment Date:</strong> {assessment.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</p>
                <p><strong>Report Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="summary">
                <div class="summary-card">
                    <div class="value">{assessment.overall_coverage * 100:.1f}%</div>
                    <div class="label">Overall Coverage</div>
                </div>
                <div class="summary-card">
                    <div class="value">{assessment.controls_implemented}</div>
                    <div class="label">Implemented</div>
                </div>
                <div class="summary-card">
                    <div class="value">{assessment.controls_partial}</div>
                    <div class="label">Partial</div>
                </div>
                <div class="summary-card">
                    <div class="value">{assessment.controls_not_implemented}</div>
                    <div class="label">Not Implemented</div>
                </div>
            </div>
            
            <div class="coverage-bar">
                <div class="coverage-fill" style="width: {assessment.overall_coverage * 100}%"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>Control Assessment Details</h2>
            {controls_html}
        </div>
        
        <div class="section">
            <h2>Identified Gaps</h2>
            {gaps_html}
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            {recommendations_html}
        </div>
        
        <div class="footer">
            <p>Generated by GuardStack | AI Safety & Governance Platform</p>
            <p>This report is for informational purposes. Consult with compliance professionals for official assessments.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    async def generate_executive_summary(
        self,
        assessments: dict[str, AssessmentResult],
    ) -> dict:
        """Generate executive summary across multiple frameworks."""
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "frameworks_assessed": len(assessments),
            "framework_summaries": [],
            "overall_risk_level": "low",
            "priority_gaps": [],
        }
        
        all_gaps = []
        all_recommendations = []
        
        for framework_id, assessment in assessments.items():
            framework = get_framework(framework_id)
            
            summary["framework_summaries"].append({
                "framework_id": framework_id,
                "framework_name": framework.name if framework else framework_id,
                "coverage": round(assessment.overall_coverage * 100, 1),
                "implemented": assessment.controls_implemented,
                "gaps": len(assessment.gaps),
            })
            
            all_gaps.extend(assessment.gaps)
            all_recommendations.extend([
                r for r in assessment.recommendations
                if r.get("priority") == "high"
            ])
        
        # Determine overall risk level
        avg_coverage = sum(
            a.overall_coverage for a in assessments.values()
        ) / len(assessments)
        
        if avg_coverage >= 0.8:
            summary["overall_risk_level"] = "low"
        elif avg_coverage >= 0.5:
            summary["overall_risk_level"] = "medium"
        else:
            summary["overall_risk_level"] = "high"
        
        # Top priority gaps
        summary["priority_gaps"] = all_gaps[:5]
        summary["priority_recommendations"] = all_recommendations[:5]
        
        return summary
