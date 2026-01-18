"""
Data Quality Tests for RandomUser API.

Validates random user data across three dimensions:
1. Schema Validation - Does the data match our expected contract?
2. Business Logic - Do the user data fields make sense?
3. Data Completeness - Are all required fields present and valid?
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from tests.schemas.randomuser import RandomUserResponse, User


class TestSchemaValidation:
    """Validate API response matches expected schema."""
    
    def test_response_schema(self, randomuser_data):
        """Validate the entire response structure matches schema."""
        try:
            response = RandomUserResponse(**randomuser_data)
            assert len(response.results) > 0, "Expected at least one user"
            assert response.info.results == len(response.results), \
                "Info results count should match actual results count"
        except ValidationError as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_user_schema(self, randomuser_data):
        """Validate each user object matches schema."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            assert user.gender in ["male", "female"], \
                f"Invalid gender: {user.gender}"
            assert len(user.name.first) > 0, "First name should not be empty"
            assert len(user.name.last) > 0, "Last name should not be empty"
            assert "@" in user.email, f"Invalid email format: {user.email}"
            assert len(user.nat) == 2, f"Nationality should be 2-letter code: {user.nat}"


class TestBusinessLogic:
    """Validate user data makes logical sense."""
    
    def test_age_consistency(self, randomuser_data):
        """Validate age matches date of birth."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            now = datetime.now(timezone.utc)
            dob_date = user.dob.date
            
            # Handle timezone-aware datetime
            if dob_date.tzinfo is None:
                dob_date = dob_date.replace(tzinfo=timezone.utc)
            
            calculated_age = (now - dob_date).days // 365
            # Allow 1 year difference due to rounding
            assert abs(calculated_age - user.dob.age) <= 1, \
                f"Age mismatch for {user.name.first} {user.name.last}: " \
                f"calculated {calculated_age}, reported {user.dob.age}"
    
    def test_registration_after_birth(self, randomuser_data):
        """User should be registered after their birth date."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            dob_date = user.dob.date
            reg_date = user.registered.date
            
            # Handle timezone-aware datetime
            if dob_date.tzinfo is None:
                dob_date = dob_date.replace(tzinfo=timezone.utc)
            if reg_date.tzinfo is None:
                reg_date = reg_date.replace(tzinfo=timezone.utc)
            
            assert reg_date > dob_date, \
                f"Registration date should be after birth date for " \
                f"{user.name.first} {user.name.last}"
    
    def test_coordinates_format(self, randomuser_data):
        """Coordinates should be valid numeric strings."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            try:
                lat = float(user.location.coordinates.latitude)
                lon = float(user.location.coordinates.longitude)
                assert -90 <= lat <= 90, \
                    f"Latitude out of range: {lat}"
                assert -180 <= lon <= 180, \
                    f"Longitude out of range: {lon}"
            except ValueError:
                pytest.fail(f"Invalid coordinate format for {user.name.first}")
    
    def test_picture_urls_valid(self, randomuser_data):
        """Picture URLs should be valid and accessible."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            assert user.picture.large.startswith("http"), \
                f"Invalid picture URL: {user.picture.large}"
            assert user.picture.medium.startswith("http"), \
                f"Invalid medium picture URL: {user.picture.medium}"
            assert user.picture.thumbnail.startswith("http"), \
                f"Invalid thumbnail URL: {user.picture.thumbnail}"


class TestDataCompleteness:
    """Validate all required fields are present and non-empty."""
    
    def test_all_users_have_required_fields(self, randomuser_data):
        """All users should have complete data."""
        response = RandomUserResponse(**randomuser_data)
        
        required_fields = [
            "gender", "name", "location", "email", "login",
            "dob", "registered", "phone", "cell", "picture", "nat"
        ]
        
        for user in response.results:
            for field in required_fields:
                assert hasattr(user, field), \
                    f"Missing field {field} for user {user.name.first}"
                value = getattr(user, field)
                assert value is not None, \
                    f"Field {field} is None for user {user.name.first}"
    
    def test_name_fields_complete(self, randomuser_data):
        """Name should have title, first, and last."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            assert user.name.title, "Title should not be empty"
            assert user.name.first, "First name should not be empty"
            assert user.name.last, "Last name should not be empty"
    
    def test_location_fields_complete(self, randomuser_data):
        """Location should have all required sub-fields."""
        response = RandomUserResponse(**randomuser_data)
        
        for user in response.results:
            assert user.location.street.number > 0, \
                "Street number should be positive"
            assert user.location.street.name, "Street name should not be empty"
            assert user.location.city, "City should not be empty"
            assert user.location.state, "State should not be empty"
            assert user.location.country, "Country should not be empty"
    
    def test_requested_count_matches(self, randomuser_data):
        """Number of results should match the requested count (50)."""
        response = RandomUserResponse(**randomuser_data)
        # The API was called with results=50
        assert len(response.results) == 50, \
            f"Expected 50 users, got {len(response.results)}"
