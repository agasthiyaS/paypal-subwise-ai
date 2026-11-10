"""add account_type column to business_profiles

Revision ID: b10_account_type
Revises: a85_demo_environment
Create Date: 2026-11-10 17:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b10_account_type'
down_revision: Union[str, Sequence[str], None] = 'a85_demo_environment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col['name'] for col in insp.get_columns('business_profiles')]

    if 'account_type' not in columns:
        # Fresh database or database where column does not yet exist
        with op.batch_alter_table('business_profiles') as batch_op:
            batch_op.add_column(
                sa.Column('account_type', sa.String(), server_default='business', nullable=False)
            )
    else:
        # Existing database where column already exists (e.g. from Phase 1 direct SQL)
        # Ensure any NULL records receive 'business' without overwriting existing individual/household values
        op.execute(sa.text("UPDATE business_profiles SET account_type = 'business' WHERE account_type IS NULL"))
        with op.batch_alter_table('business_profiles') as batch_op:
            batch_op.alter_column(
                'account_type',
                server_default='business',
                nullable=False,
                existing_type=sa.String()
            )


def downgrade() -> None:
    """
    WARNING - ARCHITECTURAL IMPACT:
    Downgrading this migration drops the 'account_type' column from 'business_profiles'.
    This removes the distinction between 'individual', 'household', and 'business'
    account profiles and will revert the application to legacy single-tenant behavior.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col['name'] for col in insp.get_columns('business_profiles')]
    if 'account_type' in columns:
        with op.batch_alter_table('business_profiles') as batch_op:
            batch_op.drop_column('account_type')

