from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "traffic_admin"
    postgres_password: str = "dev_password"
    postgres_db: str = "traffic_service"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # RabbitMQ (local — used by booking/notification/analytics)
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    # RabbitMQ for cross-VM user replication (auth service only)
    # Defaults to the local broker; set to VM1's IP on VM2 to enable replication
    replication_rabbitmq_host: str = ""
    replication_rabbitmq_port: int = 5672
    replication_rabbitmq_user: str = ""
    replication_rabbitmq_password: str = ""

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # Service URLs (used by API gateway)
    auth_service_url: str = "http://localhost:8001"
    booking_service_url: str = "http://localhost:8002"
    verification_service_url: str = "http://localhost:8003"
    notification_service_url: str = "http://localhost:8004"
    analytics_service_url: str = "http://localhost:8005"

    # Service port
    service_port: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

    @property
    def replication_rabbitmq_url(self) -> str:
        """URL for cross-VM replication broker. Falls back to local broker if not configured."""
        host = self.replication_rabbitmq_host or self.rabbitmq_host
        port = self.replication_rabbitmq_port or self.rabbitmq_port
        user = self.replication_rabbitmq_user or self.rabbitmq_user
        password = self.replication_rabbitmq_password or self.rabbitmq_password
        return f"amqp://{user}:{password}@{host}:{port}/"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()