"""Initial schema - events and snapshots tables

Revision ID: 001
Revises: 
Create Date: 2025-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create event_category enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE event_category AS ENUM (
                'WORLD', 'INTERNAL', 'AGENT_ACTION', 'OBSERVATION'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('tick', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category', sa.Enum('WORLD', 'INTERNAL', 'AGENT_ACTION', 'OBSERVATION', name='event_category'), server_default='WORLD'),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('target', sa.String(255), nullable=False),
        sa.Column('salience', sa.Float(), server_default='0.5'),
        sa.Column('emotion_valence', sa.Float(), nullable=True),
        sa.Column('emotion_arousal', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), server_default='{}'),
    )
    
    # Add vector column for events
    op.execute('ALTER TABLE events ADD COLUMN effect vector(8)')
    
    # Create snapshots table
    op.create_table(
        'snapshots',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('tick', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consolidation_level', sa.SmallInteger(), server_default='0'),
        sa.Column('last_accessed', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('strength', sa.Float(), server_default='1.0'),
        sa.Column('salience', sa.Float(), server_default='0.5'),
        sa.Column('goals', sa.JSON(), server_default='[]'),
        sa.Column('metadata', sa.JSON(), server_default='{}'),
    )
    
    # Add vector column for snapshots
    op.execute('ALTER TABLE snapshots ADD COLUMN state_vector vector(8)')
    
    # Create indexes
    op.create_index('idx_events_agent_tick', 'events', ['agent_id', 'tick'])
    op.create_index('idx_events_category', 'events', ['category'])
    op.create_index('idx_snapshots_agent_tick', 'snapshots', ['agent_id', 'tick'])
    
    # Vector index (ivfflat)
    op.execute('''
        CREATE INDEX idx_snapshots_vector ON snapshots 
        USING ivfflat (state_vector vector_l2_ops) WITH (lists = 100)
    ''')
    
    # JSONB indexes
    op.execute('CREATE INDEX idx_events_metadata ON events USING gin (metadata)')
    op.execute('CREATE INDEX idx_snapshots_metadata ON snapshots USING gin (metadata)')


def downgrade() -> None:
    op.drop_table('snapshots')
    op.drop_table('events')
    op.execute('DROP TYPE IF EXISTS event_category')
