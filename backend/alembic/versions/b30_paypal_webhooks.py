"""create webhook_events table for paypal webhook intelligence

Revision ID: b30_paypal_webhooks
Revises: b20_personal_household_finance
Create Date: 2026-11-10 22:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b30_paypal_webhooks'
down_revision: Union[str, Sequence[str], None] = 'b20_personal_household_finance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'webhook_events' not in tables:
        op.create_table(
            'webhook_events',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('paypal_event_id', sa.String(length=120), nullable=False),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('resource_type', sa.String(length=50), nullable=True),
            sa.Column('resource_id', sa.String(length=100), nullable=True),
            sa.Column('business_id', sa.Integer(), sa.ForeignKey('business_profiles.id', ondelete='SET NULL'), nullable=True),
            sa.Column('status', sa.String(length=30), server_default='processed', nullable=False),
            sa.Column('verification_status', sa.String(length=30), server_default='unverified', nullable=False),
            sa.Column('payload', sa.JSON(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_webhook_events_id', 'webhook_events', ['id'])
        op.create_index('ix_webhook_events_paypal_event_id', 'webhook_events', ['paypal_event_id'], unique=True)
        op.create_index('ix_webhook_events_event_type', 'webhook_events', ['event_type'])
        op.create_index('ix_webhook_events_resource_id', 'webhook_events', ['resource_id'])
        op.create_index('ix_webhook_events_business_id', 'webhook_events', ['business_id'])
        op.create_index('ix_webhook_events_status', 'webhook_events', ['status'])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'webhook_events' in tables:
        op.drop_table('webhook_events')

