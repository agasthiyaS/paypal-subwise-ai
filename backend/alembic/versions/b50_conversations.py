"""conversational chatbot: persistent conversations and chat messages

Revision ID: b50_conversations
Revises: b40_platform_expansion
Create Date: 2026-11-11 05:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b50_conversations'
down_revision: Union[str, Sequence[str], None] = 'b40_platform_expansion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. Create conversations table if not exists
    if "conversations" not in tables:
        op.create_table(
            "conversations",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("business_id", sa.Integer(), sa.ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True),
            sa.Column("account_type", sa.String(length=32), server_default="business", nullable=False),
            sa.Column("title", sa.String(length=255), server_default="New Conversation", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_conversations_id", "conversations", ["id"])
        op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
        op.create_index("ix_conversations_account_type", "conversations", ["account_type"])

    # 2. Create chat_messages table if not exists
    if "chat_messages" not in tables:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("conversation_id", sa.String(length=64), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("meta_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_chat_messages_id", "chat_messages", ["id"])
        op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "chat_messages" in tables:
        op.drop_table("chat_messages")
    if "conversations" in tables:
        op.drop_table("conversations")
