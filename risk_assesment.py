import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class RiskFactor:
    """Represents a single risk factor in the assessment"""
    name: str
    severity: int  # 0-100
    category: str  # "security", "testing", "compliance", "infrastructure"
    description: str
    mitigation: Optional[str] = None

@dataclass
class DeploymentContext:
    """Context information for a deployment"""
    service_name: str
    version: str
    environment: str
    change_set: List[str]
    deployed_by: str
    deployment_time: datetime

class SecurityEvaluator:
    """Evaluates security-related risks"""
    
    def __init__(self, security_db: Dict):
        self.security_db = security_db
    
    def evaluate(self, service: str, version: str) -> List[RiskFactor]:
        """Assess security vulnerabilities and compliance gaps"""
        factors = []
        
        # Check for known vulnerabilities in dependencies
        scan_results = self.security_db.get(service, {})
        vuln_count = scan_results.get("vulnerability_count", 0)
        
        if vuln_count > 0:
            factors.append(RiskFactor(
                name="Known Vulnerabilities Detected",
                severity=min(50, vuln_count * 10),
                category="security",
                description=f"{vuln_count} vulnerabilities found in dependency scan",
                mitigation="Review and patch vulnerabilities before deployment"
            ))
        
        # Check SSL certificate validity
        cert_expires_days = scan_results.get("cert_expires_in_days", 365)
        if cert_expires_days < 30:
            factors.append(RiskFactor(
                name="SSL Certificate Expiring Soon",
                severity=40,
                category="security",
                description=f"SSL certificate expires in {cert_expires_days} days",
                mitigation="Renew certificate before expiration"
            ))
        
        # Check for hardcoded secrets in code
        if scan_results.get("secrets_detected", False):
            factors.append(RiskFactor(
                name="Hardcoded Secrets Detected",
                severity=80,
                category="security",
                description="Hardcoded credentials found in codebase",
                mitigation="Remove secrets and use secret management service"
            ))
        
        return factors

class TestingEvaluator:
    """Evaluates testing-related risks"""
    
    def __init__(self, test_db: Dict):
        self.test_db = test_db
    
    def evaluate(self, service: str, version: str) -> List[RiskFactor]:
        """Assess test coverage and execution results"""
        factors = []
        
        test_results = self.test_db.get(service, {})
        
        # Check code coverage
        coverage = test_results.get("code_coverage", 0)
        if coverage < 70:
            factors.append(RiskFactor(
                name="Low Code Coverage",
                severity=(100 - coverage) // 2,
                category="testing",
                description=f"Code coverage is {coverage}% (target: 70%+)",
                mitigation="Add unit tests and integration tests"
            ))
        
        # Check test execution status
        if test_results.get("failed_tests", 0) > 0:
            factors.append(RiskFactor(
                name="Test Failures Detected",
                severity=60,
                category="testing",
                description=f"{test_results['failed_tests']} tests failed",
                mitigation="Fix failing tests before deployment"
            ))
        
        # Check performance test results
        perf_regression = test_results.get("performance_regression_percent", 0)
        if perf_regression > 5:
            factors.append(RiskFactor(
                name="Performance Regression Detected",
                severity=min(50, perf_regression * 2),
                category="testing",
                description=f"Performance degradation: {perf_regression}%",
                mitigation="Optimize code or increase resource allocation"
            ))
        
        return factors

class ComplianceEvaluator:
    """Evaluates compliance and governance risks"""
    
    def __init__(self, compliance_db: Dict):
        self.compliance_db = compliance_db
    
    def evaluate(self, service: str, version: str, environment: str) -> List[RiskFactor]:
        """Assess compliance with organizational policies"""
        factors = []
        
        policies = self.compliance_db.get("policies", {})
        
        # Check change management approval
        if not self.compliance_db.get("change_approved", False):
            factors.append(RiskFactor(
                name="Change Not Approved",
                severity=100,
                category="compliance",
                description="Release not approved by change management board",
                mitigation="Submit and obtain change approval"
            ))
        
        # Check deployment window restrictions
        if environment == "production":
            restricted_windows = policies.get("restricted_deployment_windows", [])
            deployment_hour = datetime.now().hour
            
            if deployment_hour in restricted_windows:
                factors.append(RiskFactor(
                    name="Deployment Outside Approved Window",
                    severity=40,
                    category="compliance",
                    description=f"Current hour {deployment_hour} is in restricted window",
                    mitigation="Deploy during approved maintenance windows"
                ))
        
        # Check data residency compliance
        if policies.get("data_residency_required"):
            if not self.compliance_db.get("deployment_in_correct_region", True):
                factors.append(RiskFactor(
                    name="Data Residency Violation",
                    severity=85,
                    category="compliance",
                    description="Service not deployed in compliant region",
                    mitigation="Redeploy to correct geographic region"
                ))
        
        return factors

class InfrastructureEvaluator:
    """Evaluates infrastructure and operational risks"""
    
    def __init__(self, infra_db: Dict):
        self.infra_db = infra_db
    
    def evaluate(self, service: str, version: str) -> List[RiskFactor]:
        """Assess infrastructure health and capacity"""
        factors = []
        
        infra_status = self.infra_db.get(service, {})
        
        # Check cluster health
        cluster_health = infra_status.get("cluster_health", 100)
        if cluster_health < 80:
            factors.append(RiskFactor(
                name="Degraded Cluster Health",
                severity=(100 - cluster_health),
                category="infrastructure",
                description=f"Cluster health score: {cluster_health}%",
                mitigation="Investigate and resolve cluster issues before deployment"
            ))
        
        # Check disk space
        disk_usage = infra_status.get("disk_usage_percent", 0)
        if disk_usage > 85:
            factors.append(RiskFactor(
                name="High Disk Usage",
                severity=30,
                category="infrastructure",
                description=f"Disk usage: {disk_usage}%",
                mitigation="Clean up old logs/data or expand storage"
            ))
        
        # Check deployment pipeline load
        pipeline_queue = infra_status.get("deployments_in_queue", 0)
        if pipeline_queue > 5:
            factors.append(RiskFactor(
                name="Pipeline Congestion",
                severity=20,
                category="infrastructure",
                description=f"{pipeline_queue} deployments queued",
                mitigation="Wait for pipeline capacity or stagger deployment"
            ))
        
        return factors

class RiskAssessmentAgent:
    """Autonomous agent that assesses deployment risk"""
    
    def __init__(self, security_db: Dict, test_db: Dict, compliance_db: Dict, infra_db: Dict):
        self.security_evaluator = SecurityEvaluator(security_db)
        self.testing_evaluator = TestingEvaluator(test_db)
        self.compliance_evaluator = ComplianceEvaluator(compliance_db)
        self.infrastructure_evaluator = InfrastructureEvaluator(infra_db)
        self.learning_history = []  # Track deployment outcomes for learning
    
    def assess(self, context: DeploymentContext) -> Dict:
        """Main decision-making method"""
        logger.info(f"Starting risk assessment for {context.service_name}:{context.version}")
        
        # Parallel evaluation across all dimensions
        all_factors = []
        all_factors.extend(self.security_evaluator.evaluate(context.service_name, context.version))
        all_factors.extend(self.testing_evaluator.evaluate(context.service_name, context.version))
        all_factors.extend(self.compliance_evaluator.evaluate(context.service_name, context.version, context.environment))
        all_factors.extend(self.infrastructure_evaluator.evaluate(context.service_name, context.version))
        
        # Calculate composite risk score
        risk_score = self._calculate_risk_score(all_factors)
        risk_level = self._classify_risk_level(risk_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_score, all_factors, context)
        
        # Build decision report
        report = {
            "timestamp": datetime.now().isoformat(),
            "service": context.service_name,
            "version": context.version,
            "environment": context.environment,
            "risk_score": risk_score,
            "risk_level": risk_level.name,
            "factors": [
                {
                    "name": f.name,
                    "severity": f.severity,
                    "category": f.category,
                    "description": f.description,
                    "mitigation": f.mitigation
                }
                for f in sorted(all_factors, key=lambda x: x.severity, reverse=True)
            ],
            "recommendation": recommendation,
            "factors_by_category": self._categorize_factors(all_factors),
            "autonomous_decision": risk_score < 30
        }
        
        # Log decision for learning
        self.learning_history.append(report)
        
        return report
    
    def _calculate_risk_score(self, factors: List[RiskFactor]) -> int:
        """Calculate composite risk using weighted algorithm"""
        if not factors:
            return 0
        
        # Weight by category (compliance > security > testing > infrastructure)
        weights = {
            "compliance": 1.5,
            "security": 1.3,
            "testing": 1.0,
            "infrastructure": 0.8
        }
        
        weighted_sum = sum(
            f.severity * weights.get(f.category, 1.0)
            for f in factors
        )
        
        total_weight = sum(
            weights.get(f.category, 1.0)
            for f in factors
        )
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 0
    
    def _classify_risk_level(self, score: int) -> RiskLevel:
        """Classify risk into categories"""
        if score < 20:
            return RiskLevel.LOW
        elif score < 45:
            return RiskLevel.MEDIUM
        elif score < 70:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _generate_recommendation(self, score: int, factors: List[RiskFactor], context: DeploymentContext) -> str:
        """Generate intelligent recommendation based on factors"""
        if score < 20:
            return "✓ APPROVED: Deploy immediately. All systems green."
        elif score < 45:
            return "⚠ CONDITIONAL: Deploy with caution. Review mitigations below."
        elif score < 70:
            return "🛑 MANUAL REVIEW REQUIRED: Address critical factors before deployment."
        else:
            return "❌ BLOCKED: Critical issues detected. Do not proceed without resolution."
    
    def _categorize_factors(self, factors: List[RiskFactor]) -> Dict:
        """Organize factors by category"""
        categorized = {}
        for factor in factors:
            if factor.category not in categorized:
                categorized[factor.category] = []
            categorized[factor.category].append({
                "name": factor.name,
                "severity": factor.severity
            })
        return categorized
    
    def get_deployment_insights(self) -> Dict:
        """Analyze historical patterns for learning"""
        if not self.learning_history:
            return {}
        
        insights = {
            "total_assessments": len(self.learning_history),
            "avg_risk_score": sum(d["risk_score"] for d in self.learning_history) / len(self.learning_history),
            "approved_rate": sum(1 for d in self.learning_history if d["autonomous_decision"]) / len(self.learning_history),
            "most_common_issues": self._analyze_common_issues()
        }
        
        return insights
    
    def _analyze_common_issues(self) -> List[str]:
        """Identify patterns in recurring issues"""
        issue_counts = {}
        for report in self.learning_history:
            for factor in report["factors"]:
                issue_name = factor["name"]
                issue_counts[issue_name] = issue_counts.get(issue_name, 0) + 1
        
        return sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]

# Example usage
if __name__ == "__main__":
    # Sample data sources (in production, these would connect to actual systems)
    security_db = {
        "payment-service": {
            "vulnerability_count": 2,
            "cert_expires_in_days": 45,
            "secrets_detected": False
        }
    }
    
    test_db = {
        "payment-service": {
            "code_coverage": 82,
            "failed_tests": 0,
            "performance_regression_percent": 2.3
        }
    }
    
    compliance_db = {
        "change_approved": True,
        "policies": {
            "restricted_deployment_windows": [2, 3, 4],  # 2-4 AM
            "data_residency_required": True
        },
        "deployment_in_correct_region": True
    }
    
    infra_db = {
        "payment-service": {
            "cluster_health": 94,
            "disk_usage_percent": 62,
            "deployments_in_queue": 1
        }
    }
    
    # Initialize agent
    agent = RiskAssessmentAgent(security_db, test_db, compliance_db, infra_db)
    
    # Create deployment context
    context = DeploymentContext(
        service_name="payment-service",
        version="2.4.1",
        environment="production",
        change_set=["feature/payment-retry-logic", "bugfix/timeout-handling"],
        deployed_by="sarah.chen",
        deployment_time=datetime.now()
    )
    
    # Run assessment
    result = agent.assess(context)
    
    # Print results
    print("\n" + "="*70)
    print("RISK ASSESSMENT REPORT")
    print("="*70)
    print(json.dumps(result, indent=2, default=str))
    print("\nAUTONOMOUS DECISION:", "✓ PROCEED" if result["autonomous_decision"] else "⚠ MANUAL REVIEW REQUIRED")
    print("="*70)