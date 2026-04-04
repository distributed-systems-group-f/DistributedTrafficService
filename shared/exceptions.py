class TrafficServiceError(Exception):
    """Base exception for all traffic service errors."""
    pass


class BookingNotFoundError(TrafficServiceError):
    pass


class CapacityExceededError(TrafficServiceError):
    pass


class SegmentNotFoundError(TrafficServiceError):
    pass


class LockAcquisitionError(TrafficServiceError):
    pass


class SagaRollbackError(TrafficServiceError):
    pass


class UserNotFoundError(TrafficServiceError):
    pass


class AuthenticationError(TrafficServiceError):
    pass


class RegionUnavailableError(TrafficServiceError):
    pass


class RouteNotFoundError(TrafficServiceError):
    pass
