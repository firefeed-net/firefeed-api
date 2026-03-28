"""
Metrics collection and monitoring for FireFeed API

This module provides comprehensive metrics collection for monitoring
API performance, usage patterns, and system health.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Container for request metrics"""
    method: str
    path: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    error_type: Optional[str] = None


class MetricsCollector:
    """Central metrics collector for the API"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Prometheus metrics
        self.request_count = Counter(
            'firefeed_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'firefeed_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'firefeed_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'firefeed_database_connections',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.redis_operations = Counter(
            'firefeed_redis_operations_total',
            'Total number of Redis operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Summary(
            'firefeed_cache_operations',
            'Cache operations summary',
            ['operation'],
            registry=self.registry
        )
        
        self.error_count = Counter(
            'firefeed_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        # In-memory metrics for real-time analysis
        self.request_history: deque = deque(maxlen=10000)
        self.user_sessions: Dict[str, datetime] = {}
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'errors': 0
        })
        
        # Rate limiting metrics
        self.rate_limit_hits = Counter(
            'firefeed_rate_limit_hits_total',
            'Total number of rate limit hits',
            ['endpoint'],
            registry=self.registry
        )
        
        # Business metrics
        self.user_registrations = Counter(
            'firefeed_user_registrations_total',
            'Total number of user registrations',
            registry=self.registry
        )
        
        self.rss_items_processed = Counter(
            'firefeed_rss_items_processed_total',
            'Total number of RSS items processed',
            ['source', 'status'],
            registry=self.registry
        )
        
        self.translation_requests = Counter(
            'firefeed_translation_requests_total',
            'Total number of translation requests',
            ['source_language', 'target_language'],
            registry=self.registry
        )
    
    def record_request(self, metrics: RequestMetrics):
        """Record a request metric"""
        # Update Prometheus metrics
        self.request_count.labels(
            method=metrics.method,
            endpoint=metrics.endpoint or metrics.path,
            status_code=str(metrics.status_code)
        ).inc()
        
        self.request_duration.labels(
            method=metrics.method,
            endpoint=metrics.endpoint or metrics.path
        ).observe(metrics.response_time)
        
        # Update in-memory metrics
        self.request_history.append(metrics)
        
        if metrics.user_id:
            self.user_sessions[metrics.user_id] = metrics.timestamp
        
        # Update endpoint statistics
        endpoint_key = metrics.endpoint or metrics.path
        stats = self.endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_time'] += metrics.response_time
        stats['min_time'] = min(stats['min_time'], metrics.response_time)
        stats['max_time'] = max(stats['max_time'], metrics.response_time)
        
        if metrics.error_type:
            stats['errors'] += 1
            self.error_count.labels(
                error_type=metrics.error_type,
                endpoint=endpoint_key
            ).inc()
    
    def record_redis_operation(self, operation: str, status: str, duration: float = None):
        """Record a Redis operation"""
        self.redis_operations.labels(
            operation=operation,
            status=status
        ).inc()
        
        if duration is not None:
            self.cache_hit_ratio.labels(operation=operation).observe(duration)
    
    def record_rate_limit_hit(self, endpoint: str):
        """Record a rate limit hit"""
        self.rate_limit_hits.labels(endpoint=endpoint).inc()
    
    def record_user_registration(self):
        """Record a user registration"""
        self.user_registrations.inc()
    
    def record_rss_item_processed(self, source: str, status: str):
        """Record an RSS item processing event"""
        self.rss_items_processed.labels(
            source=source,
            status=status
        ).inc()
    
    def record_translation_request(self, source_language: str, target_language: str):
        """Record a translation request"""
        self.translation_requests.labels(
            source_language=source_language,
            target_language=target_language
        ).inc()
    
    def update_active_users(self):
        """Update the count of active users"""
        # Consider users active if they made a request in the last 5 minutes
        cutoff = datetime.now() - timedelta(minutes=5)
        active_count = sum(1 for last_seen in self.user_sessions.values() if last_seen > cutoff)
        self.active_users.set(active_count)
    
    def get_endpoint_statistics(self, endpoint: str = None) -> Dict[str, Any]:
        """Get statistics for an endpoint or all endpoints"""
        if endpoint:
            return self.endpoint_stats.get(endpoint, {})
        
        # Return statistics for all endpoints
        stats = {}
        for ep, data in self.endpoint_stats.items():
            if data['count'] > 0:
                avg_time = data['total_time'] / data['count']
                error_rate = (data['errors'] / data['count']) * 100
                stats[ep] = {
                    'count': data['count'],
                    'average_response_time': round(avg_time, 3),
                    'min_response_time': round(data['min_time'], 3),
                    'max_response_time': round(data['max_time'], 3),
                    'error_count': data['errors'],
                    'error_rate': round(error_rate, 2)
                }
        return stats
    
    def get_request_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get a summary of requests in the specified time window"""
        cutoff = datetime.now() - time_window
        recent_requests = [r for r in self.request_history if r.timestamp > cutoff]
        
        if not recent_requests:
            return {
                'total_requests': 0,
                'average_response_time': 0.0,
                'error_rate': 0.0,
                'requests_per_minute': 0.0,
                'top_endpoints': [],
                'status_codes': {}
            }
        
        # Calculate summary statistics
        total_requests = len(recent_requests)
        total_time = sum(r.response_time for r in recent_requests)
        error_count = sum(1 for r in recent_requests if r.status_code >= 400)
        
        # Count status codes
        status_codes = defaultdict(int)
        for r in recent_requests:
            status_codes[str(r.status_code)] += 1
        
        # Count endpoints
        endpoints = defaultdict(int)
        for r in recent_requests:
            endpoint = r.endpoint or r.path
            endpoints[endpoint] += 1
        
        # Get top endpoints
        top_endpoints = sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate rates
        time_diff = (datetime.now() - cutoff).total_seconds() / 60  # minutes
        requests_per_minute = total_requests / time_diff if time_diff > 0 else 0
        
        return {
            'total_requests': total_requests,
            'average_response_time': round(total_time / total_requests, 3),
            'error_rate': round((error_count / total_requests) * 100, 2),
            'requests_per_minute': round(requests_per_minute, 2),
            'top_endpoints': [{'endpoint': ep, 'count': count} for ep, count in top_endpoints],
            'status_codes': dict(status_codes)
        }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for the API"""
        self.update_active_users()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'active_users': self.active_users._value,
            'total_requests': len(self.request_history),
            'endpoint_count': len(self.endpoint_stats),
            'recent_errors': sum(1 for r in self.request_history if r.status_code >= 400),
            'system_metrics': {
                'memory_usage': self._get_memory_usage(),
                'cpu_usage': self._get_cpu_usage()
            }
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage metrics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def _get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage metrics"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads()
            }
        except ImportError:
            return {'error': 'psutil not available'}


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect metrics for all requests"""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics_collector = metrics_collector
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        # Extract user ID from request if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = str(request.state.user.id)
        
        # Extract endpoint from request
        endpoint = self._extract_endpoint(request)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_type = None
        except Exception as e:
            status_code = 500
            error_type = type(e).__name__
            response = None
        
        # Calculate response time
        response_time = time.perf_counter() - start_time
        
        # Record metrics
        metrics = RequestMetrics(
            method=request.method,
            path=str(request.url.path),
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(),
            user_id=user_id,
            endpoint=endpoint,
            error_type=error_type
        )
        
        self.metrics_collector.record_request(metrics)
        
        return response if response else Response(status_code=status_code)
    
    def _extract_endpoint(self, request: Request) -> str:
        """Extract endpoint name from request"""
        # Try to get endpoint name from route
        if hasattr(request, 'scope') and 'endpoint' in request.scope:
            endpoint_func = request.scope['endpoint']
            return getattr(endpoint_func, '__name__', str(endpoint_func))
        
        # Fallback to path
        return str(request.url.path)


class AlertManager:
    """Manager for performance alerts and thresholds"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: List[Dict[str, Any]] = []
        self.thresholds = {
            'error_rate': 5.0,  # 5% error rate
            'response_time_p95': 2.0,  # 2 seconds
            'requests_per_minute': 1000,  # 1000 requests per minute
            'memory_usage_mb': 500.0,  # 500 MB
        }
    
    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any thresholds are exceeded"""
        alerts = []
        
        # Check error rate
        summary = self.metrics_collector.get_request_summary()
        if summary['error_rate'] > self.thresholds['error_rate']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'message': f"Error rate is {summary['error_rate']:.2f}%, above threshold of {self.thresholds['error_rate']}%",
                'value': summary['error_rate'],
                'threshold': self.thresholds['error_rate'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Check response time
        endpoint_stats = self.metrics_collector.get_endpoint_statistics()
        for endpoint, stats in endpoint_stats.items():
            if stats['average_response_time'] > self.thresholds['response_time_p95']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f"Average response time for {endpoint} is {stats['average_response_time']:.3f}s, above threshold of {self.thresholds['response_time_p95']}s",
                    'value': stats['average_response_time'],
                    'threshold': self.thresholds['response_time_p95'],
                    'endpoint': endpoint,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check memory usage
        health_metrics = self.metrics_collector.get_health_metrics()
        memory_usage = health_metrics['system_metrics'].get('memory_usage', {})
        if 'rss_mb' in memory_usage and memory_usage['rss_mb'] > self.thresholds['memory_usage_mb']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'critical',
                'message': f"Memory usage is {memory_usage['rss_mb']:.1f}MB, above threshold of {self.thresholds['memory_usage_mb']}MB",
                'value': memory_usage['rss_mb'],
                'threshold': self.thresholds['memory_usage_mb'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Store alerts
        self.alerts.extend(alerts)
        
        # Keep only recent alerts (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if datetime.fromisoformat(a['timestamp']) > cutoff]
        
        return alerts
    
    def get_alerts(self, severity: str = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by severity"""
        if severity:
            return [a for a in self.alerts if a['severity'] == severity]
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()


# Global metrics collector instance
metrics_collector = MetricsCollector()
alert_manager = AlertManager(metrics_collector)


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance"""
    return alert_manager


# Background task to periodically check thresholds
async def threshold_monitoring_task():
    """Background task to monitor thresholds and generate alerts"""
    while True:
        try:
            alerts = alert_manager.check_thresholds()
            if alerts:
                logger.warning(f"Threshold alerts generated: {len(alerts)}")
                for alert in alerts:
                    logger.warning(f"Alert: {alert['message']}")
        except Exception as e:
            logger.error(f"Error in threshold monitoring: {e}")
        
        await asyncio.sleep(60)  # Check every minute


# Export Prometheus metrics
def get_prometheus_metrics() -> str:
    """Get Prometheus metrics in text format"""
    from prometheus_client import generate_latest
    return generate_latest(metrics_collector.registry).decode('utf-8')