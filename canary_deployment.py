class CanaryDeploymentAgent:
    """Orchestrates canary deployments on Azure"""
    
    def __init__(self, app_service_client, app_insights_client):
        self.app_service = app_service_client
        self.app_insights = app_insights_client
    
    async def deploy_canary(self,
                           app_name: str,
                           new_version: str,
                           canary_traffic_percent: int = 5) -> Dict:
        """
        Gradual traffic shift with continuous monitoring
        """
        
        logger.info(f"Starting canary deployment for {app_name}")
        
        canary_stages = [5, 25, 50, 100]  # Gradually increase traffic %
        monitoring_duration_per_stage = 300  # 5 minutes
        
        result = {
            "deployment_id": f"canary-{datetime.now().timestamp()}",
            "stages": [],
            "status": "IN_PROGRESS"
        }
        
        for stage_num, traffic_pct in enumerate(canary_stages, 1):
            logger.info(f"\n[Canary Stage {stage_num}] Shifting {traffic_pct}% traffic to {new_version}")
            
            # Deploy to staging slot
            if stage_num == 1:
                await self._deploy_to_slot(app_name, "staging", new_version)
            
            # Update traffic split
            await self._set_traffic_split(
                app_name=app_name,
                production_percent=100 - traffic_pct,
                staging_percent=traffic_pct
            )
            
            # Monitor for issues
            logger.info(f"Monitoring for {monitoring_duration_per_stage} seconds...")
            metrics = await self._collect_metrics(
                app_name=app_name,
                duration_seconds=monitoring_duration_per_stage
            )
            
            # Evaluate metrics
            evaluation = self._evaluate_canary_metrics(metrics)
            
            result["stages"].append({
                "stage": stage_num,
                "traffic_percent": traffic_pct,
                "metrics": metrics,
                "evaluation": evaluation,
                "passed": evaluation["healthy"]
            })
            
            if not evaluation["healthy"]:
                logger.error(f"Canary health check failed: {evaluation['reason']}")
                
                # Instant rollback
                await self._set_traffic_split(
                    app_name=app_name,
                    production_percent=100,
                    staging_percent=0
                )
                
                result["status"] = "ROLLED_BACK"
                result["rollback_reason"] = evaluation["reason"]
                return result
            
            logger.info(f"✓ Stage {stage_num} passed. Proceeding...")
        
        # Final: Swap slots
        logger.info("\nCanary successful! Swapping production slot...")
        await self._swap_slots(app_name, "production", "staging")
        
        result["status"] = "SUCCESS"
        return result
    
    def _evaluate_canary_metrics(self, metrics: Dict) -> Dict:
        """Intelligent metric evaluation"""
        
        error_rate = metrics.get("error_rate", 0)
        latency_p99 = metrics.get("latency_p99_ms", 0)
        cpu_usage = metrics.get("cpu_percent", 0)
        
        issues = []
        
        if error_rate > 2.0:
            issues.append(f"Error rate {error_rate}% > 2% threshold")
        
        if latency_p99 > 150:
            issues.append(f"P99 latency {latency_p99}ms > 150ms threshold")
        
        if cpu_usage > 80:
            issues.append(f"CPU usage {cpu_usage}% > 80% threshold")
        
        return {
            "healthy": len(issues) == 0,
            "reason": "; ".join(issues) if issues else "All metrics healthy",
            "error_rate": error_rate,
            "latency_p99_ms": latency_p99,
            "cpu_percent": cpu_usage
        }
    
    async def _deploy_to_slot(self, app_name, slot, version):
        # Deploy to Azure slot
        pass
    
    async def _set_traffic_split(self, app_name, production_percent, staging_percent):
        # Update traffic routing
        pass
    
    async def _collect_metrics(self, app_name, duration_seconds):
        # Query App Insights
        pass
    
    async def _swap_slots(self, app_name, primary, secondary):
        # Swap slots
        pass
