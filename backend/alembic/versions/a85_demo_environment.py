"""add demo business environment support

Revision ID: a85_demo_environment
Revises: f4283ade5772
Create Date: 2026-11-08 08:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a85_demo_environment'
down_revision: Union[str, Sequence[str], None] = 'f4283ade5772'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add demo columns to business_profiles
    op.add_column('business_profiles', sa.Column('is_demo', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('business_profiles', sa.Column('profile_type', sa.String(), server_default='STANDARD', nullable=True))
    
    # 2. Drop single-column unique constraint on user_id in business_profiles to allow (user_id, is_demo)
    # Check if constraint exists before dropping
    op.drop_constraint('business_profiles_user_id_key', 'business_profiles', type_='unique')
    op.create_unique_constraint('uq_business_user_demo', 'business_profiles', ['user_id', 'is_demo'])
    
    # 3. Add active_business_id to users
    op.add_column('users', sa.Column('active_business_id', sa.Integer(), nullable=True))
    
    # 4. Add is_simulated to transactions
    op.add_column('transactions', sa.Column('is_simulated', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('transactions', 'is_simulated')
    op.drop_column('users', 'active_business_id')
    op.drop_constraint('uq_business_user_demo', 'business_profiles', type_='unique')
    op.create_unique_constraint('business_profiles_user_id_key', 'business_profiles', ['user_id'])
    op.drop_column('business_profiles', 'profile_type')
    op.drop_column('business_profiles', 'is_demo')

