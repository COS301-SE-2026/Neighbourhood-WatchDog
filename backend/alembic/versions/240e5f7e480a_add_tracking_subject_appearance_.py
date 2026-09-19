"""add tracking subject appearance embedding

Revision ID: USE_GENERATED_REVISION_ID
Revises: 7eadb5195151
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "240e5f7e480a"
down_revision = "7eadb5195151"
branch_labels = None
depends_on = None


APPEARANCE_EMBEDDING_DIMENSION = 1280


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "tracking_subject",
        sa.Column(
            "reference_embedding",
            Vector(APPEARANCE_EMBEDDING_DIMENSION),
            nullable=True,
        ),
    )

    op.add_column(
        "tracking_subject",
        sa.Column(
            "embedding_model",
            sa.String(length=128),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_tracking_subject_reference_embedding_hnsw",
        "tracking_subject",
        ["reference_embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={
            "reference_embedding": "vector_cosine_ops",
        },
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tracking_subject_reference_embedding_hnsw",
        table_name="tracking_subject",
    )

    op.drop_column(
        "tracking_subject",
        "embedding_model",
    )

    op.drop_column(
        "tracking_subject",
        "reference_embedding",
    )

    # Do not drop the vector extension during downgrade.
    # Other future tables may depend on it.