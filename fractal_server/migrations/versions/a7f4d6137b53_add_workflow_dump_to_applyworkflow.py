"""Add ApplyWorkflow.workflow_dump

Revision ID: a7f4d6137b53
Revises: 70e77f1c38b0
Create Date: 2023-07-24 16:53:02.569582

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "a7f4d6137b53"
down_revision = "70e77f1c38b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("applyworkflow", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("workflow_dump", sa.JSON(), nullable=True)
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("applyworkflow", schema=None) as batch_op:
        batch_op.drop_column("workflow_dump")

    # ### end Alembic commands ###
