"""
SPM Scanner

Main scanner for AI Security Posture Management.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from guardstack.spm.checks import (
    BaseCheck,
    CheckResult,
    CheckSeverity,
    get_all_checks,
)
from guardstack.spm.inventory import AIInventory, AIAsset

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result of an SPM scan."""
    
    scan_id: str
    timestamp: str
    duration_ms: int
    assets_scanned: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    findings: list[dict[str, Any]]
    summary: dict[str, Any]
    compliance_score: float
    
    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 1.0
        return self.passed_checks / self.total_checks


class SPMScanner:
    """
    AI Security Posture Management Scanner.
    
    Performs comprehensive security assessments of AI systems:
    - Model security configuration
    - API security
    - Data protection
    - Access control
    - Deployment security
    - Supply chain security
    """
    
    def __init__(
        self,
        checks: Optional[list[BaseCheck]] = None,
        severity_filter: Optional[list[CheckSeverity]] = None,
        parallel_scans: int = 5,
    ) -> None:
        self.checks = checks or get_all_checks()
        self.severity_filter = severity_filter
        self.parallel_scans = parallel_scans
    
    async def scan(
        self,
        inventory: AIInventory,
        scan_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Run security scan across all assets in inventory.
        
        Args:
            inventory: AI asset inventory to scan
            scan_id: Optional scan identifier
        
        Returns:
            Complete scan results
        """
        start_time = time.time()
        scan_id = scan_id or f"scan_{int(time.time())}"
        
        all_findings = []
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        
        # Get assets to scan
        assets = inventory.list_assets()
        
        # Run checks for each asset
        for asset in assets:
            asset_results = await self._scan_asset(asset)
            
            for result in asset_results:
                total_checks += 1
                
                if result.passed:
                    passed_checks += 1
                else:
                    failed_checks += 1
                    all_findings.append({
                        "asset_id": asset.asset_id,
                        "asset_type": asset.asset_type,
                        "check_id": result.check_id,
                        "check_name": result.check_name,
                        "severity": result.severity.value,
                        "message": result.message,
                        "remediation": result.remediation,
                        "details": result.details,
                    })
        
        # Calculate compliance score
        compliance_score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Generate summary
        summary = self._generate_summary(all_findings, total_checks, passed_checks)
        
        return ScanResult(
            scan_id=scan_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            duration_ms=duration_ms,
            assets_scanned=len(assets),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            findings=all_findings,
            summary=summary,
            compliance_score=compliance_score,
        )
    
    async def _scan_asset(self, asset: AIAsset) -> list[CheckResult]:
        """Run all applicable checks against an asset."""
        results = []
        
        # Filter checks by asset type
        applicable_checks = [
            check for check in self.checks
            if check.applies_to(asset)
        ]
        
        # Filter by severity if specified
        if self.severity_filter:
            applicable_checks = [
                check for check in applicable_checks
                if check.severity in self.severity_filter
            ]
        
        # Run checks in parallel batches
        for i in range(0, len(applicable_checks), self.parallel_scans):
            batch = applicable_checks[i:i + self.parallel_scans]
            
            tasks = [check.run(asset) for check in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for check, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Check {check.check_id} failed: {result}")
                    results.append(CheckResult(
                        check_id=check.check_id,
                        check_name=check.name,
                        severity=check.severity,
                        passed=False,
                        message=f"Check error: {str(result)}",
                    ))
                else:
                    results.append(result)
        
        return results
    
    def _generate_summary(
        self,
        findings: list[dict[str, Any]],
        total_checks: int,
        passed_checks: int,
    ) -> dict[str, Any]:
        """Generate scan summary."""
        # Count by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        
        for finding in findings:
            severity = finding.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Count by asset type
        asset_type_counts: dict[str, int] = {}
        for finding in findings:
            asset_type = finding.get("asset_type", "unknown")
            asset_type_counts[asset_type] = asset_type_counts.get(asset_type, 0) + 1
        
        # Top findings
        top_findings = sorted(
            findings,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(
                x.get("severity", "medium"), 2
            ),
        )[:10]
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": len(findings),
            "pass_rate": passed_checks / total_checks if total_checks > 0 else 1.0,
            "severity_breakdown": severity_counts,
            "asset_type_breakdown": asset_type_counts,
            "top_findings": top_findings,
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
        }
    
    async def scan_single_asset(
        self,
        asset: AIAsset,
    ) -> list[CheckResult]:
        """Scan a single asset."""
        return await self._scan_asset(asset)
    
    def get_check_coverage(self) -> dict[str, list[str]]:
        """Get coverage of checks by category."""
        coverage: dict[str, list[str]] = {}
        
        for check in self.checks:
            category = check.category
            if category not in coverage:
                coverage[category] = []
            coverage[category].append(check.check_id)
        
        return coverage


class ContinuousScanner:
    """
    Continuous security scanning with scheduling.
    """
    
    def __init__(
        self,
        scanner: SPMScanner,
        inventory: AIInventory,
        scan_interval_seconds: int = 3600,
    ) -> None:
        self.scanner = scanner
        self.inventory = inventory
        self.scan_interval = scan_interval_seconds
        self._running = False
        self._last_scan: Optional[ScanResult] = None
    
    async def start(self) -> None:
        """Start continuous scanning."""
        self._running = True
        
        while self._running:
            try:
                self._last_scan = await self.scanner.scan(self.inventory)
                logger.info(
                    f"Scan complete: {self._last_scan.compliance_score:.1f}% compliance"
                )
            except Exception as e:
                logger.error(f"Scan failed: {e}")
            
            await asyncio.sleep(self.scan_interval)
    
    def stop(self) -> None:
        """Stop continuous scanning."""
        self._running = False
    
    @property
    def last_scan(self) -> Optional[ScanResult]:
        """Get most recent scan result."""
        return self._last_scan
