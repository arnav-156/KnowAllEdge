"""
Property-Based Tests for Quota Tracking
Tests Properties 38 and 41 from design document
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from unittest.mock import Mock, patch
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from quota_management import (
    QuotaTracker,
    QuotaUsage,
    CostConfig,
    Base,
    init_quota_database
)


# Test fixtures
@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def db_session():
    """Create in-memory database session for testing"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Rollback any uncommitted changes
    session.rollback()
    session.close()


@pytest.fixture
def quota_tracker(db_session):
    """Create quota tracker instance for testing"""
    # Clear any existing data
    db_session.query(QuotaUsage).delete()
    db_session.commit()
    return QuotaTracker(db_session)


# Strategies for generating test data
user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=8,
    max_size=36
)

token_strategy = st.integers(min_value=1, max_value=100000)

endpoint_strategy = st.sampled_from([
    '/api/subtopics',
    '/api/generate',
    '/api/quiz',
    '/api/summary',
    '/api/flashcards'
])


class TestQuotaTrackingProperties:
    """
    Property-based tests for quota tracking system
    
    **Feature: production-readiness, Property 38: Quota tracking accuracy**
    **Feature: production-readiness, Property 41: Cost tracking**
    """
    
    @given(
        user_id=user_id_strategy,
        input_tokens=token_strategy,
        output_tokens=token_strategy,
        endpoint=endpoint_strategy
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_38_quota_tracking_accuracy(
        self,
        user_id,
        input_tokens,
        output_tokens,
        endpoint,
        quota_tracker,
        app
    ):
        """
        Property 38: Quota tracking accuracy
        
        For any API request consuming tokens, the quota tracker should 
        accurately increment daily and monthly token counts
        
        **Validates: Requirements 9.3**
        """
        with app.test_request_context():
            # Mock g.current_user
            g.current_user = {'user_id': user_id}
            
            # Get initial usage (should be None or 0)
            initial_daily = quota_tracker.get_usage(user_id, 'daily')
            initial_monthly = quota_tracker.get_usage(user_id, 'monthly')
            
            initial_daily_tokens = initial_daily['total_tokens'] if initial_daily else 0
            initial_monthly_tokens = initial_monthly['total_tokens'] if initial_monthly else 0
            
            # Track usage
            result = quota_tracker.track_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                endpoint=endpoint,
                user_id=user_id
            )
            
            # Verify tracking succeeded
            assert result['tracked'], "Usage tracking should succeed"
            
            # Get updated usage
            updated_daily = quota_tracker.get_usage(user_id, 'daily')
            updated_monthly = quota_tracker.get_usage(user_id, 'monthly')
            
            assert updated_daily is not None, "Daily usage should exist after tracking"
            assert updated_monthly is not None, "Monthly usage should exist after tracking"
            
            # Verify accuracy: daily tokens should increase by exactly input + output
            expected_daily_tokens = initial_daily_tokens + input_tokens + output_tokens
            assert updated_daily['total_tokens'] == expected_daily_tokens, \
                f"Daily tokens should be {expected_daily_tokens}, got {updated_daily['total_tokens']}"
            
            # Verify accuracy: monthly tokens should increase by exactly input + output
            expected_monthly_tokens = initial_monthly_tokens + input_tokens + output_tokens
            assert updated_monthly['total_tokens'] == expected_monthly_tokens, \
                f"Monthly tokens should be {expected_monthly_tokens}, got {updated_monthly['total_tokens']}"
            
            # Verify input/output token breakdown
            assert updated_daily['total_input_tokens'] >= input_tokens, \
                "Daily input tokens should include current request"
            assert updated_daily['total_output_tokens'] >= output_tokens, \
                "Daily output tokens should include current request"
            
            # Verify request count incremented
            initial_daily_requests = initial_daily['total_requests'] if initial_daily else 0
            assert updated_daily['total_requests'] == initial_daily_requests + 1, \
                "Request count should increment by 1"
    
    @given(
        user_id=user_id_strategy,
        input_tokens=token_strategy,
        output_tokens=token_strategy,
        endpoint=endpoint_strategy
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_41_cost_tracking(
        self,
        user_id,
        input_tokens,
        output_tokens,
        endpoint,
        quota_tracker,
        app
    ):
        """
        Property 41: Cost tracking
        
        For any API request, the system should calculate and track cost 
        per user and per endpoint
        
        **Validates: Requirements 9.6**
        """
        with app.test_request_context():
            # Mock g.current_user
            g.current_user = {'user_id': user_id}
            
            # Calculate expected cost
            cost_config = CostConfig()
            expected_cost = cost_config.calculate_cost(input_tokens, output_tokens)
            
            # Get initial cost
            initial_daily = quota_tracker.get_usage(user_id, 'daily')
            initial_daily_cost = float(initial_daily['total_cost']) if initial_daily else 0.0
            
            # Track usage
            result = quota_tracker.track_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                endpoint=endpoint,
                user_id=user_id
            )
            
            # Verify cost was calculated
            assert 'cost' in result, "Result should include cost"
            assert result['cost'] > 0, "Cost should be positive for non-zero tokens"
            
            # Verify cost calculation is correct (within floating point precision)
            assert abs(result['cost'] - expected_cost) < 0.0001, \
                f"Cost should be {expected_cost}, got {result['cost']}"
            
            # Refresh the session to get latest committed data
            quota_tracker.db_session.expire_all()
            
            # Get updated usage
            updated_daily = quota_tracker.get_usage(user_id, 'daily')
            updated_monthly = quota_tracker.get_usage(user_id, 'monthly')
            
            assert updated_daily is not None, "Daily usage should exist after tracking"
            assert updated_monthly is not None, "Monthly usage should exist after tracking"
            
            # Verify daily cost tracking
            expected_daily_cost = initial_daily_cost + expected_cost
            assert abs(float(updated_daily['total_cost']) - expected_daily_cost) < 0.0001, \
                f"Daily cost should be {expected_daily_cost}, got {updated_daily['total_cost']}"
            
            # Verify monthly cost tracking
            assert float(updated_monthly['total_cost']) >= expected_cost, \
                f"Monthly cost should include current request cost, got {updated_monthly['total_cost']}"
            
            # Verify per-endpoint cost tracking
            import json
            endpoint_data = json.loads(updated_daily['endpoint_usage'])
            assert endpoint in endpoint_data, \
                f"Endpoint {endpoint} should be in usage breakdown"
            
            endpoint_cost = endpoint_data[endpoint]['cost']
            assert endpoint_cost >= expected_cost, \
                f"Endpoint cost should include current request cost"
    
    @given(
        user_id=user_id_strategy,
        num_requests=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quota_accumulation(
        self,
        user_id,
        num_requests,
        quota_tracker,
        app
    ):
        """
        Test that quota accumulates correctly over multiple requests
        """
        with app.test_request_context():
            g.current_user = {'user_id': user_id}
            
            total_tokens = 0
            total_cost = 0.0
            
            # Make multiple requests
            for i in range(num_requests):
                input_tokens = 1000 + i * 100
                output_tokens = 500 + i * 50
                
                result = quota_tracker.track_usage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    endpoint='/api/test',
                    user_id=user_id
                )
                
                total_tokens += input_tokens + output_tokens
                total_cost += result['cost']
            
            # Get final usage
            final_usage = quota_tracker.get_usage(user_id, 'daily')
            
            # Verify accumulation
            assert final_usage['total_tokens'] == total_tokens, \
                f"Total tokens should be {total_tokens}, got {final_usage['total_tokens']}"
            
            assert final_usage['total_requests'] == num_requests, \
                f"Total requests should be {num_requests}, got {final_usage['total_requests']}"
            
            # Verify cost accumulation (within floating point precision)
            assert abs(float(final_usage['total_cost']) - total_cost) < 0.01, \
                f"Total cost should be approximately {total_cost}, got {final_usage['total_cost']}"
    
    @given(
        user1_id=user_id_strategy,
        user2_id=user_id_strategy,
        tokens=token_strategy
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quota_isolation_between_users(
        self,
        user1_id,
        user2_id,
        tokens,
        quota_tracker,
        app
    ):
        """
        Test that quota tracking is isolated between different users
        """
        assume(user1_id != user2_id)  # Ensure different users
        
        with app.test_request_context():
            # Track usage for user 1
            g.current_user = {'user_id': user1_id}
            quota_tracker.track_usage(
                input_tokens=tokens,
                output_tokens=tokens,
                endpoint='/api/test',
                user_id=user1_id
            )
            
            # Track usage for user 2
            g.current_user = {'user_id': user2_id}
            quota_tracker.track_usage(
                input_tokens=tokens * 2,
                output_tokens=tokens * 2,
                endpoint='/api/test',
                user_id=user2_id
            )
            
            # Get usage for both users
            user1_usage = quota_tracker.get_usage(user1_id, 'daily')
            user2_usage = quota_tracker.get_usage(user2_id, 'daily')
            
            # Verify isolation
            assert user1_usage['total_tokens'] == tokens * 2, \
                f"User 1 should have {tokens * 2} tokens"
            
            assert user2_usage['total_tokens'] == tokens * 4, \
                f"User 2 should have {tokens * 4} tokens"
            
            # Verify they are different
            assert user1_usage['total_tokens'] != user2_usage['total_tokens'], \
                "Different users should have different usage"
    
    def test_cost_config_calculation(self):
        """
        Test that cost calculation is correct
        """
        cost_config = CostConfig()
        
        # Test case 1: 1M input tokens, 0 output tokens
        cost = cost_config.calculate_cost(1_000_000, 0)
        assert abs(cost - 0.075) < 0.0001, \
            f"Cost for 1M input tokens should be $0.075, got ${cost}"
        
        # Test case 2: 0 input tokens, 1M output tokens
        cost = cost_config.calculate_cost(0, 1_000_000)
        assert abs(cost - 0.30) < 0.0001, \
            f"Cost for 1M output tokens should be $0.30, got ${cost}"
        
        # Test case 3: 1M input + 1M output tokens
        cost = cost_config.calculate_cost(1_000_000, 1_000_000)
        assert abs(cost - 0.375) < 0.0001, \
            f"Cost for 1M input + 1M output should be $0.375, got ${cost}"
        
        # Test case 4: Small amounts
        cost = cost_config.calculate_cost(1000, 500)
        expected = (1000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        assert abs(cost - expected) < 0.000001, \
            f"Cost calculation should be accurate for small amounts"
    
    @given(
        user_id=user_id_strategy,
        input_tokens=token_strategy,
        output_tokens=token_strategy
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_daily_and_monthly_consistency(
        self,
        user_id,
        input_tokens,
        output_tokens,
        quota_tracker,
        app
    ):
        """
        Test that daily and monthly tracking are consistent
        """
        with app.test_request_context():
            g.current_user = {'user_id': user_id}
            
            # Track usage
            quota_tracker.track_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                endpoint='/api/test',
                user_id=user_id
            )
            
            # Get both daily and monthly usage
            daily_usage = quota_tracker.get_usage(user_id, 'daily')
            monthly_usage = quota_tracker.get_usage(user_id, 'monthly')
            
            # Daily usage should be <= monthly usage (since daily is subset of monthly)
            assert daily_usage['total_tokens'] <= monthly_usage['total_tokens'], \
                "Daily tokens should be <= monthly tokens"
            
            assert daily_usage['total_requests'] <= monthly_usage['total_requests'], \
                "Daily requests should be <= monthly requests"
            
            assert float(daily_usage['total_cost']) <= float(monthly_usage['total_cost']), \
                "Daily cost should be <= monthly cost"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
