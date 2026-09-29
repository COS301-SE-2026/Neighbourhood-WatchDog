"""merge existing migration heads before incident grouping"""

from typing import Sequence, Union


revision: str = "merge_pre_incident_heads"

down_revision: Union[str, Sequence[str], None] = (
    "05696974518c",
    "7eadb5195151",
    "a7f3c9d1e2b4",
)

branch_labels = None
depends_on = None


def upgrade() -> None:
    # No schema changes. This only consolidates the existing migration heads.
    pass


def downgrade() -> None:
    pass