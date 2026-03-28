"""
Health check endpoints and monitoring for FireFeed API

This module provides comprehensive health checks for all system components
including database, Redis, external services, and overall system health.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from firefeed_api.dependencies import get_metrics_collector
from firefeed_api.monitoring.metrics import get_metrics_collector, get_alert_manager
from firefeed_api.routers.internal import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthCheckResult(BaseModel):
    """Result of a health check"""
    status: str  # 'healthy', 'unhealthy', 'degraded'
    component: str
    message: str
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint"""
    status: str  # 'healthy', 'unhealthy', 'degraded'
    timestamp: datetime
    uptime: float
    version: str
    checks: List[HealthCheckResult]
    alerts: List[Dict[str, Any]]


class DatabaseHealthChecker:
    """Health checker for database connections"""
    
    def __init__(self, db):
        self.db = db
    
    async def check(self) -> HealthCheckResult:
        """Check database health"""
        start_time = time.perf_counter()
        
        try:
            # Test basic connection
            result = await self.db.fetch_one("SELECT 1 as test")
            if result is None:
                raise Exception("Database returned no result")
            
            # Test write operation
            test_id = f"health_check_{int(time.time())}"
            await self.db.execute(
                "INSERT INTO health_check (id, created_at) VALUES ($1, NOW())",
                (test_id,)
            )
            
            # Test read operation
            check_result = await self.db.fetch_one(
                "SELECT id, created_at FROM health_check WHERE id = $1",
                (test_id,)
            )
            
            if check_result is None:
                raise Exception("Failed to read health check record")
            
            # Clean up test record
            await self.db.execute(
                "DELETE FROM health_check WHERE id = $1",
                (test_id,)
            )
            
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="healthy",
                component="database",
                message="Database connection and operations working correctly",
                response_time=response_time,
                details={
                    "connection_test": True,
                    "read_write_test": True,
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="unhealthy",
                component="database",
                message=f"Database health check failed: {str(e)}",
                response_time=response_time,
                details={
                    "error": str(e),
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )


class RedisHealthChecker:
    """Health checker for Redis connections"""
    
    def __init__(self, redis):
        self.redis = redis
    
    async def check(self) -> HealthCheckResult:
        """Check Redis health"""
        start_time = time.perf_counter()
        
        try:
            # Test basic connection
            pong = await self.redis.ping()
            if not pong:
                raise Exception("Redis ping failed")
            
            # Test write operation
            test_key = f"health_check_{int(time.time())}"
            test_value = "test_value"
            
            await self.redis.set(test_key, test_value, ex=60)
            
            # Test read operation
            retrieved_value = await self.redis.get(test_key)
            
            if retrieved_value != test_value.encode():
                raise Exception("Redis read/write mismatch")
            
            # Clean up test key
            await self.redis.delete(test_key)
            
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="healthy",
                component="redis",
                message="Redis connection and operations working correctly",
                response_time=response_time,
                details={
                    "ping_test": True,
                    "read_write_test": True,
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="unhealthy",
                component="redis",
                message=f"Redis health check failed: {str(e)}",
                response_time=response_time,
                details={
                    "error": str(e),
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )


class InternalAPIHealthChecker:
    """Health checker for internal API services"""
    
    def __init__(self, internal_api_url: str, service_token: str):
        self.internal_api_url = internal_api_url
        self.service_token = service_token
    
    async def check(self) -> HealthCheckResult:
        """Check internal API health"""
        start_time = time.perf_counter()
        
        try:
            import httpx
            
            # Test internal API health endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.internal_api_url}/api/v1/internal/health",
                    headers={"X-Service-Token": self.service_token},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Internal API returned status {response.status_code}")
                
                response_data = response.json()
                
                response_time = time.perf_counter() - start_time
                
                return HealthCheckResult(
                    status="healthy",
                    component="internal_api",
                    message="Internal API is responding correctly",
                    response_time=response_time,
                    details={
                        "status_code": response.status_code,
                        "response_data": response_data,
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="unhealthy",
                component="internal_api",
                message=f"Internal API health check failed: {str(e)}",
                response_time=response_time,
                details={
                    "error": str(e),
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )


class SystemHealthChecker:
    """Health checker for system resources"""
    
    def check(self) -> HealthCheckResult:
        """Check system health"""
        start_time = time.perf_counter()
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define thresholds
            cpu_threshold = 90.0
            memory_threshold = 90.0
            disk_threshold = 90.0
            
            # Check thresholds
            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"CPU usage too high: {cpu_percent}%")
            if memory.percent > memory_threshold:
                issues.append(f"Memory usage too high: {memory.percent}%")
            if disk.percent > disk_threshold:
                issues.append(f"Disk usage too high: {disk.percent}%")
            
            response_time = time.perf_counter() - start_time
            
            if issues:
                return HealthCheckResult(
                    status="degraded",
                    component="system",
                    message=f"System resources under pressure: {'; '.join(issues)}",
                    response_time=response_time,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent,
                        "issues": issues,
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    timestamp=datetime.now()
                )
            else:
                return HealthCheckResult(
                    status="healthy",
                    component="system",
                    message="System resources within acceptable limits",
                    response_time=response_time,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent,
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except ImportError:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="healthy",
                component="system",
                message="System monitoring not available (psutil not installed)",
                response_time=response_time,
                details={
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )
        
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="unhealthy",
                component="system",
                message=f"System health check failed: {str(e)}",
                response_time=response_time,
                details={
                    "error": str(e),
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )


class ApplicationHealthChecker:
    """Health checker for application-specific metrics"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
    
    def check(self) -> HealthCheckResult:
        """Check application health"""
        start_time = time.perf_counter()
        
        try:
            # Get recent metrics
            summary = self.metrics_collector.get_request_summary(timedelta(minutes=5))
            health_metrics = self.metrics_collector.get_health_metrics()
            
            # Define thresholds
            error_rate_threshold = 10.0  # 10% error rate
            response_time_threshold = 5.0  # 5 seconds
            
            issues = []
            if summary['error_rate'] > error_rate_threshold:
                issues.append(f"Error rate too high: {summary['error_rate']:.2f}%")
            if summary['average_response_time'] > response_time_threshold:
                issues.append(f"Average response time too high: {summary['average_response_time']:.3f}s")
            
            response_time = time.perf_counter() - start_time
            
            if issues:
                return HealthCheckResult(
                    status="degraded",
                    component="application",
                    message=f"Application performance issues: {'; '.join(issues)}",
                    response_time=response_time,
                    details={
                        "error_rate": summary['error_rate'],
                        "average_response_time": summary['average_response_time'],
                        "active_users": health_metrics['active_users'],
                        "total_requests": summary['total_requests'],
                        "issues": issues,
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    timestamp=datetime.now()
                )
            else:
                return HealthCheckResult(
                    status="healthy",
                    component="application",
                    message="Application performance within acceptable limits",
                    response_time=response_time,
                    details={
                        "error_rate": summary['error_rate'],
                        "average_response_time": summary['average_response_time'],
                        "active_users": health_metrics['active_users'],
                        "total_requests": summary['total_requests'],
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            response_time = time.perf_counter() - start_time
            
            return HealthCheckResult(
                status="unhealthy",
                component="application",
                message=f"Application health check failed: {str(e)}",
                response_time=response_time,
                details={
                    "error": str(e),
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now()
            )


class HealthChecker:
    """Main health checker orchestrating all checks"""
    
    def __init__(self, db, redis, internal_api_url: str, service_token: str):
        self.checkers = {
            "database": DatabaseHealthChecker(db),
            "redis": RedisHealthChecker(redis),
            "internal_api": InternalAPIHealthChecker(internal_api_url, service_token),
            "system": SystemHealthChecker(),
            "application": ApplicationHealthChecker(get_metrics_collector())
        }
    
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks concurrently"""
        tasks = [checker.check() for checker in self.checkers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_name = list(self.checkers.keys())[i]
                final_results.append(HealthCheckResult(
                    status="unhealthy",
                    component=component_name,
                    message=f"Health check failed with exception: {str(result)}",
                    timestamp=datetime.now()
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def determine_overall_status(self, results: List[HealthCheckResult]) -> str:
        """Determine overall system status based on individual check results"""
        if any(r.status == "unhealthy" for r in results):
            return "unhealthy"
        elif any(r.status == "degraded" for r in results):
            return "degraded"
        else:
            return "healthy"


# Global uptime tracker
_start_time = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds"""
    return time.time() - _start_time


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    metrics_collector=Depends(get_metrics_collector),
    alert_manager=Depends(get_alert_manager)
):
    """Comprehensive health check endpoint"""
    try:
        # Get database connection
        db = await get_db_connection()
        
        # Get Redis connection (placeholder for now)
        from firefeed_core.cache import get_redis_pool
        redis = get_redis_pool()
        
        # Run all health checks
        health_checker = HealthChecker(
            db=db,
            redis=redis,
            internal_api_url="http://localhost:8001",  # Default internal API URL
            service_token="test-service-token"  # Default service token
        )
        
        checks = await health_checker.run_all_checks()
        overall_status = health_checker.determine_overall_status(checks)
        
        # Get alerts
        alerts = alert_manager.get_alerts()
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            uptime=get_uptime(),
            version="1.0.0",  # This should be dynamic
            checks=checks,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": get_uptime()
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - ensures all dependencies are available"""
    try:
        # Get database connection
        db = await get_db_connection()
        
        # Check database
        await db.fetch_one("SELECT 1")
        
        # Get Redis connection (placeholder for now)
        from firefeed_core.cache import get_redis_pool
        redis = get_redis_pool()
        
        # Check Redis
        await redis.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "database": "healthy",
                "redis": "healthy"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/health/live")
async def liveness_check():
    """Liveness check - ensures the service is running"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime": get_uptime()
    }


@router.get("/metrics")
async def metrics_endpoint(metrics_collector=Depends(get_metrics_collector)):
    """Prometheus metrics endpoint"""
    from firefeed_api.monitoring.metrics import get_prometheus_metrics
    return get_prometheus_metrics()


@router.get("/alerts")
async def alerts_endpoint(alert_manager=Depends(get_alert_manager)):
    """Get current alerts"""
    return {
        "alerts": alert_manager.get_alerts(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status")
async def status_endpoint(
    metrics_collector=Depends(get_metrics_collector)
):
    """Get detailed system status"""
    try:
        # Get database connection
        db = await get_db_connection()
        
        # Get Redis connection (placeholder for now)
        from firefeed_core.cache import get_redis_pool
        redis = get_redis_pool()
        
        # Get database status
        db_result = await db.fetch_one("SELECT COUNT(*) as user_count FROM users")
        user_count = db_result['user_count'] if db_result else 0
        
        # Get Redis status
        redis_info = await redis.info()
        redis_memory = redis_info.get('used_memory_human', 'unknown')
        
        # Get metrics summary
        summary = metrics_collector.get_request_summary()
        health_metrics = metrics_collector.get_health_metrics()
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime": get_uptime(),
            "database": {
                "status": "connected",
                "user_count": user_count
            },
            "redis": {
                "status": "connected",
                "memory_usage": redis_memory
            },
            "metrics": {
                "total_requests": summary['total_requests'],
                "error_rate": summary['error_rate'],
                "average_response_time": summary['average_response_time'],
                "requests_per_minute": summary['requests_per_minute'],
                "active_users": health_metrics['active_users']
            }
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Background health check task
async def health_check_task():
    """Background task to periodically run health checks"""
    while True:
        try:
            # This could be used to trigger periodic health checks
            # or update health status in a cache
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in health check task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying