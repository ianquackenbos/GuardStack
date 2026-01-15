"""
Reports Router

Endpoints for generating, managing, and downloading
compliance and security reports in various formats.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ReportTemplate(BaseModel):
    """Report template definition"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Category: compliance, security, executive, audit")
    supported_formats: list[str] = Field(..., description="Supported output formats")
    parameters: Optional[dict] = Field(None, description="Configurable parameters")


class ReportGenerateRequest(BaseModel):
    """Request model for report generation"""
    template_id: str = Field(..., description="Report template to use")
    title: str = Field(..., description="Report title")
    format: str = Field("pdf", description="Output format: pdf, html, json, csv")
    date_range_start: Optional[datetime] = Field(None, description="Report period start")
    date_range_end: Optional[datetime] = Field(None, description="Report period end")
    filters: Optional[dict] = Field(default_factory=dict, description="Additional filters")
    include_sections: Optional[list[str]] = Field(None, description="Sections to include")
    parameters: Optional[dict] = Field(default_factory=dict, description="Template-specific parameters")


class ReportResponse(BaseModel):
    """Report metadata response"""
    id: UUID
    title: str
    template_id: str
    format: str
    status: str = Field(..., description="Status: queued, generating, completed, failed")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledReport(BaseModel):
    """Scheduled report configuration"""
    id: UUID
    template_id: str
    title: str
    format: str
    schedule: str = Field(..., description="Cron expression for schedule")
    recipients: list[str] = Field(..., description="Email recipients")
    enabled: bool = Field(True, description="Whether schedule is active")
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# Template Endpoints
# ============================================================================

@router.get("/templates", response_model=list[ReportTemplate])
async def list_report_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List available report templates.
    """
    templates = [
        ReportTemplate(
            id="compliance-summary",
            name="Compliance Summary Report",
            description="Overview of compliance status across all frameworks",
            category="compliance",
            supported_formats=["pdf", "html", "json"],
            parameters={
                "frameworks": {"type": "array", "description": "Frameworks to include"},
                "include_evidence": {"type": "boolean", "default": True},
            },
        ),
        ReportTemplate(
            id="security-posture",
            name="AI Security Posture Report",
            description="Comprehensive security posture analysis with risk scores",
            category="security",
            supported_formats=["pdf", "html"],
            parameters={
                "include_trends": {"type": "boolean", "default": True},
                "risk_threshold": {"type": "number", "default": 50},
            },
        ),
        ReportTemplate(
            id="executive-dashboard",
            name="Executive Dashboard Report",
            description="High-level metrics and KPIs for leadership",
            category="executive",
            supported_formats=["pdf", "html"],
            parameters={
                "compare_period": {"type": "string", "enum": ["month", "quarter", "year"]},
            },
        ),
        ReportTemplate(
            id="model-inventory",
            name="AI Model Inventory Report",
            description="Complete inventory of AI models and their security status",
            category="audit",
            supported_formats=["pdf", "html", "csv", "json"],
            parameters={
                "include_inactive": {"type": "boolean", "default": False},
                "group_by": {"type": "string", "enum": ["provider", "risk_level", "team"]},
            },
        ),
        ReportTemplate(
            id="evaluation-results",
            name="Model Evaluation Results",
            description="Detailed evaluation results with benchmark comparisons",
            category="security",
            supported_formats=["pdf", "html", "json"],
            parameters={
                "model_ids": {"type": "array", "description": "Models to include"},
                "benchmarks": {"type": "array", "description": "Benchmarks to show"},
            },
        ),
        ReportTemplate(
            id="incident-report",
            name="Security Incident Report",
            description="Detailed incident analysis and remediation tracking",
            category="security",
            supported_formats=["pdf", "html"],
            parameters={
                "incident_ids": {"type": "array", "description": "Incidents to include"},
            },
        ),
        ReportTemplate(
            id="audit-trail",
            name="Audit Trail Report",
            description="Complete audit log of system activities",
            category="audit",
            supported_formats=["pdf", "csv", "json"],
            parameters={
                "user_filter": {"type": "string", "description": "Filter by user"},
                "action_types": {"type": "array", "description": "Action types to include"},
            },
        ),
    ]
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    return templates


@router.get("/templates/{template_id}", response_model=ReportTemplate)
async def get_report_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific report template.
    """
    templates = {
        "compliance-summary": ReportTemplate(
            id="compliance-summary",
            name="Compliance Summary Report",
            description="Overview of compliance status across all frameworks",
            category="compliance",
            supported_formats=["pdf", "html", "json"],
            parameters={
                "frameworks": {"type": "array", "description": "Frameworks to include"},
                "include_evidence": {"type": "boolean", "default": True},
            },
        ),
    }
    
    if template_id not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    
    return templates[template_id]


# ============================================================================
# Report Generation Endpoints
# ============================================================================

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a new report asynchronously.
    
    The report will be queued for generation. Poll the status endpoint
    or wait for webhook notification when complete.
    """
    from uuid import uuid4
    
    valid_formats = ["pdf", "html", "json", "csv"]
    if request.format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {valid_formats}"
        )
    
    report_id = uuid4()
    
    return ReportResponse(
        id=report_id,
        title=request.title,
        template_id=request.template_id,
        format=request.format,
        status="queued",
        file_size=None,
        download_url=None,
        date_range_start=request.date_range_start,
        date_range_end=request.date_range_end,
        created_by=current_user.get("username", "unknown"),
        created_at=datetime.utcnow(),
        completed_at=None,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    template_id: Optional[str] = Query(None, description="Filter by template"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List generated reports.
    """
    from uuid import uuid4
    
    reports = [
        ReportResponse(
            id=uuid4(),
            title="Q4 2024 Compliance Summary",
            template_id="compliance-summary",
            format="pdf",
            status="completed",
            file_size=2456789,
            download_url="/api/reports/download/abc123",
            date_range_start=datetime(2024, 10, 1),
            date_range_end=datetime(2024, 12, 31),
            created_by="admin",
            created_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            expires_at=datetime.utcnow() + timedelta(days=7),
        ),
        ReportResponse(
            id=uuid4(),
            title="Weekly Security Posture",
            template_id="security-posture",
            format="pdf",
            status="completed",
            file_size=1234567,
            download_url="/api/reports/download/def456",
            date_range_start=datetime.utcnow() - timedelta(days=7),
            date_range_end=datetime.utcnow(),
            created_by="security-team",
            created_at=datetime.utcnow() - timedelta(days=1),
            completed_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=30),
            expires_at=datetime.utcnow() + timedelta(days=6),
        ),
        ReportResponse(
            id=uuid4(),
            title="Model Inventory Export",
            template_id="model-inventory",
            format="json",
            status="generating",
            file_size=None,
            download_url=None,
            date_range_start=None,
            date_range_end=None,
            created_by="admin",
            created_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=None,
            expires_at=datetime.utcnow() + timedelta(days=7),
        ),
    ]
    
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific report.
    """
    return ReportResponse(
        id=report_id,
        title="Q4 2024 Compliance Summary",
        template_id="compliance-summary",
        format="pdf",
        status="completed",
        file_size=2456789,
        download_url=f"/api/reports/{report_id}/download",
        date_range_start=datetime(2024, 10, 1),
        date_range_end=datetime(2024, 12, 31),
        created_by="admin",
        created_at=datetime.utcnow() - timedelta(hours=2),
        completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download a completed report.
    """
    # In production, would fetch from storage and stream
    # For now, return a mock response
    import io
    
    content = f"Mock report content for report {report_id}"
    
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'
        }
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a generated report.
    """
    return None


# ============================================================================
# Scheduled Reports Endpoints
# ============================================================================

@router.get("/schedules", response_model=list[ScheduledReport])
async def list_scheduled_reports(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List scheduled report configurations.
    """
    from uuid import uuid4
    
    schedules = [
        ScheduledReport(
            id=uuid4(),
            template_id="compliance-summary",
            title="Weekly Compliance Summary",
            format="pdf",
            schedule="0 8 * * MON",  # Every Monday at 8 AM
            recipients=["compliance@company.com", "security@company.com"],
            enabled=True,
            last_run=datetime.utcnow() - timedelta(days=3),
            next_run=datetime.utcnow() + timedelta(days=4),
            created_at=datetime.utcnow() - timedelta(days=60),
        ),
        ScheduledReport(
            id=uuid4(),
            template_id="security-posture",
            title="Daily Security Posture",
            format="html",
            schedule="0 6 * * *",  # Every day at 6 AM
            recipients=["security-team@company.com"],
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=18),
            next_run=datetime.utcnow() + timedelta(hours=6),
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
    ]
    
    return schedules


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    template_id: str,
    title: str,
    format: str,
    schedule: str = Query(..., description="Cron expression"),
    recipients: list[str] = Query(..., description="Email recipients"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new scheduled report.
    """
    from uuid import uuid4
    
    return {
        "id": uuid4(),
        "template_id": template_id,
        "title": title,
        "format": format,
        "schedule": schedule,
        "recipients": recipients,
        "enabled": True,
        "created_at": datetime.utcnow(),
    }


@router.patch("/schedules/{schedule_id}")
async def update_scheduled_report(
    schedule_id: UUID,
    enabled: Optional[bool] = Query(None),
    schedule: Optional[str] = Query(None),
    recipients: Optional[list[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a scheduled report configuration.
    """
    return {
        "id": schedule_id,
        "updated_at": datetime.utcnow(),
        "message": "Schedule updated successfully",
    }


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_report(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a scheduled report.
    """
    return None
