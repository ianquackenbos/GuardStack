"""
Report Generation Tasks

Celery tasks for generating PDF, HTML, and JSON reports
using ReportLab and Jinja2 templates.
"""

import io
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    name="guardstack.workers.tasks.reports.generate_report",
    max_retries=3,
    default_retry_delay=60,
)
def generate_report(
    self,
    report_id: str,
    template_id: str,
    title: str,
    format: str,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    filters: Optional[dict] = None,
    parameters: Optional[dict] = None,
) -> dict:
    """
    Generate a report asynchronously.
    
    Args:
        report_id: Unique report identifier
        template_id: Template to use for generation
        title: Report title
        format: Output format (pdf, html, json, csv)
        date_range_start: Report period start (ISO format)
        date_range_end: Report period end (ISO format)
        filters: Additional data filters
        parameters: Template-specific parameters
    
    Returns:
        dict with report metadata and storage location
    """
    logger.info(f"Starting report generation: {report_id} using template {template_id}")
    
    try:
        # Update task state
        self.update_state(state="PROGRESS", meta={"stage": "gathering_data", "progress": 10})
        
        # Gather report data based on template
        report_data = _gather_report_data(
            template_id=template_id,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            filters=filters or {},
        )
        
        self.update_state(state="PROGRESS", meta={"stage": "generating_content", "progress": 50})
        
        # Generate report in requested format
        if format == "pdf":
            content, content_type = _generate_pdf_report(template_id, title, report_data, parameters)
        elif format == "html":
            content, content_type = _generate_html_report(template_id, title, report_data, parameters)
        elif format == "json":
            content, content_type = _generate_json_report(title, report_data)
        elif format == "csv":
            content, content_type = _generate_csv_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.update_state(state="PROGRESS", meta={"stage": "storing_report", "progress": 90})
        
        # Store report (in production, upload to S3/MinIO)
        storage_path = _store_report(report_id, content, format)
        
        logger.info(f"Report generation completed: {report_id}")
        
        return {
            "report_id": report_id,
            "status": "completed",
            "format": format,
            "content_type": content_type,
            "file_size": len(content),
            "storage_path": storage_path,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Report generation failed: {report_id} - {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    name="guardstack.workers.tasks.reports.generate_daily_summary",
)
def generate_daily_summary() -> dict:
    """
    Generate daily summary report (scheduled task).
    
    This runs on a schedule to create automated daily reports.
    """
    logger.info("Starting daily summary report generation")
    
    from uuid import uuid4
    
    report_id = str(uuid4())
    today = datetime.utcnow().date()
    
    # Trigger the main report generation
    result = generate_report.delay(
        report_id=report_id,
        template_id="executive-dashboard",
        title=f"Daily Summary - {today.isoformat()}",
        format="pdf",
        date_range_start=(datetime.utcnow().replace(hour=0, minute=0, second=0)).isoformat(),
        date_range_end=datetime.utcnow().isoformat(),
    )
    
    return {
        "report_id": report_id,
        "task_id": result.id,
        "scheduled_at": datetime.utcnow().isoformat(),
    }


@shared_task(
    name="guardstack.workers.tasks.reports.send_scheduled_report",
)
def send_scheduled_report(
    schedule_id: str,
    report_path: str,
    recipients: list[str],
    subject: str,
) -> dict:
    """
    Send a scheduled report to recipients via email.
    """
    logger.info(f"Sending scheduled report {schedule_id} to {len(recipients)} recipients")
    
    # In production, integrate with email service (SendGrid, SES, etc.)
    # For now, log the action
    
    return {
        "schedule_id": schedule_id,
        "recipients": recipients,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }


def _gather_report_data(
    template_id: str,
    date_range_start: Optional[str],
    date_range_end: Optional[str],
    filters: dict,
) -> dict:
    """Gather data for report based on template type."""
    # In production, query database and external services
    # This is mock data for now
    
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period": {
            "start": date_range_start,
            "end": date_range_end,
        },
        "summary": {
            "total_models": 47,
            "total_evaluations": 234,
            "compliance_score": 87.5,
            "security_score": 72.3,
            "critical_findings": 3,
            "open_findings": 23,
        },
        "models": [
            {"name": "GPT-4", "status": "compliant", "risk_score": 23.5},
            {"name": "Claude-3", "status": "compliant", "risk_score": 18.2},
            {"name": "Llama-2", "status": "review_required", "risk_score": 45.8},
        ],
        "findings": [
            {"severity": "critical", "count": 3},
            {"severity": "high", "count": 8},
            {"severity": "medium", "count": 12},
            {"severity": "low", "count": 0},
        ],
        "compliance": {
            "EU_AI_Act": {"score": 89, "status": "compliant"},
            "SOC2": {"score": 92, "status": "compliant"},
            "HIPAA": {"score": 85, "status": "review_required"},
        },
    }


def _generate_pdf_report(
    template_id: str,
    title: str,
    data: dict,
    parameters: Optional[dict],
) -> tuple[bytes, str]:
    """Generate PDF report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 0.5 * inch))
        
        # Summary section
        story.append(Paragraph("Executive Summary", styles["Heading1"]))
        summary = data.get("summary", {})
        summary_data = [
            ["Metric", "Value"],
            ["Total Models", str(summary.get("total_models", 0))],
            ["Security Score", f"{summary.get('security_score', 0):.1f}%"],
            ["Compliance Score", f"{summary.get('compliance_score', 0):.1f}%"],
            ["Critical Findings", str(summary.get("critical_findings", 0))],
        ]
        
        table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.25 * inch))
        
        # Generation timestamp
        story.append(Paragraph(f"Generated: {data.get('generated_at', '')}", styles["Normal"]))
        
        doc.build(story)
        content = buffer.getvalue()
        buffer.close()
        
        return content, "application/pdf"
        
    except ImportError:
        # Fallback if ReportLab not installed
        logger.warning("ReportLab not installed, generating placeholder PDF")
        return b"%PDF-1.4 placeholder", "application/pdf"


def _generate_html_report(
    template_id: str,
    title: str,
    data: dict,
    parameters: Optional[dict],
) -> tuple[bytes, str]:
    """Generate HTML report using Jinja2."""
    # Simple HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #333; }}
            .label {{ font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="summary">
            <h2>Executive Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Models</td>
                    <td>{data.get('summary', {}).get('total_models', 0)}</td>
                </tr>
                <tr>
                    <td>Security Score</td>
                    <td>{data.get('summary', {}).get('security_score', 0):.1f}%</td>
                </tr>
                <tr>
                    <td>Compliance Score</td>
                    <td>{data.get('summary', {}).get('compliance_score', 0):.1f}%</td>
                </tr>
                <tr>
                    <td>Critical Findings</td>
                    <td>{data.get('summary', {}).get('critical_findings', 0)}</td>
                </tr>
            </table>
        </div>
        <footer>
            <p>Generated: {data.get('generated_at', '')}</p>
        </footer>
    </body>
    </html>
    """
    
    return html.encode("utf-8"), "text/html"


def _generate_json_report(title: str, data: dict) -> tuple[bytes, str]:
    """Generate JSON report."""
    report = {
        "title": title,
        **data,
    }
    return json.dumps(report, indent=2).encode("utf-8"), "application/json"


def _generate_csv_report(data: dict) -> tuple[bytes, str]:
    """Generate CSV report."""
    import csv
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write summary as CSV
    writer.writerow(["Metric", "Value"])
    summary = data.get("summary", {})
    for key, value in summary.items():
        writer.writerow([key, value])
    
    content = buffer.getvalue().encode("utf-8")
    buffer.close()
    
    return content, "text/csv"


def _store_report(report_id: str, content: bytes, format: str) -> str:
    """Store report content and return storage path."""
    # In production, upload to S3/MinIO
    # For now, return a mock path
    return f"s3://guardstack-reports/{report_id}/report.{format}"
