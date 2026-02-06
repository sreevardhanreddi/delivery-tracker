"""drop events column from trackpackage

Revision ID: b8f24d3e9a01
Revises: a7313c5e7768
Create Date: 2026-02-06 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8f24d3e9a01"
down_revision: Union[str, Sequence[str], None] = "a7313c5e7768"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("trackpackage", "events")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "trackpackage",
        sa.Column(
            "events",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="[]",
        ),
    )
