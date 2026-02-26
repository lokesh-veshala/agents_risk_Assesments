from typing import Tuple, List
import statistics

class CanaryMonitoringAgent:
    """Monitors deployment health during canary phase"""
    
    def __init__(self, prometheus_client, datadog_client):
        self.prometheus = prometheus_client
        self.datadog = datadog_client
        self.baseline_metrics = {}
        self.alert_threshold = 0.15  # 15% deviation triggers concern
    
    def compare_versions(self, service: str, 
                        baseline_version: str, 
                        canary_version: str) -> Dict:
        """Compare metrics between stable and canary"""
        
        metrics_to_compare = [
            "request_latency_p99",
            "error_rate",
            "cpu_usage",
            "memory_usage",
            "cache_hit_ratio"
        ]
        
        comparison = {
            "service": service,
            "baseline_version": baseline_version,
            "canary_version": canary_version,
            "metric_comparisons": {},
            "issues_detected": [],
            "rollback_recommended": False
        }
        
        for metric in metrics_to_compare:
            baseline_data = self.prometheus.query_range(
                f'{metric}{{service="{service}", version="{baseline_version}"}}',
                start_time='-5m'
            )
            
            canary_data = self.prometheus.query_range(
                f'{metric}{{service="{service}", version="{canary_version}"}}',
                start_time='-5m'
            )
            
            baseline_avg = statistics.mean(baseline_data)
            canary_avg = statistics.mean(canary_data)
            
            # Calculate percentage change
            if baseline_avg > 0:
                pct_change = abs(canary_avg - baseline_avg) / baseline_avg
            else:
                pct_change = 0
            
            metric_result = {
                "baseline_avg": baseline_avg,
                "canary_avg": canary_avg,
                "percent_change": pct_change,
                "status": "DEGRADED" if pct_change > self.alert_threshold else "HEALTHY"
            }
            
            comparison["metric_comparisons"][metric] = metric_result
            
            if pct_change > self.alert_threshold:
                comparison["issues_detected"].append({
                    "metric": metric,
                    "severity": "HIGH" if pct_change > 0.25 else "MEDIUM",
                    "change_percent": round(pct_change * 100, 2)
                })
        
        # Autonomous rollback decision
        critical_issues = sum(1 for issue in comparison["issues_detected"] 
                             if issue["severity"] == "HIGH")
        if critical_issues >= 2:
            comparison["rollback_recommended"] = True
        
        return comparison
    
    def execute_intelligent_rollback(self, service: str, 
                                     canary_version: str,
                                     baseline_version: str) -> Dict:
        """Autonomous rollback execution"""
        
        rollback_action = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "rolled_back_from": canary_version,
            "rolled_back_to": baseline_version,
            "status": "IN_PROGRESS",
            "steps": [
                "Stopping new traffic to canary",
                "Draining in-flight requests",
                "Shifting traffic to baseline",
                "Waiting for metrics stabilization",
                "Terminating canary instances"
            ]
        }
        
        # Execute rollback with safeguards
        try:
            # Stop traffic shift
            self._stop_canary_traffic(service, canary_version)
            # Drain requests
            self._drain_canary_requests(service, canary_version)
            # Revert traffic
            self._revert_traffic(service, baseline_version)
            
            rollback_action["status"] = "COMPLETED"
        except Exception as e:
            rollback_action["status"] = "FAILED"
            rollback_action["error"] = str(e)
        
        return rollback_action
    
    def _stop_canary_traffic(self, service, version):
        # Implementation: update load balancer routing
        pass
    
    def _drain_canary_requests(self, service, version):
        # Implementation: wait for active connections to close
        pass
    
    def _revert_traffic(self, service, version):
        # Implementation: restore baseline routing
        pass