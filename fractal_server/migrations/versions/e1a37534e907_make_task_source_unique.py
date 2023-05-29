"""Make task.source unique

Revision ID: e1a37534e907
Revises: 62f2f0c4ac49
Create Date: 2023-05-29 12:05:05.654350

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "e1a37534e907"
down_revision = "62f2f0c4ac49"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "task", ["source"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "task", type_="unique")
    # ### end Alembic commands ###
