"""TMP - TaskV2.type

Revision ID: b9e9eed9d442
Revises: 9cd305cd6023
Create Date: 2024-03-27 13:10:34.125503

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op


# revision identifiers, used by Alembic.
revision = "b9e9eed9d442"
down_revision = "9cd305cd6023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("taskv2", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "type", sqlmodel.sql.sqltypes.AutoString(), nullable=False
            )
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("taskv2", schema=None) as batch_op:
        batch_op.drop_column("type")

    # ### end Alembic commands ###