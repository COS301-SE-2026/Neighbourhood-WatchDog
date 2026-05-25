from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Import all models so Alembic can detect them
from app.core.database import Base
from app.models.user import User
from app.models.neighbourhood import Neighbourhood
from app.models.property import Property
from app.models.camera import Camera
from app.models.detection_event import DetectionEvent
from app.models.alert import Alert
from app.models.zone import GeospatialZone
from app.models.retention_policy import RetentionPolicy
from app.models.neighbourhood_join_request import NeighbourhoodJoinRequest
from app.models.audit_log import AuditLog
from app.models.user_property import UserProperty
from app.models.property_user import PropertyUser

config = context.config

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# -------------------------------------------------------
# This function tells Alembic to ignore PostGIS system
# tables (tiger, topology, spatial_ref_sys, etc.) that
# exist in the DB but are not part of models.
# Without this, Alembic tries to drop them all.
# -------------------------------------------------------
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,        
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,    
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()