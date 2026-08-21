"""add authentication and soft delete

Revision ID: b6f91c2e4a10
Revises: dc47eddc938a
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6f91c2e4a10"
down_revision: Union[str, Sequence[str], None] = "dc47eddc938a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # 簡易ログイン時代のユーザーと履歴は残すが、ログインはできない値にする。
    op.execute(
        sa.text(
            "UPDATE users "
            "SET email = 'legacy-' || id || '@invalid.local', "
            "password_hash = '!legacy-account-disabled!'"
        )
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=320),
            nullable=False,
        )
        batch_op.alter_column(
            "password_hash",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_users_email",
            ["email"],
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_email", type_="unique")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("is_admin")
        batch_op.drop_column("password_hash")
        batch_op.drop_column("email")
