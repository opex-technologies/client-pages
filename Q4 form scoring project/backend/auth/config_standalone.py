"""
Configuration management for backend services
Loads configuration from environment variables with defaults
Created: November 5, 2025
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for backend services

    Usage:
        from common.config import config
        project_id = config.PROJECT_ID
    """

    # GCP Configuration
    PROJECT_ID: str = os.getenv('PROJECT_ID', 'opex-data-lake-k23k4y98m')
    REGION: str = os.getenv('REGION', 'us-central1')

    # BigQuery Datasets
    AUTH_DATASET: str = os.getenv('AUTH_DATASET', 'auth')
    FORM_BUILDER_DATASET: str = os.getenv('FORM_BUILDER_DATASET', 'form_builder')
    SCORING_DATASET: str = os.getenv('SCORING_DATASET', 'scoring')
    OPEX_DEV_DATASET: str = os.getenv('OPEX_DEV_DATASET', 'opex_dev')

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'CHANGE_THIS_IN_PRODUCTION')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS: int = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    JWT_REFRESH_EXPIRATION_DAYS: int = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', '30'))

    # Password Security
    BCRYPT_ROUNDS: int = int(os.getenv('BCRYPT_ROUNDS', '12'))
    MIN_PASSWORD_LENGTH: int = int(os.getenv('MIN_PASSWORD_LENGTH', '8'))
    PASSWORD_REQUIRE_UPPERCASE: bool = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE: bool = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_DIGIT: bool = os.getenv('PASSWORD_REQUIRE_DIGIT', 'true').lower() == 'true'
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'

    # Account Security
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    ACCOUNT_LOCKOUT_MINUTES: int = int(os.getenv('ACCOUNT_LOCKOUT_MINUTES', '30'))

    # MFA Configuration
    MFA_ENABLED: bool = os.getenv('MFA_ENABLED', 'false').lower() == 'true'
    MFA_ISSUER: str = os.getenv('MFA_ISSUER', 'Opex Technologies')

    # GitHub Configuration (for form deployment)
    GITHUB_TOKEN: Optional[str] = os.getenv('GITHUB_TOKEN')
    GITHUB_REPO: str = os.getenv('GITHUB_REPO', 'landoncolvig/opex-technologies')
    GITHUB_PAGES_BRANCH: str = os.getenv('GITHUB_PAGES_BRANCH', 'gh-pages')
    GITHUB_FORMS_PATH: str = os.getenv('GITHUB_FORMS_PATH', 'forms')

    # Cloud Storage
    STORAGE_BUCKET: str = os.getenv('STORAGE_BUCKET', 'opex-web-forms-20250716-145646')

    # Scoring Configuration
    DEFAULT_WEIGHT_INFO: str = "Info"
    SCORING_PRECISION: int = 2  # Decimal places for scores

    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # CORS Configuration
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '*').split(',')

    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv('DEFAULT_PAGE_SIZE', '50'))
    MAX_PAGE_SIZE: int = int(os.getenv('MAX_PAGE_SIZE', '100'))

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_PERIOD: int = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # seconds

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT == 'production'

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT == 'development'

    @classmethod
    def get_dataset_table(cls, dataset: str, table: str) -> str:
        """Get fully qualified table name"""
        return f"{cls.PROJECT_ID}.{dataset}.{table}"

    @classmethod
    def validate_config(cls) -> list:
        """
        Validate critical configuration values

        Returns:
            list: List of configuration errors, empty if valid
        """
        errors = []

        # Check critical values in production
        if cls.is_production():
            if cls.JWT_SECRET_KEY == 'CHANGE_THIS_IN_PRODUCTION':
                errors.append("JWT_SECRET_KEY must be set in production")

            if not cls.GITHUB_TOKEN:
                errors.append("GITHUB_TOKEN must be set in production")

        # Validate ranges
        if cls.BCRYPT_ROUNDS < 10 or cls.BCRYPT_ROUNDS > 15:
            errors.append("BCRYPT_ROUNDS should be between 10 and 15")

        if cls.MIN_PASSWORD_LENGTH < 8:
            errors.append("MIN_PASSWORD_LENGTH should be at least 8")

        if cls.JWT_EXPIRATION_HOURS < 1:
            errors.append("JWT_EXPIRATION_HOURS must be at least 1")

        return errors


# Singleton instance
config = Config()


# Validate configuration on module load
_config_errors = config.validate_config()
if _config_errors:
    import warnings
    for error in _config_errors:
        warnings.warn(f"Configuration warning: {error}")
