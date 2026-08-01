"""change document id to string

Revision ID: e6a9d12f2e5e
Revises: 5993cff0418e
Create Date: 2026-08-01 12:03:07.714774

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e6a9d12f2e5e"
down_revision: Union[str, Sequence[str], None] = "5993cff0418e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.Integer(),
            type_=sa.String(length=36),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=36),
            type_=sa.Integer(),
            existing_nullable=False,
        )
