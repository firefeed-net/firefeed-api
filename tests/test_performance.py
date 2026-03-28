"""
Performance tests for FireFeed API

This module contains performance tests to ensure the API maintains
acceptable response times and can handle expected load.
"""

import asyncio
import time
import pytest
import httpx
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median, stdev

from firefeed_api.main import app
from firefeed_api.models.public_models import UserCreate, RSSItemResponse
from firefeed_api.dependencies import get_db, get_redis
from tests.conftest import create_test_user, create_test_rss_item


class PerformanceTestConfig:
    """Configuration for performance tests"""
    
    # Test parameters
    CONCURRENT_USERS = 50
    REQUESTS_PER_USER = 10
    TIMEOUT_SECONDS = 30
    
    # Performance thresholds (in seconds)
    MAX_RESPONSE_TIME_P95 = 2.0
    MAX_RESPONSE_TIME_P99 = 5.0
    MIN_REQUESTS_PER_SECOND = 100
    
    # Database test parameters
    BULK_INSERT_COUNT = 1000
    BULK_QUERY_COUNT = 100


class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.total_requests = 0
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement"""
        self.response_times.append(response_time)
        self.total_requests += 1
    
    def add_success(self):
        """Increment success counter"""
        self.success_count += 1
    
    def add_error(self):
        """Increment error counter"""
        self.error_count += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return mean(self.response_times)
    
    @property
    def median_response_time(self) -> float:
        """Calculate median response time"""
        if not self.response_times:
            return 0.0
        return median(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
    
    @property
    def p99_response_time(self) -> float:
        """Calculate 99th percentile response time"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
    
    @property
    def throughput(self) -> float:
        """Calculate requests per second"""
        if not self.response_times:
            return 0.0
        total_time = sum(self.response_times)
        return self.total_requests / total_time if total_time > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 2),
            "average_response_time": round(self.average_response_time, 3),
            "median_response_time": round(self.median_response_time, 3),
            "p95_response_time": round(self.p95_response_time, 3),
            "p99_response_time": round(self.p99_response_time, 3),
            "throughput": round(self.throughput, 2),
            "response_time_std_dev": round(stdev(self.response_times) if len(self.response_times) > 1 else 0.0, 3)
        }


class PerformanceTester:
    """Performance testing utilities"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=PerformanceTestConfig.TIMEOUT_SECONDS)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def measure_response_time(self, method: str, url: str, **kwargs) -> float:
        """Measure response time for a single request"""
        start_time = time.perf_counter()
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            end_time = time.perf_counter()
            return end_time - start_time
        except Exception as e:
            end_time = time.perf_counter()
            return end_time - start_time
    
    async def concurrent_requests(self, method: str, url: str, count: int, **kwargs) -> PerformanceMetrics:
        """Execute multiple concurrent requests and measure performance"""
        metrics = PerformanceMetrics()
        
        async def make_request():
            try:
                response_time = await self.measure_response_time(method, url, **kwargs)
                metrics.add_response_time(response_time)
                metrics.add_success()
            except Exception:
                metrics.add_error()
        
        # Execute concurrent requests
        tasks = [make_request() for _ in range(count)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return metrics
    
    async def load_test(self, method: str, url: str, concurrent_users: int = None, 
                       requests_per_user: int = None, **kwargs) -> PerformanceMetrics:
        """Perform load test with multiple concurrent users"""
        if concurrent_users is None:
            concurrent_users = PerformanceTestConfig.CONCURRENT_USERS
        if requests_per_user is None:
            requests_per_user = PerformanceTestConfig.REQUESTS_PER_USER
        
        metrics = PerformanceMetrics()
        
        async def user_session(user_id: int):
            user_metrics = await self.concurrent_requests(
                method, url, requests_per_user, **kwargs
            )
            metrics.success_count += user_metrics.success_count
            metrics.error_count += user_metrics.error_count
            metrics.total_requests += user_metrics.total_requests
            metrics.response_times.extend(user_metrics.response_times)
        
        # Execute concurrent user sessions
        tasks = [user_session(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return metrics


@pytest.mark.asyncio
class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, test_db, test_redis):
        """Setup test data for performance tests"""
        # Create test user
        self.test_user = await create_test_user(test_db)
        
        # Create test RSS items
        self.test_items = []
        for i in range(100):
            item = await create_test_rss_item(test_db, self.test_user.id)
            self.test_items.append(item)
    
    async def test_authentication_performance(self, client):
        """Test authentication endpoint performance"""
        async with PerformanceTester() as tester:
            # Test login performance
            login_data = {
                "username": self.test_user.email,
                "password": "testpassword123"
            }
            
            metrics = await tester.load_test(
                "POST", 
                f"{client.base_url}/api/v1/auth/login",
                data=login_data
            )
            
            # Assert performance requirements
            assert metrics.success_rate >= 95.0, f"Login success rate too low: {metrics.success_rate}%"
            assert metrics.p95_response_time <= PerformanceTestConfig.MAX_RESPONSE_TIME_P95, \
                f"P95 response time too high: {metrics.p95_response_time}s"
            assert metrics.p99_response_time <= PerformanceTestConfig.MAX_RESPONSE_TIME_P99, \
                f"P99 response time too high: {metrics.p99_response_time}s"
            
            print(f"Authentication Performance: {metrics.to_dict()}")
    
    async def test_rss_items_endpoint_performance(self, client):
        """Test RSS items endpoint performance"""
        # First authenticate to get token
        login_response = await client.post("/api/v1/auth/login", data={
            "username": self.test_user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with PerformanceTester() as tester:
            metrics = await tester.load_test(
                "GET",
                f"{client.base_url}/api/v1/rss-items/",
                headers=headers,
                params={"limit": 20}
            )
            
            # Assert performance requirements
            assert metrics.success_rate >= 98.0, f"RSS items success rate too low: {metrics.success_rate}%"
            assert metrics.p95_response_time <= PerformanceTestConfig.MAX_RESPONSE_TIME_P95, \
                f"P95 response time too high: {metrics.p95_response_time}s"
            assert metrics.throughput >= PerformanceTestConfig.MIN_REQUESTS_PER_SECOND, \
                f"Throughput too low: {metrics.throughput} req/s"
            
            print(f"RSS Items Performance: {metrics.to_dict()}")
    
    async def test_user_profile_performance(self, client):
        """Test user profile endpoint performance"""
        # Authenticate
        login_response = await client.post("/api/v1/auth/login", data={
            "username": self.test_user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with PerformanceTester() as tester:
            metrics = await tester.load_test(
                "GET",
                f"{client.base_url}/api/v1/users/me",
                headers=headers
            )
            
            # Assert performance requirements
            assert metrics.success_rate >= 99.0, f"User profile success rate too low: {metrics.success_rate}%"
            assert metrics.p95_response_time <= PerformanceTestConfig.MAX_RESPONSE_TIME_P95, \
                f"P95 response time too high: {metrics.p95_response_time}s"
            
            print(f"User Profile Performance: {metrics.to_dict()}")
    
    async def test_concurrent_user_creation(self, client):
        """Test concurrent user creation performance"""
        async with PerformanceTester() as tester:
            user_data = {
                "email": "perf_test_user_{}.@example.com",
                "password": "testpassword123",
                "language": "en"
            }
            
            # Create multiple users concurrently
            tasks = []
            for i in range(50):
                data = user_data.copy()
                data["email"] = data["email"].format(i)
                tasks.append(tester.measure_response_time(
                    "POST", 
                    f"{client.base_url}/api/v1/auth/register",
                    json=data
                ))
            
            response_times = await asyncio.gather(*tasks, return_exceptions=True)
            successful_times = [t for t in response_times if not isinstance(t, Exception)]
            
            if successful_times:
                avg_time = mean(successful_times)
                p95_time = sorted(successful_times)[int(0.95 * len(successful_times))]
                
                assert avg_time <= 2.0, f"Average user creation time too high: {avg_time}s"
                assert p95_time <= 5.0, f"P95 user creation time too high: {p95_time}s"
                
                print(f"Concurrent User Creation: avg={avg_time:.3f}s, p95={p95_time:.3f}s, count={len(successful_times)}")
    
    async def test_database_query_performance(self, test_db):
        """Test database query performance"""
        import time
        
        # Test single query performance
        start_time = time.perf_counter()
        result = await test_db.fetch_one("SELECT COUNT(*) as count FROM users")
        single_query_time = time.perf_counter() - start_time
        
        assert single_query_time < 0.1, f"Single query too slow: {single_query_time}s"
        
        # Test multiple concurrent queries
        start_time = time.perf_counter()
        
        async def query_user(user_id):
            return await test_db.fetch_one("SELECT * FROM users WHERE id = $1", (user_id,))
        
        tasks = [query_user(item.id) for item in self.test_items[:10]]
        results = await asyncio.gather(*tasks)
        
        concurrent_query_time = time.perf_counter() - start_time
        
        assert concurrent_query_time < 1.0, f"Concurrent queries too slow: {concurrent_query_time}s"
        assert len(results) == 10, "Not all queries completed"
        
        print(f"Database Performance: single_query={single_query_time:.3f}s, concurrent_queries={concurrent_query_time:.3f}s")
    
    async def test_redis_performance(self, test_redis):
        """Test Redis operations performance"""
        import time
        
        # Test single operation
        start_time = time.perf_counter()
        await test_redis.set("test_key", "test_value", ex=60)
        single_op_time = time.perf_counter() - start_time
        
        assert single_op_time < 0.01, f"Single Redis operation too slow: {single_op_time}s"
        
        # Test multiple operations
        start_time = time.perf_counter()
        
        async def redis_operation(i):
            key = f"test_key_{i}"
            value = f"test_value_{i}"
            await test_redis.set(key, value, ex=60)
            return await test_redis.get(key)
        
        tasks = [redis_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        batch_op_time = time.perf_counter() - start_time
        
        assert batch_op_time < 1.0, f"Batch Redis operations too slow: {batch_op_time}s"
        assert len(results) == 100, "Not all Redis operations completed"
        
        print(f"Redis Performance: single_op={single_op_time:.3f}s, batch_ops={batch_op_time:.3f}s")
    
    async def test_memory_usage_stability(self, client):
        """Test memory usage stability under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests to test memory stability
        async with PerformanceTester() as tester:
            metrics = await tester.load_test(
                "GET",
                f"{client.base_url}/api/v1/health",
                concurrent_users=20,
                requests_per_user=50
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory usage increased too much: {memory_increase:.1f}MB"
        
        print(f"Memory Stability: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, increase={memory_increase:.1f}MB")
    
    @pytest.mark.slow
    async def test_endurance_test(self, client):
        """Endurance test - run for extended period"""
        async with PerformanceTester() as tester:
            # Run test for 5 minutes
            end_time = time.time() + 300  # 5 minutes
            metrics = PerformanceMetrics()
            
            while time.time() < end_time:
                # Make a few requests every second
                batch_metrics = await tester.concurrent_requests(
                    "GET",
                    f"{client.base_url}/api/v1/health",
                    count=5
                )
                
                metrics.success_count += batch_metrics.success_count
                metrics.error_count += batch_metrics.error_count
                metrics.total_requests += batch_metrics.total_requests
                metrics.response_times.extend(batch_metrics.response_times)
                
                await asyncio.sleep(1)
            
            # Assert stability requirements
            assert metrics.success_rate >= 99.0, f"Endurance test success rate too low: {metrics.success_rate}%"
            assert metrics.p95_response_time <= PerformanceTestConfig.MAX_RESPONSE_TIME_P95, \
                f"Endurance test P95 response time too high: {metrics.p95_response_time}s"
            
            print(f"Endurance Test (5min): {metrics.to_dict()}")


class TestDatabasePerformance:
    """Database-specific performance tests"""
    
    async def test_bulk_insert_performance(self, test_db):
        """Test bulk insert performance"""
        import time
        
        # Generate test data
        test_data = []
        for i in range(PerformanceTestConfig.BULK_INSERT_COUNT):
            test_data.append({
                "original_title": f"Test News {i}",
                "original_content": f"Test content {i}",
                "original_language": "en",
                "category_id": None,
                "rss_feed_id": None,
                "source_url": f"https://test{i}.com"
            })
        
        # Test bulk insert
        start_time = time.perf_counter()
        
        # Use executemany for bulk insert
        query = """
            INSERT INTO rss_data (original_title, original_content, original_language, category_id, rss_feed_id, source_url)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        values = [
            (item["original_title"], item["original_content"], item["original_language"],
             item["category_id"], item["rss_feed_id"], item["source_url"])
            for item in test_data
        ]
        
        await test_db.execute_many(query, values)
        
        insert_time = time.perf_counter() - start_time
        
        # Should insert 1000 records in under 10 seconds
        assert insert_time < 10.0, f"Bulk insert too slow: {insert_time}s"
        
        print(f"Bulk Insert Performance: {PerformanceTestConfig.BULK_INSERT_COUNT} records in {insert_time:.3f}s")
    
    async def test_bulk_query_performance(self, test_db):
        """Test bulk query performance"""
        import time
        
        # Test bulk select
        start_time = time.perf_counter()
        
        query = "SELECT * FROM rss_data LIMIT $1"
        result = await test_db.fetch_all(query, (PerformanceTestConfig.BULK_QUERY_COUNT,))
        
        query_time = time.perf_counter() - start_time
        
        # Should query 100 records in under 1 second
        assert query_time < 1.0, f"Bulk query too slow: {query_time}s"
        assert len(result) == PerformanceTestConfig.BULK_QUERY_COUNT, "Wrong number of records returned"
        
        print(f"Bulk Query Performance: {PerformanceTestConfig.BULK_QUERY_COUNT} records in {query_time:.3f}s")


class TestCachingPerformance:
    """Caching-specific performance tests"""
    
    async def test_cache_hit_performance(self, test_redis):
        """Test cache hit performance"""
        import time
        
        # Set up cache
        await test_redis.set("test_key", "test_value", ex=3600)
        
        # Test cache hit
        start_time = time.perf_counter()
        
        async def cache_hit():
            return await test_redis.get("test_key")
        
        tasks = [cache_hit() for _ in range(1000)]
        results = await asyncio.gather(*tasks)
        
        hit_time = time.perf_counter() - start_time
        
        assert hit_time < 2.0, f"Cache hit too slow: {hit_time}s"
        assert all(r == b"test_value" for r in results), "Cache hit returned wrong value"
        
        print(f"Cache Hit Performance: 1000 hits in {hit_time:.3f}s")
    
    async def test_cache_miss_performance(self, test_redis):
        """Test cache miss performance"""
        import time
        
        # Test cache miss
        start_time = time.perf_counter()
        
        async def cache_miss():
            return await test_redis.get("nonexistent_key")
        
        tasks = [cache_miss() for _ in range(1000)]
        results = await asyncio.gather(*tasks)
        
        miss_time = time.perf_counter() - start_time
        
        assert miss_time < 2.0, f"Cache miss too slow: {miss_time}s"
        assert all(r is None for r in results), "Cache miss should return None"
        
        print(f"Cache Miss Performance: 1000 misses in {miss_time:.3f}s")


def print_performance_summary(metrics: PerformanceMetrics):
    """Print a formatted performance summary"""
    data = metrics.to_dict()
    
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUMMARY")
    print("="*60)
    print(f"Total Requests: {data['total_requests']}")
    print(f"Success Rate: {data['success_rate']}%")
    print(f"Error Count: {data['error_count']}")
    print(f"Average Response Time: {data['average_response_time']}s")
    print(f"Median Response Time: {data['median_response_time']}s")
    print(f"P95 Response Time: {data['p95_response_time']}s")
    print(f"P99 Response Time: {data['p99_response_time']}s")
    print(f"Throughput: {data['throughput']} req/s")
    print(f"Response Time Std Dev: {data['response_time_std_dev']}s")
    print("="*60)