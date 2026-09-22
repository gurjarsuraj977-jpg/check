"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(100), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("sessions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("csrf_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"]); op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True); op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_table("login_attempts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(100), nullable=False), sa.Column("ip_hash", sa.String(64), nullable=False), sa.Column("succeeded", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_login_attempts_username", "login_attempts", ["username"]); op.create_index("ix_login_attempts_ip_hash", "login_attempts", ["ip_hash"]); op.create_index("ix_login_attempts_created_at", "login_attempts", ["created_at"])
    op.create_table("batches", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("batch_reference", sa.String(64), nullable=False), sa.Column("total", sa.Integer(), nullable=False), sa.Column("processed", sa.Integer(), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_batches_batch_reference", "batches", ["batch_reference"], unique=True); op.create_index("ix_batches_status", "batches", ["status"])
    op.create_table("credential_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=False), sa.Column("key_reference", sa.String(64), nullable=False), sa.Column("encrypted_value", sa.Text(), nullable=False), sa.Column("fingerprint", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("report_status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("tested_at", sa.DateTime(), nullable=True), sa.Column("deleted_at", sa.DateTime(), nullable=True), sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True), sa.UniqueConstraint("fingerprint", name="uq_credential_fingerprint"))
    op.create_index("ix_credential_records_batch_id", "credential_records", ["batch_id"]); op.create_index("ix_credential_records_key_reference", "credential_records", ["key_reference"]); op.create_index("ix_credential_records_fingerprint", "credential_records", ["fingerprint"]); op.create_index("ix_credential_records_status", "credential_records", ["status"]); op.create_index("ix_credential_records_report_status", "credential_records", ["report_status"])
    op.create_table("audit_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("key_reference", sa.String(64), nullable=True), sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=True), sa.Column("metadata_json", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"]); op.create_index("ix_audit_events_batch_id", "audit_events", ["batch_id"]); op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

def downgrade():
    op.drop_table("audit_events"); op.drop_table("credential_records"); op.drop_table("batches"); op.drop_table("login_attempts"); op.drop_table("sessions"); op.drop_table("users")
