"""recorrência de agendamentos e token de exportação ics

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-31 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recurrence_group_id', sa.String(length=36), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_schedules_recurrence_group_id'), ['recurrence_group_id'], unique=False
        )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ics_token', sa.String(length=64), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_users_ics_token'), ['ics_token'], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_ics_token'))
        batch_op.drop_column('ics_token')

    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_schedules_recurrence_group_id'))
        batch_op.drop_column('recurrence_group_id')
