"""add ai_interpretation chat waitlist and notification tables

Revision ID: a88e01cfb395
Revises: 2306685d216c
Create Date: 2026-05-09 12:02:11.171646
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a88e01cfb395"
down_revision: Union[str, None] = "2306685d216c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "waitlist",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "medical_cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("guest_session_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medical_cases_user_id"),
        "medical_cases",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "ai_interpretation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("medical_case_id", sa.UUID(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("value_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggested_questions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_level", sa.Enum("low", "moderate", "high", name="risklevel"), nullable=True),
        sa.Column("confidence", sa.Enum("low", "medium", "high", name="confidence"), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "complete",
                "failed",
                name="interpretationstatus",
            ),
            nullable=False,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medical_case_id"], ["medical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_interpretation_medical_case_id"),
        "ai_interpretation",
        ["medical_case_id"],
        unique=False,
    )

    op.create_table(
        "chat",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("sender_type", sa.Enum("patient", "ai", name="sendertype"), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("medical_case_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["medical_case_id"], ["medical_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_medical_case_id"), "chat", ["medical_case_id"], unique=False)
    op.create_index(op.f("ix_chat_user_id"), "chat", ["user_id"], unique=False)

    op.create_table(
        "lab_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("medical_case_id", sa.UUID(), nullable=False),
        sa.Column("file", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ocr_status", sa.String(), nullable=False),
        sa.Column("extracted_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ocr_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medical_case_id"], ["medical_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lab_results_medical_case_id"),
        "lab_results",
        ["medical_case_id"],
        unique=False,
    )

    op.create_table(
        "notification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("medical_case_id", sa.UUID(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "interpretation_ready",
                "interpretation_failed",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["medical_case_id"], ["medical_cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notification_medical_case_id"),
        "notification",
        ["medical_case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_user_id"),
        "notification",
        ["user_id"],
        unique=False,
    )

    op.execute(
        "INSERT INTO medical_cases "
        "(id, guest_session_id, status, created_at, completed_at) "
        "SELECT id, guest_session_id, status, created_at, completed_at "
        "FROM medical_case"
    )

    op.execute(
        "INSERT INTO lab_results "
        "(id, medical_case_id, file, ocr_status, extracted_values, ocr_completed_at, created_at) "
        "SELECT id, medical_case_id, file, ocr_status, extracted_data, ocr_completed_at, created_at "
        "FROM lab_result"
    )

    op.drop_index(op.f("ix_lab_result_medical_case_id"), table_name="lab_result")
    op.drop_table("lab_result")
    op.drop_index(op.f("ix_medical_case_user_id"), table_name="medical_case")
    op.drop_table("medical_case")


def downgrade() -> None:
    op.create_table(
        "medical_case",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.Integer(), autoincrement=False, nullable=True),
        sa.Column("guest_session_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("status", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column("completed_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("medical_case_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("medical_case_pkey")),
    )
    op.create_index(op.f("ix_medical_case_user_id"), "medical_case", ["user_id"], unique=False)

    op.create_table(
        "lab_result",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("medical_case_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("file", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
        sa.Column("ocr_status", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.Column("ocr_completed_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["medical_case_id"],
            ["medical_case.id"],
            name=op.f("lab_result_medical_case_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("lab_result_pkey")),
    )
    op.create_index(op.f("ix_lab_result_medical_case_id"), "lab_result", ["medical_case_id"], unique=False)

    op.execute(
        "INSERT INTO medical_case "
        "(id, guest_session_id, status, created_at, completed_at) "
        "SELECT id, guest_session_id, status, created_at, completed_at "
        "FROM medical_cases"
    )

    op.execute(
        "INSERT INTO lab_result "
        "(id, medical_case_id, file, ocr_status, extracted_data, ocr_completed_at, created_at) "
        "SELECT id, medical_case_id, file, ocr_status, COALESCE(extracted_values, '{}'), "
        "ocr_completed_at, created_at FROM lab_results"
    )

    op.drop_index(op.f("ix_notification_user_id"), table_name="notification")
    op.drop_index(op.f("ix_notification_medical_case_id"), table_name="notification")
    op.drop_table("notification")
    op.drop_index(op.f("ix_lab_results_medical_case_id"), table_name="lab_results")
    op.drop_table("lab_results")
    op.drop_index(op.f("ix_chat_user_id"), table_name="chat")
    op.drop_index(op.f("ix_chat_medical_case_id"), table_name="chat")
    op.drop_table("chat")
    op.drop_index(op.f("ix_ai_interpretation_medical_case_id"), table_name="ai_interpretation")
    op.drop_table("ai_interpretation")
    op.drop_index(op.f("ix_medical_cases_user_id"), table_name="medical_cases")
    op.drop_table("medical_cases")
    op.drop_table("waitlist")

    sa.Enum(name="notificationtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sendertype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="interpretationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="confidence").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="risklevel").drop(op.get_bind(), checkfirst=True)