"""initial_schema for PostgreSQL migration

Revision ID: f4283ade5772
Revises: 
Create Date: 2026-11-06 13:19:00.735701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4283ade5772'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. business_profiles table
    op.create_table(
        'business_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), server_default='SaaS / Technology', nullable=True),
        sa.Column('monthly_baseline_revenue', sa.Float(), server_default='15000.0', nullable=True),
        sa.Column('current_cash_reserves', sa.Float(), server_default='45000.0', nullable=True),
        sa.Column('target_runway_months', sa.Integer(), server_default='6', nullable=True),
        sa.Column('risk_tolerance', sa.String(), server_default='moderate', nullable=True),
        sa.Column('currency', sa.String(), server_default='USD', nullable=True),
        sa.Column('paypal_connected', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('paypal_mode', sa.String(), server_default='demo', nullable=True),
        sa.Column('paypal_client_id', sa.String(), nullable=True),
        sa.Column('paypal_client_secret', sa.String(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_business_profiles_id'), 'business_profiles', ['id'], unique=False)

    # 3. transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('paypal_transaction_id', sa.String(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('raw_description', sa.String(), nullable=False),
        sa.Column('normalized_vendor', sa.String(), nullable=False),
        sa.Column('category', sa.String(), server_default='General Software', nullable=True),
        sa.Column('gross_amount', sa.Float(), nullable=False),
        sa.Column('fee_amount', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('net_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), server_default='USD', nullable=True),
        sa.Column('status', sa.String(), server_default='COMPLETED', nullable=True),
        sa.Column('data_source', sa.String(), server_default='demo', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['business_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_business_id'), 'transactions', ['business_id'], unique=False)
    op.create_index(op.f('ix_transactions_paypal_transaction_id'), 'transactions', ['paypal_transaction_id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_date'), 'transactions', ['transaction_date'], unique=False)
    op.create_index(op.f('ix_transactions_normalized_vendor'), 'transactions', ['normalized_vendor'], unique=False)
    op.create_index('idx_biz_vendor_date', 'transactions', ['business_id', 'normalized_vendor', 'transaction_date'], unique=False)

    # 4. subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('vendor_name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), server_default='Productivity', nullable=True),
        sa.Column('cadence', sa.String(), server_default='monthly', nullable=True),
        sa.Column('average_amount', sa.Float(), nullable=False),
        sa.Column('latest_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), server_default='USD', nullable=True),
        sa.Column('first_billed_date', sa.DateTime(), nullable=False),
        sa.Column('last_billed_date', sa.DateTime(), nullable=False),
        sa.Column('next_billing_date', sa.DateTime(), nullable=False),
        sa.Column('price_change_pct', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('confidence_score', sa.Float(), server_default='0.95', nullable=True),
        sa.Column('priority_tier', sa.Integer(), server_default='2', nullable=True),
        sa.Column('redundancy_group', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='active', nullable=True),
        sa.Column('utilization_score', sa.Float(), server_default='0.7', nullable=True),
        sa.Column('is_essential', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['business_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_business_id'), 'subscriptions', ['business_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_vendor_name'), 'subscriptions', ['vendor_name'], unique=False)

    # 5. recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('action_plan', sa.Text(), nullable=True),
        sa.Column('potential_monthly_saving', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('potential_annual_saving', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('runway_impact_days', sa.Integer(), server_default='0', nullable=True),
        sa.Column('negotiation_script', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['business_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_recommendations_business_id'), 'recommendations', ['business_id'], unique=False)

    # 6. scenario_simulations table
    op.create_table(
        'scenario_simulations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(), nullable=False),
        sa.Column('revenue_shock_pct', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('paused_subscription_ids', sa.JSON(), nullable=True),
        sa.Column('initial_cash_reserves', sa.Float(), nullable=False),
        sa.Column('projected_burn_rate', sa.Float(), nullable=False),
        sa.Column('projected_runway_months', sa.Float(), nullable=False),
        sa.Column('depletion_month', sa.String(), nullable=True),
        sa.Column('monthly_projection_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['business_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenario_simulations_id'), 'scenario_simulations', ['id'], unique=False)
    op.create_index(op.f('ix_scenario_simulations_business_id'), 'scenario_simulations', ['business_id'], unique=False)


def downgrade() -> None:
    op.drop_table('scenario_simulations')
    op.drop_table('recommendations')
    op.drop_table('subscriptions')
    op.drop_table('transactions')
    op.drop_table('business_profiles')
    op.drop_table('users')
