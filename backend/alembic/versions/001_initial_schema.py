"""Initial schema — creates all tables.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Tables created:
    operators             — production operators (anonymized)
    operations            — workstations / manufacturing operations
    assignments           — historical assignment records
    skill_snapshots       — pre-computed skill state per (operator, operation)
    operation_similarities — adjacency matrix between operations
    quality_metrics       — defect tracking per operator/operation/period
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── operators ────────────────────────────────────────────────────────
    op.create_table(
        "operators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("matricule", sa.String(20), nullable=False, comment="Anonymized operator identifier (GDPR)"),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("team", sa.String(50), nullable=False, comment="Production team (A/B/C/D)"),
        sa.Column("shift", sa.String(20), nullable=False, comment="Work shift (matin/apres-midi/nuit)"),
        sa.Column(
            "status",
            sa.Enum("present", "absent", "conge", name="operator_status"),
            nullable=False,
            server_default="present",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operators_matricule", "operators", ["matricule"], unique=True)
    op.create_index("ix_operators_team", "operators", ["team"])

    # ── operations ───────────────────────────────────────────────────────
    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("line", sa.String(50), nullable=False, comment="Production line identifier"),
        sa.Column("criticality", sa.Integer(), nullable=False, server_default="3",
                  comment="Criticality 1 (low) → 5 (critical bottleneck)"),
        sa.Column("nominal_cycle_time_s", sa.Float(), nullable=True,
                  comment="Nominal cycle time in seconds"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operations_code", "operations", ["code"], unique=True)
    op.create_index("ix_operations_line", "operations", ["line"])

    # ── assignments ──────────────────────────────────────────────────────
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("shift_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("shift_label", sa.String(20), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assignments_operator_id", "assignments", ["operator_id"])
    op.create_index("ix_assignments_operation_id", "assignments", ["operation_id"])
    op.create_index("ix_assignments_shift_date", "assignments", ["shift_date"])

    # ── skill_snapshots ───────────────────────────────────────────────────
    op.create_table(
        "skill_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False, server_default="0",
                  comment="Raw mastery score 0-100 (before decay)"),
        sa.Column("last_practice", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decay_rate", sa.Float(), nullable=False, server_default="90",
                  comment="Skill half-life in days"),
        sa.Column("total_hours", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operator_id", "operation_id", name="uq_skill_operator_operation"),
    )
    op.create_index("ix_skill_snapshots_operator_id", "skill_snapshots", ["operator_id"])
    op.create_index("ix_skill_snapshots_operation_id", "skill_snapshots", ["operation_id"])

    # ── operation_similarities ────────────────────────────────────────────
    op.create_table(
        "operation_similarities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("operation_id_a", sa.Integer(), nullable=False),
        sa.Column("operation_id_b", sa.Integer(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False,
                  comment="Similarity coefficient 0-1"),
        sa.ForeignKeyConstraint(["operation_id_a"], ["operations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operation_id_b"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operation_id_a", "operation_id_b", name="uq_similarity_pair"),
    )
    op.create_index("ix_op_sim_operation_id_a", "operation_similarities", ["operation_id_a"])
    op.create_index("ix_op_sim_operation_id_b", "operation_similarities", ["operation_id_b"])

    # ── quality_metrics ────────────────────────────────────────────────────
    op.create_table(
        "quality_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("defects_per_100", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pieces_produced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "operator_id", "operation_id", "period_start",
            name="uq_quality_operator_operation_period",
        ),
    )
    op.create_index("ix_quality_metrics_operator_id", "quality_metrics", ["operator_id"])
    op.create_index("ix_quality_metrics_operation_id", "quality_metrics", ["operation_id"])


def downgrade() -> None:
    op.drop_table("quality_metrics")
    op.drop_table("operation_similarities")
    op.drop_table("skill_snapshots")
    op.drop_table("assignments")
    op.drop_table("operations")
    op.drop_table("operators")
    op.execute("DROP TYPE IF EXISTS operator_status")
