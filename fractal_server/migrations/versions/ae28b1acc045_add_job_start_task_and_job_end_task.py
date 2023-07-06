"""Add job.start_task and job.end_task

Revision ID: ae28b1acc045
Revises: f384e1c0cf5d
Create Date: 2023-07-06 16:34:42.476966

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "ae28b1acc045"
down_revision = "f384e1c0cf5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("applyworkflow", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("start_task", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("end_task", sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("applyworkflow", schema=None) as batch_op:
        batch_op.drop_column("end_task")
        batch_op.drop_column("start_task")

    # ### end Alembic commands ###
