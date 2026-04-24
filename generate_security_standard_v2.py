#!/usr/bin/env python3
"""Generate updated Prompterly Security & Data Architecture Standard PDF (v2)."""

from fpdf import FPDF


class SecurityStandardPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "Prompterly Security & Data Architecture Standard v2.0", align="R")
        self.ln(4)
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def doc_title(self, text):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(26, 26, 31)
        self.cell(0, 12, text, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def section(self, num, title):
        if self.get_y() > 240:
            self.add_page()
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(254, 226, 197)  # Peach background like original
        self.set_text_color(0, 0, 0)
        self.cell(0, 9, f"  {num}. {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def subsection(self, num, title):
        if self.get_y() > 250:
            self.add_page()
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, f"  {num} {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def heading(self, text):
        if self.get_y() > 260:
            self.add_page()
        self.ln(1)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def para(self, text):
        if self.get_y() > 265:
            self.add_page()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        # Replace special chars
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2192", "->").replace("\u2026", "...")
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=10):
        if self.get_y() > 268:
            self.add_page()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2192", "->").replace("\u2026", "...")
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5, "-")
        self.multi_cell(186 - indent, 5, text)
        self.ln(0.5)

    def code_box(self, text):
        if self.get_y() > 260:
            self.add_page()
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, f"  {text}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def info_box(self, label, text):
        if self.get_y() > 255:
            self.add_page()
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        self.multi_cell(0, 5, text)
        self.ln(2)


def build():
    pdf = SecurityStandardPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ===== Cover / Header =====
    pdf.ln(10)
    pdf.doc_title("Prompterly Security & Data")
    pdf.doc_title("Architecture Standard")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Version 2.0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Last Updated: April 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Next Review: October 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5.5,
        "This document outlines the minimum security, privacy, backup, and data protection "
        "requirements for the Prompterly platform before public launch. The goal is to protect "
        "user data, mentor intellectual property, and platform operations while complying with "
        "applicable privacy laws and industry best practices. This document applies to:")
    pdf.ln(2)
    pdf.bullet("Platform infrastructure")
    pdf.bullet("User data")
    pdf.bullet("Mentor content")
    pdf.bullet("AI coaching lounge interactions")
    pdf.bullet("Payment processing through Stripe")
    pdf.bullet("Third-party data processors and sub-processors")
    pdf.ln(2)

    pdf.set_font("Helvetica", "BU", 10)
    pdf.cell(8, 5, "Note:")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5,
        " Prompterly is a platform that will store deeply personal reflections. It is "
        "expected that users will treat the coaching lounge like a journal. That creates a "
        "psychological trust obligation, even if the law doesn't strictly require it. "
        "Therefore, the goal should be security posture closer to a journaling app than a "
        "simple chatbot.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "BU", 10)
    pdf.cell(0, 5, "Document Control:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "  Owner: Prompterly Compliance / Engineering Team", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "  Review Cadence: Annual or upon major regulatory change", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "  Distribution: Internal (engineering, mentors, admin staff)", new_x="LMARGIN", new_y="NEXT")

    # ===== Section 1: Data Categories =====
    pdf.section("1", "Data Categories Stored on Prompterly")
    pdf.para("Prompterly stores several categories of information which must be protected appropriately.")

    pdf.heading("User data")
    pdf.bullet("Name")
    pdf.bullet("Email address")
    pdf.bullet("Account settings")
    pdf.bullet("Notification preferences")
    pdf.bullet("Language and timezone preferences")

    pdf.heading("User generated content")
    pdf.bullet("Coaching lounge chat messages")
    pdf.bullet("Notebook entries")
    pdf.bullet("Time capsule entries")

    pdf.heading("Platform data")
    pdf.bullet("Subscription records")
    pdf.bullet("Usage logs")
    pdf.bullet("Session tokens")
    pdf.bullet("System diagnostics")
    pdf.bullet("Audit logs")

    pdf.heading("Mentor data")
    pdf.bullet("Onboarding framework materials and IP")
    pdf.bullet("Coaching lounge configuration")
    pdf.bullet("Mentor profile information")
    pdf.bullet("Mentor framework version history")

    pdf.heading("Payment data")
    pdf.bullet("Stripe subscription identifiers")
    pdf.bullet("Payment status records")
    pdf.para("Prompterly does not store full credit card details, which are handled entirely by Stripe.")

    # ===== Section 2: Data Separation =====
    pdf.section("2", "Data Separation & Pseudonymisation Architecture")
    pdf.para("Prompterly must store user identity information separately from user-generated content.")
    pdf.para("This architecture reduces the risk of unnecessary exposure of sensitive conversations and "
             "aligns with privacy-by-design principles.")

    pdf.heading("Core Principle")
    pdf.para("User conversations and personal reflections should not be directly linked to identifiable "
             "personal information in the same database structures. Instead, content must be associated "
             "with an internal pseudonymous identifier.")

    pdf.heading("Implementation Note")
    pdf.para("This architecture does not require multiple physical databases. Logical separation within "
             "the schema is acceptable provided:")
    pdf.bullet("Identity fields are stored in dedicated tables")
    pdf.bullet("Conversation and content tables reference user_uuid only")
    pdf.bullet("Personal identifiers are not duplicated across content tables")

    pdf.subsection("2.1", "Internal User Identifier")
    pdf.para("Each user account must be assigned a unique internal identifier.")
    pdf.code_box("user_uuid")
    pdf.para("This identifier will be used as the primary reference key across platform systems. "
             "The internal identifier must not contain personal information.")

    pdf.subsection("2.2", "Separation of Identity Data and Content Data")
    pdf.para("Prompterly must store data across separate logical domains.")

    pdf.heading("Identity Data (Personally Identifiable Information)")
    pdf.bullet("Name")
    pdf.bullet("Email address")
    pdf.bullet("Authentication credentials")
    pdf.bullet("Stripe customer ID")
    pdf.bullet("Account preferences")
    pdf.bullet("Notification settings")
    pdf.para("This data should be stored in the User Identity table or equivalent service.")

    pdf.heading("User Generated Content")
    pdf.para("The following data must reference user_uuid only, not personal identifiers.")
    pdf.bullet("Chat messages")
    pdf.bullet("Chat threads")
    pdf.bullet("Notebook entries")
    pdf.bullet("Time capsule entries")
    pdf.bullet("AI coaching lounge interaction records")
    pdf.para("These tables must not contain name, email, or other identifying fields.")

    pdf.subsection("2.3", "Mapping Between Identity and Content")
    pdf.para("A mapping relationship must exist between:")
    pdf.code_box("user_uuid -> identity record")
    pdf.para("This mapping must be stored in the identity layer and should not be duplicated across other tables.")
    pdf.para("Access to this mapping should be restricted to only the services that require it for legitimate "
             "platform functions.")

    pdf.subsection("2.4", "Access Restrictions")
    pdf.para("Not all services or administrators should be able to directly associate user conversations with "
             "identity information. Administrative tools capable of linking identity data with conversation "
             "data must be restricted to authorised personnel only and protected with multi-factor authentication.")
    pdf.para("Best practice is that:")
    pdf.bullet("Standard application services operate using user_uuid")
    pdf.bullet("Identity lookup is performed only when necessary (e.g. login, account management)")
    pdf.para("Where possible:")
    pdf.bullet("Developer debugging tools should operate on pseudonymous identifiers")
    pdf.bullet("Logs should avoid storing personal identifiers alongside conversation data")

    pdf.subsection("2.5", "Logging and Monitoring Considerations")
    pdf.para("System logs must avoid storing sensitive conversation content or unnecessary personal identifiers.")
    pdf.para("Logs may include:")
    pdf.bullet("user_uuid")
    pdf.bullet("timestamps")
    pdf.bullet("request metadata")
    pdf.para("Logs should not include full conversation text unless required for debugging or safety monitoring.")

    pdf.subsection("2.6", "Data Export and User Access")
    pdf.para("When users request to export their data, the system may temporarily reconstruct the relationship between:")
    pdf.bullet("identity data")
    pdf.bullet("conversation data")
    pdf.para("Exports must include:")
    pdf.bullet("chat history")
    pdf.bullet("notebook entries")
    pdf.bullet("time capsule entries")
    pdf.para("Export formats must include JSON, CSV, and PDF.")

    pdf.subsection("2.7", "Data Deletion")
    pdf.para("When a user deletes a conversation thread, notebook entry, or time capsule entry:")
    pdf.bullet("The content should be removed from the content tables associated with their user_uuid.")
    pdf.para("When a user deletes their account:")
    pdf.bullet("Personal identity information should be anonymised")
    pdf.bullet("Authentication credentials revoked")
    pdf.bullet("Content records remain pseudonymous unless administratively deleted")

    pdf.subsection("2.8", "Benefits of This Architecture")
    pdf.para("This design provides several important protections:")
    pdf.bullet("Reduces unnecessary exposure of personal identity in content systems")
    pdf.bullet("Limits the number of systems that can link identity to conversations")
    pdf.bullet("Supports privacy-by-design principles")
    pdf.bullet("Reduces the impact of accidental data exposure")
    pdf.para("This architecture does not eliminate legal disclosure obligations, but it ensures that access "
             "to identifiable user data is appropriately controlled.")

    # ===== Section 3: Encryption =====
    pdf.section("3", "Encryption Standards")
    pdf.para("All user data must be protected using encryption both when stored and when transmitted. "
             "All production databases must not be publicly accessible on the internet and must be "
             "restricted to application servers via private network rules. Production databases must "
             "only accept connections from authorised application servers through private network rules "
             "or security groups.")

    pdf.heading("Encryption In Transit")
    pdf.para("All traffic between users and the Prompterly platform must be encrypted using HTTPS with "
             "TLS 1.2 or higher. HTTP connections must automatically redirect to HTTPS. TLS certificates "
             "must be valid and configured to prevent insecure fallback connections.")

    pdf.heading("Encryption At Rest")
    pdf.para("The following systems must use encryption at rest:")
    pdf.bullet("Platform database (MySQL or equivalent)")
    pdf.bullet("Object storage (S3 or equivalent)")
    pdf.bullet("Backup storage systems")
    pdf.para("Industry standard AES-256 encryption (or equivalent cloud-provider managed encryption) "
             "should be used where available.")
    pdf.para("The mapping between user identity and user_uuid must be protected using the same encryption "
             "and access controls applied to other sensitive personal data.")

    pdf.heading("Sensitive Content Encryption")
    pdf.para("Prompterly must apply application-level encryption to highly sensitive user-generated content. "
             "The following fields must be encrypted before storage:")
    pdf.bullet("Chat message content")
    pdf.bullet("Notebook entry text")
    pdf.bullet("Time capsule entry content")
    pdf.para("Encryption must occur before the data is written to the database.")
    pdf.para("Encryption keys must be managed through a secure key management service (e.g., AWS KMS or "
             "equivalent) and must not be stored directly in the application database.")
    pdf.para("Decryption should occur only within the application layer when rendering user content to "
             "the authenticated user.")

    pdf.heading("Search requirements")
    pdf.para("Prompterly must preserve the user's ability to search within the current chat thread.")
    pdf.para("If chat message content is encrypted at the application layer, developers must implement a "
             "search method that allows thread-level search without exposing full plaintext content unnecessarily.")
    pdf.para("This may be achieved by:")
    pdf.bullet("Decrypting the current thread in the application layer for search, or")
    pdf.bullet("Maintaining a separate search index that does not store full message content in plain text")

    # ===== Section 4: Password & Authentication =====
    pdf.section("4", "Password & Authentication Security")
    pdf.para("Passwords must never be stored in plain text. Passwords must be stored using strong hashing "
             "methods such as bcrypt.")
    pdf.para("Authentication tokens must:")
    pdf.bullet("Have a defined expiration time appropriate to the application session (e.g., hours rather than months)")
    pdf.bullet("Be securely stored")
    pdf.bullet("Be transmitted only over encrypted connections")
    pdf.bullet("Be invalidated upon user logout where possible")
    pdf.para("Administrative access must require:")
    pdf.bullet("Role-based permissions")
    pdf.bullet("Multi-factor authentication (MANDATORY for all admin accounts)")

    pdf.heading("Login & API Rate Limiting")
    pdf.para("Authentication endpoints and sensitive API routes must implement rate limiting to prevent "
             "automated abuse.")
    pdf.para("Minimum expectations:")
    pdf.bullet("Limit repeated login attempts from the same IP address")
    pdf.bullet("Temporarily block excessive failed login attempts")
    pdf.bullet("Apply rate limiting to authentication and account recovery endpoints")
    pdf.bullet("Per-account lockout after 5 failed attempts (15-minute cooldown)")
    pdf.bullet("Notify the user via email when their account is locked")

    pdf.heading("Two-Factor Authentication (2FA) - NEW")
    pdf.para("Prompterly must offer 2FA for all users:")
    pdf.bullet("Email OTP (default method - sends 6-digit code to user's email)")
    pdf.bullet("Authenticator app (TOTP) as an optional alternative for advanced users")
    pdf.bullet("MANDATORY for all admin and mentor accounts")
    pdf.bullet("Cannot be disabled by the user once enforced for admin/mentor roles")

    pdf.heading("Account Recovery - NEW")
    pdf.para("If a user loses access to their MFA device or cannot receive emails:")
    pdf.bullet("Account recovery must be available via verified support process")
    pdf.bullet("Identity verification required before recovery (e.g., security questions, ID verification)")
    pdf.bullet("Recovery actions must be logged in the audit trail")
    pdf.bullet("User must be notified via all known contact methods when recovery is initiated")

    # ===== Section 5: Secrets =====
    pdf.section("5", "Secrets & Credential Management")
    pdf.para("Sensitive credentials must not be hardcoded in application code.")
    pdf.para("This includes:")
    pdf.bullet("Database credentials")
    pdf.bullet("API keys")
    pdf.bullet("Stripe secret keys")
    pdf.bullet("Email service credentials")
    pdf.bullet("AI provider keys")
    pdf.bullet("Encryption keys")
    pdf.para("Secrets must be stored using a secure secret management system such as:")
    pdf.bullet("AWS Secrets Manager")
    pdf.bullet("AWS Parameter Store")
    pdf.bullet("Hashicorp Vault")
    pdf.bullet("Or an equivalent managed secret storage")
    pdf.para("Access to secrets must be restricted to only the services that require them.")

    # ===== Section 6: Backups =====
    pdf.section("6", "Data Backups & Disaster Recovery")
    pdf.para("Prompterly must maintain reliable backup and recovery procedures.")

    pdf.heading("Database Backups")
    pdf.para("Automated backups of the primary database must occur at least once per day. Backups must be:")
    pdf.bullet("Stored separately from the primary server")
    pdf.bullet("Encrypted at rest using the same encryption standard applied to the primary database (AES-256 or equivalent)")
    pdf.bullet("Stored in secure cloud storage (e.g., encrypted S3 bucket or equivalent)")
    pdf.para("If backups are stored in cloud object storage, server-side encryption must be enabled.")

    pdf.heading("Backup Retention")
    pdf.para("Recommended retention periods:")
    pdf.bullet("Daily backups: 30 days")
    pdf.bullet("Monthly backups: 12 months")

    pdf.heading("Restore Capability")
    pdf.para("The system must support restoration of database backups in the event of:")
    pdf.bullet("Infrastructure failure")
    pdf.bullet("Accidental deletion")
    pdf.bullet("Security incident")
    pdf.para("Bitsclan / developers must test restoration procedures periodically (at least quarterly) "
             "to confirm backups are functional.")

    pdf.heading("Recovery Objectives - NEW")
    pdf.bullet("Recovery Time Objective (RTO): 4 hours maximum downtime")
    pdf.bullet("Recovery Point Objective (RPO): 24 hours maximum data loss (matches daily backup cadence)")
    pdf.bullet("Service uptime target: 99.5%")

    # ===== Section 7: Data Retention =====
    pdf.section("7", "Data Retention Policy")
    pdf.para("Prompterly defines the following timeframes for how long different categories of data are stored:")
    pdf.bullet("Chat Messages - Indefinite: Retained until the user deletes the associated conversation thread")
    pdf.bullet("Notebook Entries - Indefinite: Retained until the user deletes the entry")
    pdf.bullet("Time Capsule Entries - Indefinite: Retained until the user deletes the entry")
    pdf.bullet("System Logs - 60 days, then automatically rotated and deleted unless required for investigation or legal preservation")
    pdf.bullet("Audit Logs - At least 12 months")
    pdf.bullet("Backups - Daily backups: 30 days, monthly backups: 12 months")

    pdf.heading("Log Rotation")
    pdf.para("Operational logs must implement automatic log rotation. Minimum requirements:")
    pdf.bullet("Logs must rotate daily or by size threshold")
    pdf.bullet("Rotated logs must be retained for 60 days")
    pdf.bullet("Older logs must be automatically deleted unless preserved under legal hold")

    pdf.heading("Legal Retention Override - NEW")
    pdf.para("Where Australian or applicable law requires longer retention (e.g. tax records: 5 years per "
             "ATO requirements; payment records: 7 years), legal retention requirements override the policy "
             "above. The longer of the two periods applies.")

    pdf.heading("Account Deletion")
    pdf.para("When a user deletes their account:")
    pdf.bullet("Direct identifiers (name, email, Stripe ID) must be removed or irreversibly anonymised")
    pdf.bullet("Authentication credentials must be revoked")
    pdf.bullet("Content records remain associated only with the internal user_uuid unless administratively deleted")
    pdf.bullet("A confirmation email must be sent to the user before deletion is finalised")
    pdf.bullet("A 30-day cooling off period applies (user can cancel deletion within this window)")

    # ===== Section 8: Legal Hold =====
    pdf.section("8", "Legal Preservation (Legal Hold)")
    pdf.para("Prompterly must maintain the ability to temporarily preserve account data when required.")
    pdf.para("If a legal request or investigation occurs, the platform must be able to:")
    pdf.bullet("Temporarily disable deletion of account data")
    pdf.bullet("Preserve relevant records for legal review")
    pdf.bullet("Document the reason and authorising party for the hold")
    pdf.bullet("Notify affected users where legally permitted")
    pdf.para("This capability should be controlled through an internal administrative mechanism.")

    # ===== Section 9: Audit Logging =====
    pdf.section("9", "Audit Logging")
    pdf.para("Prompterly must maintain logs of critical platform actions.")
    pdf.para("The system should record:")
    pdf.bullet("Account creation and deletion")
    pdf.bullet("Administrative actions")
    pdf.bullet("Data deletion requests")
    pdf.bullet("Subscription changes")
    pdf.bullet("Security-related events")
    pdf.bullet("Consent changes (opt-in/opt-out)")
    pdf.bullet("Permission and role changes")
    pdf.bullet("Data exports")
    pdf.bullet("Legal hold actions")
    pdf.bullet("Mentor framework version changes")
    pdf.para("Audit logs must be stored separately from standard application logs where possible.")
    pdf.para("Audit logs must be tamper-evident (e.g., append-only or cryptographically signed) where feasible.")

    # ===== Section 10: User Data Export =====
    pdf.section("10", "User Data Export")
    pdf.para("Users must have the ability to export their data upon request.")
    pdf.para("Exportable data may include:")
    pdf.bullet("Chat conversation history")
    pdf.bullet("Notebook entries")
    pdf.bullet("Time capsule entries")
    pdf.bullet("Profile information")
    pdf.bullet("Subscription and billing history")
    pdf.para("Exports must be provided in formats such as:")
    pdf.bullet("JSON")
    pdf.bullet("CSV")
    pdf.bullet("PDF (human-readable)")
    pdf.para("Export features should avoid including mentor branding where the lounge has been removed due "
             "to safety or legal concerns.")

    pdf.heading("Response Timeframes - NEW")
    pdf.bullet("GDPR Subject Access Requests: 30 days from verified request")
    pdf.bullet("CCPA Consumer Requests: 45 days (extendable by 45 days with notice)")
    pdf.bullet("Australian Privacy Act access requests: 30 days")
    pdf.bullet("Identity verification required before fulfilling requests")
    pdf.bullet("First request per user is free of charge")

    # ===== Section 11: Payment Processing =====
    pdf.section("11", "Payment Processing (Stripe)")
    pdf.para("Prompterly uses Stripe for payment processing.")

    pdf.heading("Stripe Responsibilities")
    pdf.para("Stripe securely handles:")
    pdf.bullet("Credit card storage")
    pdf.bullet("Payment authorisation")
    pdf.bullet("Payment processing")
    pdf.para("Prompterly must never store raw credit card numbers.")

    pdf.heading("Prompterly Responsibilities")
    pdf.para("Prompterly stores limited Stripe-related records such as:")
    pdf.bullet("Stripe customer ID")
    pdf.bullet("Subscription ID")
    pdf.bullet("Payment status")
    pdf.para("These identifiers must be stored securely within the platform database.")

    pdf.heading("Stripe Webhooks")
    pdf.para("Stripe webhook endpoints must:")
    pdf.bullet("Validate webhook signatures")
    pdf.bullet("Reject requests without valid signatures")
    pdf.bullet("Enforce timestamp tolerance to prevent replay attacks")

    # ===== Section 12: Age Requirements =====
    pdf.section("12", "Minimum Age Requirements")
    pdf.para("Prompterly is intended for users aged 18 years or older. Account creation must require users to confirm:")
    pdf.code_box('"I confirm that I am at least 18 years of age or older"')

    pdf.heading("Underage Account Discovery - NEW")
    pdf.para("If Prompterly discovers a user is under 18:")
    pdf.bullet("The account must be immediately suspended")
    pdf.bullet("All personal data must be deleted within 30 days")
    pdf.bullet("Parents/guardians may be notified where appropriate and lawful")
    pdf.bullet("A reporting mechanism must exist for users to flag suspected underage accounts")

    # ===== Section 13: Security Monitoring & Incident Response =====
    pdf.section("13", "Security Monitoring & Incident Response")
    pdf.para("Prompterly must maintain procedures for responding to security incidents. If a data breach "
             "or security incident occurs, Prompterly must:")
    pdf.bullet("Investigate the issue promptly")
    pdf.bullet("Secure affected systems")
    pdf.bullet("Notify affected users where legally required")
    pdf.bullet("Document the incident in the breach log")
    pdf.bullet("Conduct a root cause analysis")
    pdf.bullet("Apply remediation and preventive measures")

    pdf.heading("Notifiable Data Breaches (NDB) Scheme - NEW")
    pdf.para("Prompterly is subject to Australia's Notifiable Data Breaches (NDB) scheme under the Privacy "
             "Act 1988. If a data breach is likely to result in serious harm to affected individuals, "
             "Prompterly must:")
    pdf.bullet("Assess the breach within 30 days of becoming aware")
    pdf.bullet("Notify the Office of the Australian Information Commissioner (OAIC) as soon as practicable")
    pdf.bullet("Notify affected individuals as soon as practicable")
    pdf.bullet("Provide the OAIC and users with details: what happened, what data was affected, recommended actions")
    pdf.bullet("Maintain a breach log with date, scope, severity, response actions, and outcomes")

    pdf.heading("Breach Notification Content")
    pdf.para("Notifications to affected users must include:")
    pdf.bullet("Description of what happened (in plain language)")
    pdf.bullet("Type of personal information involved")
    pdf.bullet("Recommended steps the user should take (e.g., change password)")
    pdf.bullet("Contact information for support")
    pdf.bullet("Reference number for the incident")

    pdf.heading("Detection & Monitoring")
    pdf.bullet("Anomaly detection on authentication and admin actions")
    pdf.bullet("Failed login monitoring with alerting")
    pdf.bullet("Regular review of audit logs")
    pdf.bullet("Vulnerability scanning of dependencies (npm, pip)")

    # ===== Section 14: AI System Data Boundaries =====
    pdf.section("14", "AI System Data Boundaries")
    pdf.para("Prompterly's AI coaching lounges generate responses using:")
    pdf.bullet("Mentor-provided frameworks")
    pdf.bullet("User prompts")
    pdf.bullet("System guardrails")
    pdf.para("User conversations must not be used to train public AI models.")
    pdf.para("AI responses are generated in real time and are not intended to replace professional services "
             "such as therapy, legal advice, or medical advice.")

    pdf.heading("AI Disclosure Requirements - NEW")
    pdf.para("Under the Australian Consumer Law and AI Ethics Framework:")
    pdf.bullet("Users must be clearly informed they are interacting with an AI, not a human")
    pdf.bullet("This disclosure must appear on first interaction with each coaching lounge")
    pdf.bullet("AI personas must not be presented in a way that misleads users into believing they are human")

    pdf.heading("AI Safety Disclaimers")
    pdf.para("The following disclaimer must be visible to users:")
    pdf.code_box('"This is an AI coaching assistant, not a licensed professional."')
    pdf.code_box('"Do not use this service for medical, legal, or financial advice."')
    pdf.code_box('"In a crisis, contact emergency services or a qualified practitioner."')

    pdf.heading("Crisis Intervention Protocol - NEW")
    pdf.para("Because Prompterly stores deeply personal reflections, the system must implement basic safety "
             "mechanisms for users in crisis:")
    pdf.bullet("Detect keywords or phrases related to self-harm, suicide, abuse, or imminent danger")
    pdf.bullet("Display a crisis support message overriding the normal AI response")
    pdf.bullet("Provide region-appropriate emergency contact information")
    pdf.bullet("Australia: Lifeline 13 11 14, Beyond Blue 1300 22 4636, 000 for emergencies")
    pdf.bullet("UK: Samaritans 116 123, 999 for emergencies")
    pdf.bullet("USA: 988 Suicide & Crisis Lifeline, 911 for emergencies")
    pdf.bullet("Log the event (without exposing the user's content) for safety review")
    pdf.bullet("Never provide medical, psychological, or therapeutic advice in response to crisis content")

    # ===== Section 15: Mentor Framework Versioning =====
    pdf.section("15", "Mentor Framework / IP Versioning")
    pdf.para("Prompterly must maintain versioned configuration records for each Coaching Lounge framework "
             "and AI system instruction set.")
    pdf.para("Configuration includes, but is not limited to:")
    pdf.bullet("Mentor frameworks")
    pdf.bullet("Prompt templates")
    pdf.bullet("AI system instructions")
    pdf.bullet("Behavioural guardrails")
    pdf.bullet("Tone or persona configuration")
    pdf.para("When a mentor or administrator modifies any of the above, the system must:")
    pdf.bullet("Create a new configuration version")
    pdf.bullet("Preserve all previous versions unchanged (versions must be immutable)")
    pdf.para("Existing configuration versions must not be overwritten.")
    pdf.para("Each chat session must record the configuration version used to generate responses so that "
             "past interactions can be reconstructed if required.")
    pdf.para("The platform must support rollback to a previous configuration version if a configuration update "
             "produces unintended behaviour. Rollback must not modify or delete historical versions.")

    pdf.heading("Mentor IP Ownership - NEW")
    pdf.para("Prompterly must clearly define ownership of mentor-provided frameworks:")
    pdf.bullet("Mentors retain ownership of their original framework IP")
    pdf.bullet("Prompterly receives a licence to use the framework for the duration of the mentor's agreement")
    pdf.bullet("If a mentor leaves the platform, their frameworks must be archived (not deleted) for a defined period")
    pdf.bullet("Mentors must be able to export their own framework configurations on request")
    pdf.bullet("Confidentiality of mentor-provided training data must be maintained")

    # ===== Section 16: Data Protection Compliance =====
    pdf.section("16", "Data Protection Compliance")
    pdf.para("Prompterly will operate globally and must comply with relevant privacy frameworks including:")
    pdf.bullet("Australian Privacy Act 1988 (APPs)")
    pdf.bullet("Australian Notifiable Data Breaches (NDB) Scheme")
    pdf.bullet("GDPR (European Union)")
    pdf.bullet("CCPA/CPRA (California)")
    pdf.bullet("UK GDPR")
    pdf.bullet("New Zealand Privacy Act 2020")
    pdf.bullet("Canada PIPEDA")
    pdf.para("Prompterly's privacy policy must clearly disclose:")
    pdf.bullet("What data is collected")
    pdf.bullet("How it is used")
    pdf.bullet("How long it is retained")
    pdf.bullet("How users may request deletion or export")
    pdf.bullet("Who data is shared with (third parties)")
    pdf.bullet("Cross-border data transfers")
    pdf.bullet("User rights and how to exercise them")

    pdf.heading("Privacy Policy Versioning - NEW")
    pdf.bullet("The privacy policy must include a 'last updated' date")
    pdf.bullet("Policy versions must be tracked")
    pdf.bullet("Users must be re-prompted to accept the policy when material changes occur")
    pdf.bullet("Records of which version each user accepted must be retained")

    # ===== Section 17: Consent Management - NEW =====
    pdf.section("17", "Consent Management (NEW)")
    pdf.para("Prompterly must implement granular and revocable consent mechanisms.")

    pdf.heading("Consent Collection")
    pdf.bullet("Explicit opt-in at signup for privacy policy and terms of service")
    pdf.bullet("Separate consent for marketing communications (not pre-checked)")
    pdf.bullet("Separate consent for analytics and tracking (where applicable)")
    pdf.bullet("Age confirmation (18+) explicit consent required")
    pdf.bullet("All consent must be timestamped and recorded in the audit trail")

    pdf.heading("Consent Withdrawal")
    pdf.bullet("Users must be able to withdraw consent at any time from account settings")
    pdf.bullet("Withdrawing consent must not require contacting support")
    pdf.bullet("Withdrawal must take effect within 24 hours")
    pdf.bullet("Users must be informed of consequences (e.g., account closure if essential consent withdrawn)")

    pdf.heading("Re-consent")
    pdf.para("When privacy policy or terms of service are materially updated:")
    pdf.bullet("Users must be prompted to accept the new version on next login")
    pdf.bullet("Continued use without acceptance is not permitted for material changes")
    pdf.bullet("The version number and acceptance timestamp must be recorded")

    # ===== Section 18: Third-Party Processors - NEW =====
    pdf.section("18", "Third-Party Processors & Cross-Border Transfers (NEW)")
    pdf.para("Prompterly uses third-party services that process user data. Under Australian Privacy Principle 8 "
             "and GDPR Article 28, these relationships must be disclosed and governed by formal agreements.")

    pdf.heading("Current Sub-Processors")
    pdf.bullet("Anthropic (Claude AI) - USA - processes chat content for AI responses")
    pdf.bullet("Amazon Web Services - hosts database, file storage, backups")
    pdf.bullet("Stripe - USA - payment processing")
    pdf.bullet("Postmark - USA - transactional email delivery")
    pdf.bullet("Sentry (if used) - error monitoring")

    pdf.heading("Vendor Requirements")
    pdf.para("All sub-processors must:")
    pdf.bullet("Have a signed Data Processing Agreement (DPA)")
    pdf.bullet("Demonstrate equivalent or stronger privacy protections")
    pdf.bullet("Be listed in Prompterly's privacy policy")
    pdf.bullet("Provide breach notification within their own SLAs")
    pdf.bullet("Support sub-processor change notifications to Prompterly")

    pdf.heading("Cross-Border Disclosure")
    pdf.para("Prompterly must disclose:")
    pdf.bullet("Which countries user data is transferred to")
    pdf.bullet("What categories of data are transferred")
    pdf.bullet("That overseas recipients may not be subject to Australian privacy law")
    pdf.bullet("Any safeguards in place (Standard Contractual Clauses, adequacy decisions, etc.)")
    pdf.para("Users must consent to cross-border transfers as part of accepting the privacy policy.")

    # ===== Section 19: Privacy by Design - NEW =====
    pdf.section("19", "Privacy by Design (NEW)")
    pdf.para("Prompterly adopts a Privacy by Design approach as required under GDPR Article 25 and "
             "recommended by the OAIC.")

    pdf.heading("Core Principles")
    pdf.bullet("Proactive, not reactive - anticipate privacy risks before they occur")
    pdf.bullet("Privacy as the default setting - users should not have to opt in to protection")
    pdf.bullet("Privacy embedded into design - not bolted on after the fact")
    pdf.bullet("Full functionality - privacy and usability are not mutually exclusive")
    pdf.bullet("End-to-end security - data protected throughout its lifecycle")
    pdf.bullet("Visibility and transparency - users can verify privacy practices")
    pdf.bullet("Respect for user privacy - keep user interests paramount")

    pdf.heading("Implementation Requirements")
    pdf.bullet("Privacy review required for all new features")
    pdf.bullet("Data Protection Impact Assessment (DPIA) for high-risk processing")
    pdf.bullet("Default settings must minimise data collection")
    pdf.bullet("Privacy-friendly defaults (e.g., notification preferences off by default for marketing)")
    pdf.bullet("Documentation of data flows for each feature")

    # ===== Section 20: Cookie Policy - NEW =====
    pdf.section("20", "Cookie Policy (NEW)")
    pdf.para("Where Prompterly uses cookies, web storage, or similar tracking technologies:")

    pdf.heading("Cookie Categories")
    pdf.bullet("Essential cookies - required for the platform to function (session, authentication)")
    pdf.bullet("Analytics cookies - measure usage patterns")
    pdf.bullet("Marketing cookies - track for advertising purposes")

    pdf.heading("Consent Requirements")
    pdf.bullet("Cookie consent banner displayed on first visit (especially for EU users under GDPR)")
    pdf.bullet("Granular controls - users can accept/reject categories independently")
    pdf.bullet("Essential cookies do not require consent but must be disclosed")
    pdf.bullet("Cookie preferences can be changed at any time from settings")
    pdf.bullet("Cookie policy must list all cookies, their purpose, and duration")

    # ===== Section 21: Operational Security - NEW =====
    pdf.section("21", "Operational Security (NEW)")
    pdf.para("Beyond technical controls, Prompterly must maintain operational security practices.")

    pdf.heading("Staff Access Controls")
    pdf.bullet("Principle of least privilege - staff only have access to what they need")
    pdf.bullet("All production access logged and audited")
    pdf.bullet("Off-boarding process: revoke access immediately when staff leave")
    pdf.bullet("Quarterly access review")
    pdf.bullet("Background checks for staff with access to sensitive data")

    pdf.heading("Security Testing")
    pdf.bullet("Annual penetration test by qualified third party")
    pdf.bullet("Quarterly automated vulnerability scans")
    pdf.bullet("Dependency vulnerability scanning (npm audit, pip-audit) on every build")
    pdf.bullet("Security patching within 30 days of patch availability (critical patches within 7 days)")

    pdf.heading("Training & Awareness")
    pdf.bullet("Annual privacy and security training for all staff")
    pdf.bullet("Onboarding training for new staff includes data protection")
    pdf.bullet("Customer support trained on privacy requests and breach handling")
    pdf.bullet("Incident response drills conducted at least annually")

    pdf.heading("Documentation")
    pdf.bullet("All security policies documented and accessible to staff")
    pdf.bullet("Records of Processing Activities (ROPA) maintained")
    pdf.bullet("Data flow diagrams for major features")
    pdf.bullet("Incident response runbook")
    pdf.bullet("Recovery procedures runbook")

    # ===== Section 22: Service Availability - NEW =====
    pdf.section("22", "Service Availability & SLAs (NEW)")
    pdf.heading("Uptime Targets")
    pdf.bullet("Service uptime target: 99.5% (excluding planned maintenance)")
    pdf.bullet("Planned maintenance windows: outside peak hours, with 48-hour notice")
    pdf.bullet("Status page available for users to check incidents")

    pdf.heading("Recovery Objectives")
    pdf.bullet("Recovery Time Objective (RTO): 4 hours maximum downtime in disaster scenarios")
    pdf.bullet("Recovery Point Objective (RPO): 24 hours maximum data loss")
    pdf.bullet("Failover procedures documented and tested annually")

    # ===== Section 23: Document Control - NEW =====
    pdf.section("23", "Document Control & Review (NEW)")
    pdf.heading("Version History")
    pdf.bullet("Version 1.0 - Initial standard")
    pdf.bullet("Version 2.0 - April 2026 - Added sections on consent management, third-party processors, "
              "AI safety, crisis intervention, breach notification specifics, privacy by design, cookies, "
              "operational security, SLAs, and document control")

    pdf.heading("Review Cadence")
    pdf.bullet("Annual review (next: October 2026)")
    pdf.bullet("Ad-hoc review upon major regulatory changes (e.g., new privacy law)")
    pdf.bullet("Ad-hoc review after any significant security incident")
    pdf.bullet("Updates require sign-off from compliance and engineering leads")

    pdf.heading("Distribution")
    pdf.bullet("Internal: all staff, contractors, mentors with platform access")
    pdf.bullet("External: shared with auditors, legal, and key partners under NDA")

    pdf.heading("Compliance Owner")
    pdf.bullet("Primary owner: Prompterly Compliance Officer (to be designated)")
    pdf.bullet("Technical owner: Engineering Lead (Bitsclan)")
    pdf.bullet("Business owner: Lauren Donnelly")

    output = "/home/wajid-ali/Projects/Prompterly/RESTAPI/RESTAPI-Prompterly/Prompterly_Security_and_Data_Architecture_Standard_v2.pdf"
    pdf.output(output)
    print(f"Generated: {output}")


if __name__ == "__main__":
    build()
