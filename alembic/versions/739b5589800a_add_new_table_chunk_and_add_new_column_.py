"""add new table chunk and add new column status in document

Revision ID: 739b5589800a

Revises: 7db7ca6bd3b7

Create Date: 2026-09-21 14:46:06.551980
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "739b5589800a"
down_revision: Union[str, Sequence[str], None] = "7db7ca6bd3b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create the PostgreSQL ENUM type first.
    documentstatus = sa.Enum(
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="documentstatus",
    )

    documentstatus.create(op.get_bind(), checkfirst=True)

    # Create chunks table.
    op.create_table(
        "chunks",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add status column.
    op.add_column(
        "documents",
        sa.Column(
            "status",
            documentstatus,
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("documents", "status")

    op.drop_table("chunks")

    # Remove PostgreSQL ENUM type.
    documentstatus = sa.Enum(
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="documentstatus",
    )

    documentstatus.drop(op.get_bind(), checkfirst=True)