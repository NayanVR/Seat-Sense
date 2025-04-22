"""Add pgvector index on embedding

Revision ID: d7fca6a4dce3
Revises: 5dd0f3625445
Create Date: 2025-04-22 11:13:41.944148

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd7fca6a4dce3'
down_revision: Union[str, None] = '5dd0f3625445'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # Create an IVFFlat index on the embedding column using cosine similarity
    op.execute("""
        CREATE INDEX face_embedding_cosine_idx
        ON face_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

def downgrade():
    # Drop the index if we downgrade
    op.execute("""
        DROP INDEX IF EXISTS face_embedding_cosine_idx;
    """)