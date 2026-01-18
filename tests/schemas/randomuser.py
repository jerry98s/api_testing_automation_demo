"""RandomUser API Pydantic models."""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field


class Name(BaseModel):
    """User name schema."""
    title: str
    first: str
    last: str


class Street(BaseModel):
    """Street address schema."""
    number: int
    name: str


class Coordinates(BaseModel):
    """Geographic coordinates schema."""
    latitude: str
    longitude: str


class Timezone(BaseModel):
    """Timezone schema."""
    offset: str
    description: str


class Location(BaseModel):
    """User location schema."""
    street: Street
    city: str
    state: str
    country: str
    postcode: Union[str, int]  # Can be string or int depending on country
    coordinates: Coordinates
    timezone: Timezone


class Login(BaseModel):
    """User login credentials schema."""
    uuid: str
    username: str
    password: str
    salt: str
    md5: str
    sha1: str
    sha256: str


class DateOfBirth(BaseModel):
    """Date of birth schema."""
    date: datetime
    age: int


class Registered(BaseModel):
    """Registration date schema."""
    date: datetime
    age: int


class UserId(BaseModel):
    """User ID schema."""
    name: str
    value: Optional[str] = None


class Picture(BaseModel):
    """User picture URLs schema."""
    large: str
    medium: str
    thumbnail: str


class User(BaseModel):
    """Schema for a single user from RandomUser API."""
    gender: str
    name: Name
    location: Location
    email: str
    login: Login
    dob: DateOfBirth
    registered: Registered
    phone: str
    cell: str
    id: UserId
    picture: Picture
    nat: str  # Nationality
    
    class Config:
        extra = "allow"  # Allow extra fields from API


class Info(BaseModel):
    """API metadata schema."""
    seed: str
    results: int
    page: int
    version: str


class RandomUserResponse(BaseModel):
    """Schema for RandomUser API response."""
    results: List[User]
    info: Info
