#!/usr/bin/env python3
"""
Monitoring Integration Verification Script

This script verifies that all monitoring components are properly integrated
and can be imported without errors.
"""

import sys


def verify_imports():
    """Verify all monitoring imports."""
    print("🔍 Verifying monitoring imports...")

    try:
        # Import monitoring modules
        from app.monitoring import (
            PrometheusMiddleware,
            REGISTRY,
            HealthCheckService,
            HealthStatus,
            init_sentry,
            capture_exception,
            capture_message,
        )
        print("✅ Monitoring module imports successful")

        # Import main app components
        from app.main import app
        print("✅ FastAPI app import successful")

        # Verify Prometheus metrics are defined
        from app.monitoring.metrics import (
            http_requests_total,
            http_request_duration_seconds,
            http_requests_in_progress,
            keywords_researched_total,
            content_generated_total,
            images_generated_total,
            posts_published_total,
            errors_total,
            api_errors_total,
        )
        print("✅ Prometheus metrics defined")

        # Verify health check components
        health_service = HealthCheckService()
        print(f"✅ HealthCheckService instantiated")

        # Check if metrics are in registry
        metrics_count = len(list(REGISTRY.collect()))
        print(f"✅ Prometheus registry has {metrics_count} metric families")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_app_routes():
    """Verify app routes are registered."""
    print("\n🔍 Verifying FastAPI routes...")

    try:
        from app.main import app

        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        required_routes = ['/health', '/metrics', '/']

        for required_route in required_routes:
            if required_route in routes:
                print(f"✅ Route {required_route} registered")
            else:
                print(f"❌ Route {required_route} NOT registered")
                return False

        return True

    except Exception as e:
        print(f"❌ Route verification error: {e}")
        return False


def verify_middleware():
    """Verify middleware is registered."""
    print("\n🔍 Verifying middleware...")

    try:
        from app.main import app
        from app.monitoring.metrics import PrometheusMiddleware

        # Check if PrometheusMiddleware is in the middleware stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]

        if 'PrometheusMiddleware' in str(app.user_middleware):
            print("✅ PrometheusMiddleware registered")
        else:
            print("⚠️  PrometheusMiddleware may not be registered (check if enable_metrics=True)")

        print(f"ℹ️  Total middleware count: {len(app.user_middleware)}")

        return True

    except Exception as e:
        print(f"❌ Middleware verification error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("🚀 Monitoring Integration Verification")
    print("="*60)

    results = []

    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("Routes", verify_app_routes()))
    results.append(("Middleware", verify_middleware()))

    # Summary
    print("\n" + "="*60)
    print("📊 Verification Summary")
    print("="*60)

    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20} {status}")
        if not result:
            all_passed = False

    print("="*60)

    if all_passed:
        print("✅ All verification checks passed!")
        print("\nNext steps:")
        print("1. Set ENABLE_METRICS=true in .env")
        print("2. Start the application: uvicorn app.main:app")
        print("3. Test endpoints:")
        print("   - http://localhost:8000/health")
        print("   - http://localhost:8000/metrics")
        return 0
    else:
        print("❌ Some verification checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
