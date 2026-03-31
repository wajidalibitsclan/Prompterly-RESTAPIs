#!/usr/bin/env python3
"""Generate PDF gap analysis report for Prompterly Security & Data Architecture Standard."""

from fpdf import FPDF


class GapReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "Prompterly - Security & Data Architecture Gap Analysis", align="R")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(41, 41, 41)
        self.set_text_color(255, 255, 255)
        self.cell(0, 9, f"  {num}. {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def status_badge(self, status):
        colors = {
            "NOT Implemented": (220, 53, 69),
            "PARTIALLY Implemented": (255, 152, 0),
            "Mostly Implemented": (76, 175, 80),
            "Implemented": (56, 142, 60),
        }
        r, g, b = colors.get(status, (100, 100, 100))
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(r, g, b)
        w = self.get_string_width(f"Status: {status}") + 6
        self.cell(w, 7, f"Status: {status}")
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def sub_heading(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(51, 51, 51)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def table_row(self, requirement, current_state, is_header=False):
        self.set_font("Helvetica", "B" if is_header else "", 9)
        col1_w = 80
        col2_w = 110

        if is_header:
            self.set_fill_color(230, 230, 230)
            self.cell(col1_w, 7, requirement, border=1, fill=True)
            self.cell(col2_w, 7, current_state, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            x = self.get_x()
            y = self.get_y()

            # Calculate heights
            self.set_font("Helvetica", "B", 8)
            req_lines = self.multi_cell(col1_w, 5, requirement, border=0, split_only=True)
            self.set_font("Helvetica", "", 8)
            state_lines = self.multi_cell(col2_w, 5, current_state, border=0, split_only=True)

            row_h = max(len(req_lines), len(state_lines)) * 5 + 2

            if y + row_h > 270:
                self.add_page()
                y = self.get_y()
                x = self.get_x()

            # Draw cells
            self.rect(x, y, col1_w, row_h)
            self.rect(x + col1_w, y, col2_w, row_h)

            self.set_xy(x + 1, y + 1)
            self.set_font("Helvetica", "B", 8)
            self.multi_cell(col1_w - 2, 5, requirement)

            self.set_xy(x + col1_w + 1, y + 1)
            self.set_font("Helvetica", "", 8)
            self.multi_cell(col2_w - 2, 5, current_state)

            self.set_y(y + row_h)

    def bullet(self, text, indent=15):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 51, 51)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5, "-")
        self.multi_cell(170 - indent, 5, text)
        self.ln(1)

    def para(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def priority_item(self, num, text, color):
        r, g, b = color
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(r, g, b)
        self.cell(8, 6, f"{num}.")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 51, 51)
        self.multi_cell(175, 6, text)
        self.ln(1)


def build_report():
    pdf = GapReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(41, 41, 41)
    pdf.cell(0, 12, "Gap Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Prompterly Security & Data Architecture Standard vs Current Implementation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Date: March 6, 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ─── Section 1: Data Categories ───
    pdf.section_title("1", "Data Categories Stored")
    pdf.status_badge("Mostly Implemented")
    pdf.para("User data, user-generated content, platform data, mentor data, and payment data are all modeled in the database.")
    pdf.sub_heading("Gap:")
    pdf.bullet("Missing dedicated 'Notification preferences' field on User model (no dedicated column)")
    pdf.ln(3)

    # ─── Section 2: Data Separation ───
    pdf.section_title("2", "Data Separation & Pseudonymisation Architecture")
    pdf.status_badge("NOT Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row(
        "2.1 UUID-based user identifier",
        "Users have auto-incrementing integer IDs, not user_uuid. All content tables reference user_id (integer FK) directly."
    )
    pdf.table_row(
        "2.2 Separation of identity & content data",
        "Identity fields (name, email) and content (chat, notes, capsules) are directly linked via foreign keys to the same User table. No logical separation exists."
    )
    pdf.table_row(
        "2.3 Mapping table (uuid to identity)",
        "Does not exist. No pseudonymous mapping layer is implemented."
    )
    pdf.table_row(
        "2.4 Access restrictions on identity-content linking",
        "Admin endpoints can directly associate conversations with identity. No MFA for admin access."
    )
    pdf.table_row(
        "2.5 Logging considerations",
        "Logs may include user_id alongside request data. No safeguard against logging conversation content."
    )
    pdf.table_row(
        "2.6 Data export (GDPR)",
        "ComplianceRequest model exists but no actual export endpoint is implemented (no JSON/CSV/PDF export)."
    )
    pdf.table_row(
        "2.7 Data deletion & anonymisation",
        "ComplianceRequest model supports deletion requests but no anonymisation logic is implemented. No account deletion endpoint."
    )
    pdf.ln(3)

    # ─── Section 3: Encryption ───
    pdf.section_title("3", "Encryption Standards")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row(
        "Encryption in transit (HTTPS/TLS 1.2+)",
        "NGINX config exists but TLS enforcement needs to be verified in production deployment."
    )
    pdf.table_row(
        "Encryption at rest (DB, S3, backups)",
        "NOT configured at application level. No AES-256 encryption on MySQL or S3. Depends entirely on infrastructure setup."
    )
    pdf.table_row(
        "Application-level encryption of sensitive content (chat, notes, capsules)",
        "NOT implemented. Chat messages, notebook entries, and time capsule content are stored in plaintext in the database."
    )
    pdf.table_row(
        "Encryption key management (AWS KMS or equivalent)",
        "NOT implemented. No KMS integration. No key management service configured anywhere in the codebase."
    )
    pdf.table_row(
        "Search on encrypted content",
        "Not applicable yet since encryption is not implemented."
    )
    pdf.ln(3)

    # ─── Section 4: Password & Auth ───
    pdf.section_title("4", "Password & Authentication Security")
    pdf.status_badge("Mostly Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("Bcrypt password hashing", "Implemented - dual SHA-256 pre-hash + bcrypt.")
    pdf.table_row("Token expiration", "Implemented - access: 30 min, refresh: 7 days.")
    pdf.table_row(
        "Token invalidation on logout",
        "PARTIAL - UserSession model exists but no explicit logout endpoint that revokes all sessions."
    )
    pdf.table_row("Role-based permissions", "Implemented - MEMBER, MENTOR, ADMIN roles.")
    pdf.table_row(
        "MFA for admin access",
        "NOT implemented - no multi-factor authentication at all."
    )
    pdf.table_row(
        "Rate limiting on login/auth endpoints",
        "NOT implemented - RateLimitExceededError exception is defined but no actual rate limiting middleware is active. Config values exist but are unused."
    )
    pdf.table_row(
        "Block repeated failed login attempts",
        "NOT implemented - no account lockout or IP-based throttling."
    )
    pdf.ln(3)

    # ─── Section 5: Secrets Management ───
    pdf.section_title("5", "Secrets & Credential Management")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row(
        "No hardcoded secrets in code",
        "Implemented - uses .env files with pydantic-settings for configuration."
    )
    pdf.table_row(
        "Managed secret storage (AWS Secrets Manager, Vault, etc.)",
        "NOT implemented - secrets stored in .env files on disk. No integration with AWS Secrets Manager, Parameter Store, or HashiCorp Vault."
    )
    pdf.ln(3)

    # ─── Section 6: Backups ───
    pdf.section_title("6", "Data Backups & Disaster Recovery")
    pdf.status_badge("NOT Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("Automated daily database backups", "No backup scripts or cron jobs exist in the codebase.")
    pdf.table_row("Encrypted backup storage (S3 with AES-256)", "Not configured.")
    pdf.table_row("Backup retention (30 days daily, 12 months monthly)", "No retention policy configured.")
    pdf.table_row("Restore capability & periodic testing", "No restore scripts or documented procedures.")
    pdf.ln(3)

    # ─── Section 7: Data Retention ───
    pdf.section_title("7", "Data Retention Policy")
    pdf.status_badge("NOT Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("System logs: 60-day retention + rotation", "No log rotation configured. Logs write to files indefinitely.")
    pdf.table_row("Audit logs: 12-month retention", "No retention or cleanup policy on AuditLog table.")
    pdf.table_row("Automatic log deletion after retention period", "Not implemented.")
    pdf.ln(3)

    # ─── Section 8: Legal Hold ───
    pdf.section_title("8", "Legal Preservation (Legal Hold)")
    pdf.status_badge("NOT Implemented")
    pdf.para("No mechanism to temporarily disable deletion of account data. No legal hold flag on users or compliance requests. No admin interface to place or remove legal holds.")
    pdf.ln(2)

    # ─── Section 9: Audit Logging ───
    pdf.section_title("9", "Audit Logging")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("AuditLog model", "Exists with action, entity, IP, and changes tracking.")
    pdf.table_row("Account creation/deletion logging", "Partial - auth events logged, but no systematic audit of all critical actions.")
    pdf.table_row("Administrative actions logging", "Not consistently applied across all admin endpoints.")
    pdf.table_row("Subscription changes logging", "Not audited.")
    pdf.table_row("Separate storage from app logs", "NOT implemented - audit logs stored in same database as application data.")
    pdf.ln(3)

    # ─── Section 10: User Data Export ───
    pdf.section_title("10", "User Data Export")
    pdf.status_badge("NOT Implemented")
    pdf.para("ComplianceRequest model supports 'export' type but no actual export functionality exists. No endpoint to generate JSON, CSV, or PDF exports of user chat history, notebook entries, or time capsule entries.")
    pdf.ln(2)

    # ─── Section 11: Payment Processing ───
    pdf.section_title("11", "Payment Processing (Stripe)")
    pdf.status_badge("Mostly Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("Stripe integration", "Implemented with subscription plans and payments.")
    pdf.table_row("No raw credit card storage", "Correct - uses Stripe tokens/IDs only.")
    pdf.table_row("Webhook signature validation", "STRIPE_WEBHOOK_SECRET configured but implementation needs audit.")
    pdf.table_row("Timestamp tolerance for replay attacks", "Not explicitly implemented.")
    pdf.ln(3)

    # ─── Section 12: Minimum Age ───
    pdf.section_title("12", "Minimum Age Requirements")
    pdf.status_badge("NOT Implemented")
    pdf.para("No age confirmation checkbox or field during registration. No date_of_birth or age_confirmed field on the User model. No terms acceptance tracking.")
    pdf.ln(2)

    # ─── Section 13: Security Monitoring ───
    pdf.section_title("13", "Security Monitoring & Incident Response")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("Error tracking", "Sentry integration configured (optional).")
    pdf.table_row("Incident response procedures", "No documented procedures exist.")
    pdf.table_row("User breach notification system", "Not implemented.")
    pdf.ln(3)

    # ─── Section 14: AI Data Boundaries ───
    pdf.section_title("14", "AI System Data Boundaries")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("AI uses mentor frameworks + user prompts", "Implemented via ai_service.py.")
    pdf.table_row("System guardrails", "Basic implementation, needs comprehensive audit.")
    pdf.table_row("No training on user data enforcement", "Not enforced - relies on provider settings. No contractual or technical safeguard visible in code.")
    pdf.ln(3)

    # ─── Section 15: Mentor Framework Versioning ───
    pdf.section_title("15", "Mentor Framework / IP Versioning")
    pdf.status_badge("NOT Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("Versioned configuration records", "NOT implemented - no version tracking on lounge/mentor configurations.")
    pdf.table_row("Immutable historical versions", "Not implemented.")
    pdf.table_row("Chat sessions linked to config version", "Not implemented - no way to reconstruct which config generated past responses.")
    pdf.table_row("Rollback capability", "Not implemented.")
    pdf.ln(3)

    # ─── Section 16: Compliance ───
    pdf.section_title("16", "Data Protection Compliance")
    pdf.status_badge("PARTIALLY Implemented")

    pdf.table_row("Requirement", "Current State", is_header=True)
    pdf.table_row("ComplianceRequest model (GDPR/CCPA)", "Model exists with export and delete request types.")
    pdf.table_row("Actual GDPR export/delete workflows", "NOT implemented - model exists but no processing logic.")
    pdf.ln(5)

    # ─── Priority Summary ───
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(41, 41, 41)
    pdf.cell(0, 10, "Priority Summary", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # CRITICAL
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(220, 53, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  CRITICAL - Must Fix Before Launch", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    critical = [
        "Data Separation & Pseudonymisation - Switch to UUID identifiers, separate identity from content tables",
        "Application-level Encryption - Encrypt chat messages, notes, time capsules before DB storage with AWS KMS",
        "Rate Limiting - Activate rate limiting on auth endpoints (currently defined but unused)",
        "Data Backup & Disaster Recovery - Set up automated encrypted daily backups with retention policy",
        "Mentor Framework Versioning - Implement immutable config versions linked to chat sessions",
    ]
    for i, item in enumerate(critical, 1):
        pdf.priority_item(i, item, (220, 53, 69))

    pdf.ln(4)

    # HIGH
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(255, 152, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  HIGH - Should Fix Before Launch", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    high = [
        "MFA for Admin Access - Implement multi-factor authentication for administrative users",
        "User Data Export - Implement actual JSON/CSV/PDF export endpoints for GDPR compliance",
        "Account Deletion with Anonymisation - Implement proper GDPR deletion flow with identity anonymisation",
        "Age Confirmation - Add 18+ confirmation checkbox during registration",
        "Secrets Management - Migrate from .env files to AWS Secrets Manager or equivalent",
        "Encryption Key Management - Integrate AWS KMS for managing encryption keys",
    ]
    for i, item in enumerate(high, 6):
        pdf.priority_item(i, item, (255, 152, 0))

    pdf.ln(4)

    # MEDIUM
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(33, 150, 243)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  MEDIUM - Should Address Soon After Launch", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    medium = [
        "Log Rotation - Implement 60-day retention with automatic cleanup and size-based rotation",
        "Legal Hold Mechanism - Admin ability to freeze account deletion for legal preservation",
        "Audit Log Completeness - Ensure all critical platform actions are consistently audited",
        "Stripe Webhook Replay Protection - Enforce timestamp tolerance on webhook validation",
        "Incident Response Documentation - Create and maintain documented response procedures",
    ]
    for i, item in enumerate(medium, 12):
        pdf.priority_item(i, item, (33, 150, 243))

    # Save
    output_path = "/home/wajid-ali/Projects/Prompterly/RESTAPI/RESTAPI-Prompterly/Prompterly_Gap_Analysis_Report.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_report()
