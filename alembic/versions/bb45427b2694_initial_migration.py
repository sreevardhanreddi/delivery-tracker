"""initial migration

Revision ID: bb45427b2694
Revises:
Create Date: 2026-02-06 11:32:04.693708

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bb45427b2694"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table already exists (for existing databases)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "trackpackage" not in inspector.get_table_names():
        op.create_table(
            "trackpackage",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("number", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("service", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column(
                "description", sqlmodel.sql.sqltypes.AutoString(), nullable=False
            ),
            sa.Column("events", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("eta", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("number"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("trackpackage")
