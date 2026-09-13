"""chave estrangeira notifications.schedule_id -> schedules.id (ON DELETE SET NULL)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12 00:00:00.000000

Leva para bancos já existentes a FK que o modelo `Notification` passou a
declarar. Sem ela, excluir uma sessão por um caminho que não passa por
`delete_schedule` (ex.: cascata ao excluir a matéria) deixava a notificação
apontando para um agendamento inexistente.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = 'fk_notifications_schedule_id_schedules'


def _has_fk() -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(
        fk.get('referred_table') == 'schedules'
        and fk.get('constrained_columns') == ['schedule_id']
        for fk in inspector.get_foreign_keys('notifications')
    )


def upgrade() -> None:
    # Notificações órfãs violariam a FK na cópia que o modo batch faz da tabela.
    # Roda sempre, mesmo quando a FK já existe, para não deixar violação herdada.
    op.execute(
        "UPDATE notifications SET schedule_id = NULL "
        "WHERE schedule_id IS NOT NULL "
        "AND schedule_id NOT IN (SELECT id FROM schedules)"
    )

    # Bancos criados pelo `create_all` depois do commit 135d1c2 já nascem com a
    # FK — nesse caso não há o que alterar no esquema.
    if _has_fk():
        return

    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_foreign_key(
            FK_NAME, 'schedules', ['schedule_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    if not _has_fk():
        return

    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_constraint(FK_NAME, type_='foreignkey')
