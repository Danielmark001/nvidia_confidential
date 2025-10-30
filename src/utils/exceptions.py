"""
Custom exceptions for the medication advisor system.
Provides domain-specific exception types for error handling.
"""


class MedicationAdvisorException(Exception):
    """Base exception for medication advisor system."""
    pass


class ConfigurationError(MedicationAdvisorException):
    """Raised when configuration is invalid or incomplete."""
    pass


class DataParsingError(MedicationAdvisorException):
    """Raised when data parsing fails."""
    pass


class DatabaseError(MedicationAdvisorException):
    """Raised when database operation fails."""
    pass


class QueryError(MedicationAdvisorException):
    """Raised when knowledge graph query fails."""
    pass


class MedicationNotFoundError(MedicationAdvisorException):
    """Raised when medication is not found in knowledge graph."""
    pass


class PatientNotFoundError(MedicationAdvisorException):
    """Raised when patient is not found in knowledge graph."""
    pass


class LLMError(MedicationAdvisorException):
    """Raised when LLM operation fails."""
    pass


class VoiceError(MedicationAdvisorException):
    """Raised when voice I/O operation fails."""
    pass
