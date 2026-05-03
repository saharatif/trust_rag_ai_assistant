import pytest
from pydantic import ValidationError

from src.utils.config import Settings, get_settings


def test_default_settings():
    s = Settings()
    assert s.app_name == "TrustRAG API"
    assert s.app_env == "local"
    assert s.log_level == "INFO"
    assert s.chunk_size == 800
    assert s.chunk_overlap == 120


def test_custom_settings():
    s = Settings(app_name="MyApp", app_env="production", log_level="DEBUG", chunk_size=500, chunk_overlap=50)
    assert s.app_name == "MyApp"
    assert s.app_env == "production"
    assert s.log_level == "DEBUG"
    assert s.chunk_size == 500
    assert s.chunk_overlap == 50


def test_chunk_size_lower_bound():
    with pytest.raises(ValidationError):
        Settings(chunk_size=99)


def test_chunk_size_upper_bound():
    with pytest.raises(ValidationError):
        Settings(chunk_size=10001)


def test_chunk_overlap_cannot_be_negative():
    with pytest.raises(ValidationError):
        Settings(chunk_overlap=-1)


def test_chunk_overlap_must_be_less_than_chunk_size():
    with pytest.raises(ValueError, match="CHUNK_OVERLAP must be smaller than CHUNK_SIZE"):
        Settings(chunk_size=200, chunk_overlap=200)


def test_chunk_overlap_equal_to_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        Settings(chunk_size=300, chunk_overlap=300)


def test_get_settings_returns_settings_instance():
    # Clear lru_cache so env state doesn't bleed between test runs
    get_settings.cache_clear()
    s = get_settings()
    assert isinstance(s, Settings)


def test_get_settings_is_cached():
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_get_settings_raises_on_bad_env(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CHUNK_SIZE", "not_a_number")
    with pytest.raises(RuntimeError, match="Invalid environment configuration"):
        get_settings()
    get_settings.cache_clear()
