"""create personal and household finance tables (expenses, household_members, budgets)

Revision ID: b20_personal_household_finance
Revises: b10_account_type
Create Date: 2026-11-10 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b20_personal_household_finance'
down_revision: Union[str, Sequence[str], None] = 'b10_account_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. Create household_members table
    if 'household_members' not in tables:
        op.create_table(
            'household_members',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('business_id', sa.Integer(), sa.ForeignKey('business_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('role', sa.String(), server_default='Member', nullable=False),
            sa.Column('avatar_color', sa.String(), server_default='#0070ba', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('monthly_income_share', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_household_members_business_id', 'household_members', ['business_id'])

    # 2. Create expenses table
    if 'expenses' not in tables:
        op.create_table(
            'expenses',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('business_id', sa.Integer(), sa.ForeignKey('business_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(), server_default='USD', nullable=False),
            sa.Column('expense_type', sa.String(), server_default='expense', nullable=False),
            sa.Column('category', sa.String(), server_default='Other', nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('merchant', sa.String(), nullable=True),
            sa.Column('expense_date', sa.DateTime(), nullable=False),
            sa.Column('is_recurring', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('payment_method', sa.String(), server_default='Manual Entry', nullable=False),
            sa.Column('household_member_id', sa.Integer(), sa.ForeignKey('household_members.id', ondelete='SET NULL'), nullable=True),
            sa.Column('is_shared', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('data_source', sa.String(), server_default='manual', nullable=False),
            sa.Column('paypal_transaction_id', sa.String(), nullable=True),
            sa.Column('categorization_method', sa.String(), server_default='manual', nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_expenses_business_id', 'expenses', ['business_id'])
        op.create_index('ix_expenses_user_id', 'expenses', ['user_id'])
        op.create_index('ix_expenses_category', 'expenses', ['category'])
        op.create_index('ix_expenses_expense_date', 'expenses', ['expense_date'])
        op.create_index('ix_expenses_household_member_id', 'expenses', ['household_member_id'])
        op.create_index('ix_expenses_paypal_transaction_id', 'expenses', ['paypal_transaction_id'])
        op.create_index('idx_expense_biz_date', 'expenses', ['business_id', 'expense_date'])

    # 3. Create budgets table
    if 'budgets' not in tables:
        op.create_table(
            'budgets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('business_id', sa.Integer(), sa.ForeignKey('business_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('category', sa.String(), server_default='Overall', nullable=False),
            sa.Column('monthly_limit', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(), server_default='USD', nullable=False),
            sa.Column('period_month', sa.Integer(), nullable=True),
            sa.Column('period_year', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('business_id', 'category', 'period_month', 'period_year', name='uq_budget_category_period')
        )
        op.create_index('ix_budgets_business_id', 'budgets', ['business_id'])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'budgets' in tables:
        op.drop_table('budgets')
    if 'expenses' in tables:
        op.drop_table('expenses')
    if 'household_members' in tables:
        op.drop_table('household_members')

