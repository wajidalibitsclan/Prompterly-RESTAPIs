"""
Professional email templates for Prompterly
Consistent branding with landing page design
"""
from typing import Optional


# Prompterly Brand Colors
BRAND_COLORS = {
    "primary": "#1A1A1F",        # Dark text/logo color
    "accent": "#F3FDC1",         # Yellow accent
    "success": "#10b981",        # Green for success actions
    "warning": "#f59e0b",        # Amber for warnings
    "error": "#dc2626",          # Red for errors
    "background": "#ffffff",     # White background
    "surface": "#f9fafb",        # Light gray surface
    "border": "#e5e7eb",         # Border color
    "text_primary": "#1f2937",   # Primary text
    "text_secondary": "#6b7280", # Secondary text
    "text_muted": "#9ca3af",     # Muted text
}


def get_base_template(
    content: str,
    preview_text: str = "",
    show_footer_links: bool = True
) -> str:
    """
    Base email template with Prompterly branding

    Args:
        content: Main email content HTML
        preview_text: Email preview text (shown in inbox)
        show_footer_links: Whether to show social/website links

    Returns:
        Complete HTML email
    """
    footer_links = ""
    if show_footer_links:
        footer_links = f"""
        <tr>
            <td style="padding: 0 0 20px 0; text-align: center;">
                <a href="https://prompterly.ai"
                   style="color: {BRAND_COLORS['text_secondary']}; text-decoration: none; margin: 0 10px; font-size: 13px;">
                    Website
                </a>
                <span style="color: {BRAND_COLORS['border']};">|</span>
                <a href="https://prompterly.ai/about"
                   style="color: {BRAND_COLORS['text_secondary']}; text-decoration: none; margin: 0 10px; font-size: 13px;">
                    About Us
                </a>
                <span style="color: {BRAND_COLORS['border']};">|</span>
                <a href="https://prompterly.ai/contact"
                   style="color: {BRAND_COLORS['text_secondary']}; text-decoration: none; margin: 0 10px; font-size: 13px;">
                    Contact
                </a>
            </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Prompterly</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: {BRAND_COLORS['surface']}; font-family: 'Inter', 'Segoe UI', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <!-- Preview Text -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preview_text}
    </div>

    <!-- Email Container -->
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: {BRAND_COLORS['surface']};">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto;">

                    <!-- Logo Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 30px;">
                            <img src="https://prompterly.bitsclan.us/images/black-logo.png"
                                 alt="Prompterly"
                                 width="180"
                                 style="display: inline-block; max-width: 180px; height: auto;">
                        </td>
                    </tr>

                    <!-- Main Content Card -->
                    <tr>
                        <td>
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                                   style="background-color: {BRAND_COLORS['background']}; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                                <tr>
                                    <td style="padding: 40px;">
                                        {content}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding-top: 30px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                {footer_links}
                                <tr>
                                    <td style="text-align: center; padding: 10px 0;">
                                        <p style="margin: 0; font-size: 12px; color: {BRAND_COLORS['text_muted']};">
                                            &copy; 2025 Prompterly. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align: center; padding: 5px 0;">
                                        <p style="margin: 0; font-size: 11px; color: {BRAND_COLORS['text_muted']};">
                                            You're receiving this email because you signed up for Prompterly.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_otp_email_template(name: str, otp: str) -> tuple[str, str]:
    """
    Generate OTP verification email

    Args:
        name: User's name
        otp: 6-digit OTP code

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Welcome to Prompterly! To complete your registration, please use the verification code below:

Your verification code: {otp}

This code will expire in 10 minutes.

If you didn't create an account with Prompterly, you can safely ignore this email.

Need help? Contact us at support@prompterly.ai

Best regards,
The Prompterly Team
"""

    content = f"""
<!-- Greeting -->
<h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    Verify Your Email
</h1>
<p style="margin: 0 0 25px 0; font-size: 16px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.6;">
    Hi {name}, welcome to Prompterly!
</p>

<!-- Message -->
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    To complete your registration, please enter the following verification code:
</p>

<!-- OTP Code Box -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 25px 0;">
            <div style="display: inline-block; background: linear-gradient(135deg, {BRAND_COLORS['accent']} 0%, #e8f5c8 100%);
                        padding: 20px 40px; border-radius: 12px; border: 2px dashed {BRAND_COLORS['primary']};">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 12px; color: {BRAND_COLORS['primary']};
                             font-family: 'Monaco', 'Consolas', monospace;">
                    {otp}
                </span>
            </div>
        </td>
    </tr>
</table>

<!-- Expiry Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 15px 0 25px 0;">
            <p style="margin: 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style="vertical-align: middle; margin-right: 6px;">
                    <circle cx="12" cy="12" r="10" stroke="{BRAND_COLORS['warning']}" stroke-width="2"/>
                    <path d="M12 6v6l4 2" stroke="{BRAND_COLORS['warning']}" stroke-width="2" stroke-linecap="round"/>
                </svg>
                This code expires in <strong style="color: {BRAND_COLORS['warning']};">10 minutes</strong>
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Security Notice -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6;">
    <strong>Didn't request this?</strong> If you didn't create an account with Prompterly,
    you can safely ignore this email. Someone may have entered your email by mistake.
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your Prompterly verification code is {otp}. This code expires in 10 minutes."
    )

    return plain_text, html


def get_welcome_email_template(name: str, dashboard_url: str) -> tuple[str, str]:
    """
    Generate welcome email after successful registration

    Args:
        name: User's name
        dashboard_url: URL to user dashboard

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Welcome to Prompterly! Your account has been successfully created.

You're now part of a community that's transforming how people learn and grow through AI-powered coaching.

Here's what you can do next:

1. Explore Lounges - Discover coaching spaces tailored to your interests
2. Meet Your AI Coach - Get personalized guidance anytime, anywhere
3. Take Notes - Capture insights and track your progress
4. Join the Community - Connect with mentors and fellow learners

Get started: {dashboard_url}

We're excited to have you on board!

Best regards,
The Prompterly Team

P.S. Have questions? Reply to this email or visit our Help Center.
"""

    content = f"""
<!-- Welcome Header with Accent Background -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: linear-gradient(135deg, {BRAND_COLORS['accent']} 0%, #e8f5c8 100%);
              border-radius: 12px; margin-bottom: 30px;">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <h1 style="margin: 0 0 10px 0; font-size: 28px; font-weight: 800; color: {BRAND_COLORS['primary']};">
                Welcome to Prompterly!
            </h1>
            <p style="margin: 0; font-size: 16px; color: {BRAND_COLORS['text_primary']};">
                Your journey to AI-powered growth starts now
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 30px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your account has been successfully created. You're now part of a growing community that's
    transforming how people learn and grow through AI-powered coaching.
</p>

<!-- What's Next Section -->
<h2 style="margin: 0 0 20px 0; font-size: 18px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    Here's what you can do next:
</h2>

<!-- Feature Cards -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <!-- Feature 1 -->
    <tr>
        <td style="padding: 12px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid {BRAND_COLORS['accent']};">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 40px; height: 40px; background-color: {BRAND_COLORS['accent']};
                                                border-radius: 10px; text-align: center; line-height: 40px; font-size: 20px;">
                                        🎯
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 5px 0; font-size: 15px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Explore Lounges
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.5;">
                                        Discover coaching spaces tailored to your interests and goals
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Feature 2 -->
    <tr>
        <td style="padding: 12px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid {BRAND_COLORS['success']};">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 40px; height: 40px; background-color: #d1fae5;
                                                border-radius: 10px; text-align: center; line-height: 40px; font-size: 20px;">
                                        🤖
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 5px 0; font-size: 15px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Meet Your AI Coach
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.5;">
                                        Get personalized guidance and support anytime, anywhere
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Feature 3 -->
    <tr>
        <td style="padding: 12px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid #8b5cf6;">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 40px; height: 40px; background-color: #ede9fe;
                                                border-radius: 10px; text-align: center; line-height: 40px; font-size: 20px;">
                                        📝
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 5px 0; font-size: 15px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Take Notes & Track Progress
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.5;">
                                        Capture insights and monitor your growth journey
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 35px 0 25px 0;">
            <a href="{dashboard_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 16px 40px; font-size: 16px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(26, 26, 31, 0.3);">
                Go to My Dashboard →
            </a>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 20px 0;">

<!-- Help Section -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 10px 0;">
            <p style="margin: 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
                Have questions? We're here to help!
            </p>
            <p style="margin: 10px 0 0 0; font-size: 14px;">
                <a href="mailto:support@prompterly.ai"
                   style="color: {BRAND_COLORS['primary']}; text-decoration: none; font-weight: 500;">
                    support@prompterly.ai
                </a>
            </p>
        </td>
    </tr>
</table>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Welcome to Prompterly, {name}! Your account is ready. Start exploring AI-powered coaching today."
    )

    return plain_text, html


def get_password_reset_otp_template(name: str, otp: str) -> tuple[str, str]:
    """
    Generate password reset OTP email

    Args:
        name: User's name
        otp: 6-digit OTP code

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

We received a request to reset your Prompterly password.

Your password reset code: {otp}

This code will expire in 10 minutes.

If you didn't request a password reset, please ignore this email. Your password will remain unchanged.

For security, never share this code with anyone.

Best regards,
The Prompterly Team
"""

    content = f"""
<!-- Header -->
<h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    Reset Your Password
</h1>
<p style="margin: 0 0 25px 0; font-size: 16px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.6;">
    Hi {name}, we received a request to reset your password.
</p>

<!-- Message -->
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Use the following code to reset your password:
</p>

<!-- OTP Code Box -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 25px 0;">
            <div style="display: inline-block; background-color: #fef2f2;
                        padding: 20px 40px; border-radius: 12px; border: 2px dashed {BRAND_COLORS['error']};">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 12px; color: {BRAND_COLORS['error']};
                             font-family: 'Monaco', 'Consolas', monospace;">
                    {otp}
                </span>
            </div>
        </td>
    </tr>
</table>

<!-- Expiry Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 15px 0 25px 0;">
            <p style="margin: 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
                This code expires in <strong style="color: {BRAND_COLORS['warning']};">10 minutes</strong>
            </p>
        </td>
    </tr>
</table>

<!-- Security Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #fef3c7; border-radius: 8px; margin-top: 10px;">
    <tr>
        <td style="padding: 16px 20px;">
            <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.6;">
                <strong>⚠️ Security Tip:</strong> Never share this code with anyone.
                Prompterly will never ask for your password or verification codes.
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Didn't Request Notice -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6;">
    <strong>Didn't request this?</strong> If you didn't request a password reset,
    please ignore this email. Your password will remain unchanged.
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your Prompterly password reset code is {otp}. This code expires in 10 minutes."
    )

    return plain_text, html


def get_user_credentials_email_template(
    name: str,
    email: str,
    password: str,
    login_url: str
) -> tuple[str, str]:
    """
    Generate credentials email for user created by admin

    Args:
        name: User's name
        email: User's email (login username)
        password: Temporary password
        login_url: URL to login page

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Welcome to Prompterly! An account has been created for you.

Here are your login credentials:

Email: {email}
Temporary Password: {password}

Please login at: {login_url}

For security, we recommend changing your password after your first login.

If you have any questions, please contact our support team.

Best regards,
The Prompterly Team
"""

    content = f"""
<!-- Header -->
<h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    Welcome to Prompterly!
</h1>
<p style="margin: 0 0 25px 0; font-size: 16px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.6;">
    Hi {name}, an account has been created for you.
</p>

<!-- Credentials Box -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; border: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <h3 style="margin: 0 0 20px 0; font-size: 16px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                Your Login Credentials
            </h3>

            <!-- Email -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 15px;">
                <tr>
                    <td style="width: 100px; font-size: 14px; color: {BRAND_COLORS['text_secondary']}; padding: 8px 0;">
                        Email:
                    </td>
                    <td style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']}; padding: 8px 0;">
                        {email}
                    </td>
                </tr>
            </table>

            <!-- Password -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="width: 100px; font-size: 14px; color: {BRAND_COLORS['text_secondary']}; padding: 8px 0;">
                        Password:
                    </td>
                    <td style="padding: 8px 0;">
                        <code style="background-color: {BRAND_COLORS['accent']}; padding: 8px 16px; border-radius: 6px;
                                     font-size: 15px; font-weight: 700; color: {BRAND_COLORS['primary']}; letter-spacing: 1px;">
                            {password}
                        </code>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 20px 0;">
            <a href="{login_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 16px 40px; font-size: 16px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(26, 26, 31, 0.3);">
                Login to Your Account →
            </a>
        </td>
    </tr>
</table>

<!-- Security Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #fef3c7; border-radius: 8px; margin-top: 20px;">
    <tr>
        <td style="padding: 16px 20px;">
            <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.6;">
                <strong>🔒 Security Tip:</strong> For your security, please change your password
                after your first login. Never share your credentials with anyone.
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Need help? Contact us at <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Welcome to Prompterly, {name}! Your account credentials are ready."
    )

    return plain_text, html


def get_mentor_welcome_email_template(
    name: str,
    prompterly_url: str
) -> tuple[str, str]:
    """
    Generate welcome email for mentor created by admin
    (No credentials since there's no mentor portal)

    Args:
        name: Mentor's name
        prompterly_url: Main Prompterly website URL

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Congratulations! You've been selected to join Prompterly as a Mentor!

We're thrilled to have you on board. As a Prompterly Mentor, you'll have the opportunity to:

- Share your expertise with learners worldwide
- Build your personal coaching lounge
- Connect with motivated individuals seeking guidance
- Make a meaningful impact through AI-powered coaching

What happens next?

Our team will be in touch shortly to guide you through the onboarding process and help you set up your coaching lounge.

In the meantime, feel free to explore Prompterly: {prompterly_url}

We're excited to partner with you on this journey!

Best regards,
The Prompterly Team

Questions? Reach out to us at mentors@prompterly.ai
"""

    content = f"""
<!-- Celebration Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: linear-gradient(135deg, {BRAND_COLORS['accent']} 0%, #e8f5c8 100%);
              border-radius: 12px; margin-bottom: 30px;">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
            <h1 style="margin: 0 0 10px 0; font-size: 26px; font-weight: 800; color: {BRAND_COLORS['primary']};">
                Welcome to Prompterly, Mentor!
            </h1>
            <p style="margin: 0; font-size: 16px; color: {BRAND_COLORS['text_primary']};">
                You've been selected to join our mentorship program
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 30px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Congratulations! We're thrilled to welcome you to the Prompterly mentor community.
    Your expertise and passion will help transform how people learn and grow.
</p>

<!-- Benefits Section -->
<h2 style="margin: 0 0 20px 0; font-size: 18px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    As a Prompterly Mentor, you'll be able to:
</h2>

<!-- Benefit Cards -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <!-- Benefit 1 -->
    <tr>
        <td style="padding: 10px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid {BRAND_COLORS['success']};">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 36px; height: 36px; background-color: #d1fae5;
                                                border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                        🌍
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Share Your Expertise Globally
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.4;">
                                        Reach learners worldwide with your AI-powered coaching lounge
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Benefit 2 -->
    <tr>
        <td style="padding: 10px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid #8b5cf6;">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 36px; height: 36px; background-color: #ede9fe;
                                                border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                        🏠
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Build Your Coaching Lounge
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.4;">
                                        Create a personalized space for your coaching content and interactions
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Benefit 3 -->
    <tr>
        <td style="padding: 10px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                   style="background-color: {BRAND_COLORS['surface']}; border-radius: 10px; border-left: 4px solid {BRAND_COLORS['accent']};">
                <tr>
                    <td style="padding: 16px 20px;">
                        <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 15px;">
                                    <div style="width: 36px; height: 36px; background-color: {BRAND_COLORS['accent']};
                                                border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                        💡
                                    </div>
                                </td>
                                <td style="vertical-align: top;">
                                    <h3 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        Make a Meaningful Impact
                                    </h3>
                                    <p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.4;">
                                        Help individuals achieve their goals through AI-enhanced guidance
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- What's Next Section -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #eff6ff; border-radius: 12px; margin: 30px 0;">
    <tr>
        <td style="padding: 25px;">
            <h3 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #1e40af;">
                📅 What happens next?
            </h3>
            <p style="margin: 0; font-size: 14px; color: #3b82f6; line-height: 1.6;">
                Our team will reach out within the next few days to guide you through
                the onboarding process and help you set up your coaching lounge.
            </p>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 15px 0;">
            <a href="{prompterly_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 14px 35px; font-size: 15px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(26, 26, 31, 0.3);">
                Explore Prompterly →
            </a>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Contact Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Questions about the mentor program?<br>
    Reach out to us at <a href="mailto:mentors@prompterly.ai" style="color: {BRAND_COLORS['primary']};">mentors@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Congratulations {name}! You've been selected to join Prompterly as a Mentor."
    )

    return plain_text, html


def get_contact_confirmation_email_template(
    name: str,
    subject: str
) -> tuple[str, str]:
    """
    Generate contact form confirmation email for user

    Args:
        name: User's name
        subject: Subject of their inquiry

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Thank you for reaching out to Prompterly!

We've received your message regarding: "{subject}"

Our team will review your inquiry and get back to you within 24-48 hours.

In the meantime, feel free to explore our coaching lounges and discover AI-powered mentorship.

Best regards,
The Prompterly Team

Need urgent assistance? Email us at support@prompterly.ai
"""

    content = f"""
<!-- Header -->
<h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    We've Received Your Message!
</h1>
<p style="margin: 0 0 25px 0; font-size: 16px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.6;">
    Hi {name}, thank you for reaching out to Prompterly.
</p>

<!-- Confirmation Box -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #ecfdf5; border-radius: 12px; border: 1px solid #a7f3d0; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 15px;">
                        <div style="width: 44px; height: 44px; background-color: {BRAND_COLORS['success']};
                                    border-radius: 50%; text-align: center; line-height: 44px; font-size: 22px; color: white;">
                            ✓
                        </div>
                    </td>
                    <td style="vertical-align: top;">
                        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600; color: #065f46;">
                            Message Received Successfully
                        </h3>
                        <p style="margin: 0; font-size: 14px; color: #047857; line-height: 1.5;">
                            Your inquiry about "<strong>{subject}</strong>" has been submitted.
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- Timeline -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="padding: 15px 0;">
            <p style="margin: 0; font-size: 15px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
                <strong>What happens next?</strong>
            </p>
            <p style="margin: 10px 0 0 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
                Our team will review your message and respond within <strong>24-48 hours</strong>.
                We appreciate your patience and look forward to assisting you.
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Support Section -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
                Need urgent assistance?
            </p>
            <a href="mailto:support@prompterly.ai"
               style="display: inline-block; background-color: {BRAND_COLORS['surface']}; color: {BRAND_COLORS['text_primary']};
                      padding: 12px 30px; font-size: 14px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; border: 1px solid {BRAND_COLORS['border']};">
                Email Support
            </a>
        </td>
    </tr>
</table>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Thanks for contacting Prompterly, {name}! We've received your message and will respond within 24-48 hours."
    )

    return plain_text, html


def get_contact_admin_notification_template(
    name: str,
    email: str,
    subject: str,
    message: str,
    ip_address: str,
    submitted_at: str,
    message_id: int
) -> tuple[str, str]:
    """
    Generate contact form notification email for admin

    Args:
        name: Sender's name
        email: Sender's email
        subject: Message subject
        message: Message content
        ip_address: Sender's IP address
        submitted_at: Submission timestamp
        message_id: Database message ID

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
New Contact Form Submission

From: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
IP Address: {ip_address}
Submitted at: {submitted_at}
Message ID: {message_id}
"""

    content = f"""
<!-- Header -->
<h1 style="margin: 0 0 10px 0; font-size: 22px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    New Contact Form Submission
</h1>
<p style="margin: 0 0 25px 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
    A new message has been received through the contact form.
</p>

<!-- Sender Info Card -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; margin-bottom: 20px;">
    <tr>
        <td style="padding: 20px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 13px; color: {BRAND_COLORS['text_muted']}; display: inline-block; width: 80px;">From:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">{name}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 13px; color: {BRAND_COLORS['text_muted']}; display: inline-block; width: 80px;">Email:</span>
                        <a href="mailto:{email}" style="font-size: 14px; color: {BRAND_COLORS['primary']}; text-decoration: none;">{email}</a>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;">
                        <span style="font-size: 13px; color: {BRAND_COLORS['text_muted']}; display: inline-block; width: 80px;">Subject:</span>
                        <span style="font-size: 14px; font-weight: 500; color: {BRAND_COLORS['text_primary']};">{subject}</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- Message Content -->
<h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
    Message:
</h3>
<div style="background-color: #ffffff; border: 1px solid {BRAND_COLORS['border']}; border-radius: 8px;
            padding: 20px; font-size: 14px; color: {BRAND_COLORS['text_primary']}; line-height: 1.7;
            white-space: pre-wrap; word-wrap: break-word;">
{message}
</div>

<!-- Reply Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 25px 0;">
            <a href="mailto:{email}?subject=Re: {subject}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 12px 30px; font-size: 14px; font-weight: 600; text-decoration: none;
                      border-radius: 50px;">
                Reply to {name}
            </a>
        </td>
    </tr>
</table>

<!-- Metadata -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 8px;">
    <tr>
        <td style="padding: 15px;">
            <p style="margin: 0; font-size: 12px; color: {BRAND_COLORS['text_muted']};">
                <strong>IP Address:</strong> {ip_address}<br>
                <strong>Submitted:</strong> {submitted_at}<br>
                <strong>Message ID:</strong> #{message_id}
            </p>
        </td>
    </tr>
</table>
"""

    html = get_base_template(
        content=content,
        preview_text=f"New contact from {name}: {subject}",
        show_footer_links=False
    )

    return plain_text, html


def get_subscription_confirmation_email_template(
    name: str,
    lounge_name: str,
    mentor_name: str,
    plan_type: str,
    price: str,
    next_billing_date: str,
    dashboard_url: str
) -> tuple[str, str]:
    """
    Generate subscription confirmation email when user subscribes to a lounge

    Args:
        name: User's name
        lounge_name: Name of the subscribed lounge
        mentor_name: Name of the lounge mentor
        plan_type: Subscription plan type (monthly/yearly)
        price: Subscription price
        next_billing_date: Next billing date
        dashboard_url: URL to user dashboard

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Welcome to {lounge_name}!

Your subscription has been successfully activated. Here are your subscription details:

Lounge: {lounge_name}
Mentor: {mentor_name}
Plan: {plan_type}
Price: {price}
Next Billing Date: {next_billing_date}

You now have full access to:
- AI-powered coaching sessions
- Exclusive lounge resources
- Direct mentorship content
- Community features

Access your lounge: {dashboard_url}

Thank you for subscribing!

Best regards,
The Prompterly Team
"""

    content = f"""
<!-- Success Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
              border-radius: 12px; margin-bottom: 30px;">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <div style="width: 60px; height: 60px; background-color: {BRAND_COLORS['success']};
                        border-radius: 50%; margin: 0 auto 15px; text-align: center; line-height: 60px;">
                <span style="font-size: 28px; color: white;">✓</span>
            </div>
            <h1 style="margin: 0 0 10px 0; font-size: 26px; font-weight: 800; color: #065f46;">
                Subscription Confirmed!
            </h1>
            <p style="margin: 0; font-size: 16px; color: #047857;">
                Welcome to {lounge_name}
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your subscription to <strong>{lounge_name}</strong> has been successfully activated.
    You now have full access to all the amazing content and features.
</p>

<!-- Subscription Details Card -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; border: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <h3 style="margin: 0 0 20px 0; font-size: 16px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                Subscription Details
            </h3>
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Lounge:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">{lounge_name}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Mentor:</span>
                        <span style="font-size: 14px; font-weight: 500; color: {BRAND_COLORS['text_primary']};">{mentor_name}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Plan:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['success']}; text-transform: capitalize;">{plan_type}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Price:</span>
                        <span style="font-size: 14px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">{price}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Next Billing:</span>
                        <span style="font-size: 14px; font-weight: 500; color: {BRAND_COLORS['text_primary']};">{next_billing_date}</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- What You Get Section -->
<h2 style="margin: 30px 0 20px 0; font-size: 18px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    What's included in your subscription:
</h2>

<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        AI-powered coaching sessions with personalized guidance
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Exclusive lounge resources and learning materials
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Direct access to mentor's expertise and content
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Note-taking and progress tracking tools
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 35px 0 25px 0;">
            <a href="{dashboard_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 16px 40px; font-size: 16px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(26, 26, 31, 0.3);">
                Access Your Lounge →
            </a>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 20px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Questions about your subscription? Contact us at
    <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Welcome to {lounge_name}! Your subscription is now active."
    )

    return plain_text, html


def get_subscription_expiry_warning_email_template(
    name: str,
    lounge_name: str,
    expiry_date: str,
    days_remaining: int,
    renewal_url: str
) -> tuple[str, str]:
    """
    Generate subscription expiry warning email

    Args:
        name: User's name
        lounge_name: Name of the lounge
        expiry_date: Subscription expiry date
        days_remaining: Days until expiry
        renewal_url: URL to renew subscription

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Your subscription to {lounge_name} is expiring soon!

Your subscription will expire on {expiry_date} ({days_remaining} days remaining).

Don't lose access to:
- AI-powered coaching sessions
- Exclusive lounge resources
- Your saved notes and progress

Renew your subscription now to continue your learning journey without interruption.

Renew here: {renewal_url}

Best regards,
The Prompterly Team
"""

    # Determine urgency color based on days remaining
    urgency_color = BRAND_COLORS['error'] if days_remaining <= 3 else BRAND_COLORS['warning']
    urgency_bg = "#fef2f2" if days_remaining <= 3 else "#fef3c7"
    urgency_text = "#991b1b" if days_remaining <= 3 else "#92400e"

    content = f"""
<!-- Warning Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: {urgency_bg}; border-radius: 12px; margin-bottom: 30px; border: 2px solid {urgency_color};">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 15px;">⏰</div>
            <h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 800; color: {urgency_text};">
                Your Subscription is Expiring Soon
            </h1>
            <p style="margin: 0; font-size: 16px; color: {urgency_text};">
                <strong>{days_remaining} days</strong> remaining
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your subscription to <strong>{lounge_name}</strong> is expiring on <strong>{expiry_date}</strong>.
    Renew now to continue enjoying uninterrupted access to all features.
</p>

<!-- Expiry Details Card -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; border: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Lounge:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">{lounge_name}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Expiry Date:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {urgency_color};">{expiry_date}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Days Left:</span>
                        <span style="font-size: 14px; font-weight: 700; color: {urgency_color};">{days_remaining} days</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- What You'll Lose Section -->
<h2 style="margin: 30px 0 20px 0; font-size: 18px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    Don't lose access to:
</h2>

<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['warning']}; font-size: 16px;">⚠️</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        AI-powered coaching sessions
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['warning']}; font-size: 16px;">⚠️</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Exclusive lounge resources and materials
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['warning']}; font-size: 16px;">⚠️</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Your saved notes and progress tracking
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 35px 0 25px 0;">
            <a href="{renewal_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['success']}; color: #ffffff;
                      padding: 16px 40px; font-size: 16px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.3);">
                Renew Subscription Now →
            </a>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 20px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Questions? Contact us at
    <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your {lounge_name} subscription expires in {days_remaining} days. Renew now to keep access."
    )

    return plain_text, html


def get_subscription_upgrade_email_template(
    name: str,
    lounge_name: str,
    old_plan: str,
    new_plan: str,
    new_price: str,
    savings: str,
    next_billing_date: str,
    dashboard_url: str
) -> tuple[str, str]:
    """
    Generate subscription upgrade confirmation email (monthly to yearly)

    Args:
        name: User's name
        lounge_name: Name of the lounge
        old_plan: Previous plan type
        new_plan: New plan type
        new_price: New subscription price
        savings: Amount saved by upgrading
        next_billing_date: Next billing date
        dashboard_url: URL to user dashboard

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Great news! Your subscription has been upgraded!

Your {lounge_name} subscription has been successfully upgraded from {old_plan} to {new_plan}.

Subscription Details:
- Lounge: {lounge_name}
- New Plan: {new_plan}
- New Price: {new_price}
- You're saving: {savings}
- Next Billing: {next_billing_date}

Thank you for your continued commitment to your growth journey!

Access your lounge: {dashboard_url}

Best regards,
The Prompterly Team
"""

    content = f"""
<!-- Celebration Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: linear-gradient(135deg, {BRAND_COLORS['accent']} 0%, #e8f5c8 100%);
              border-radius: 12px; margin-bottom: 30px;">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 15px;">🎉</div>
            <h1 style="margin: 0 0 10px 0; font-size: 26px; font-weight: 800; color: {BRAND_COLORS['primary']};">
                Subscription Upgraded!
            </h1>
            <p style="margin: 0; font-size: 16px; color: {BRAND_COLORS['text_primary']};">
                You're now on the {new_plan} plan
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your subscription to <strong>{lounge_name}</strong> has been successfully upgraded
    from <strong>{old_plan}</strong> to <strong>{new_plan}</strong>.
</p>

<!-- Savings Highlight -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #ecfdf5; border-radius: 12px; border: 2px solid {BRAND_COLORS['success']}; margin: 25px 0;">
    <tr>
        <td style="padding: 20px; text-align: center;">
            <p style="margin: 0 0 5px 0; font-size: 14px; color: #047857;">
                You're saving
            </p>
            <p style="margin: 0; font-size: 28px; font-weight: 800; color: {BRAND_COLORS['success']};">
                {savings}
            </p>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #047857;">
                with your new plan!
            </p>
        </td>
    </tr>
</table>

<!-- Subscription Details Card -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; border: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <h3 style="margin: 0 0 20px 0; font-size: 16px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                Updated Subscription Details
            </h3>
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Lounge:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">{lounge_name}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Previous Plan:</span>
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_muted']}; text-decoration: line-through;">{old_plan}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">New Plan:</span>
                        <span style="font-size: 14px; font-weight: 600; color: {BRAND_COLORS['success']};">{new_plan}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid {BRAND_COLORS['border']};">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">New Price:</span>
                        <span style="font-size: 14px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">{new_price}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;">
                        <span style="font-size: 14px; color: {BRAND_COLORS['text_secondary']}; display: inline-block; width: 120px;">Next Billing:</span>
                        <span style="font-size: 14px; font-weight: 500; color: {BRAND_COLORS['text_primary']};">{next_billing_date}</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CTA Button -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="text-align: center; padding: 25px 0;">
            <a href="{dashboard_url}"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 16px 40px; font-size: 16px; font-weight: 600; text-decoration: none;
                      border-radius: 50px; box-shadow: 0 4px 14px 0 rgba(26, 26, 31, 0.3);">
                Continue Learning →
            </a>
        </td>
    </tr>
</table>

<!-- Thank You Note -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #eff6ff; border-radius: 8px; margin-top: 10px;">
    <tr>
        <td style="padding: 16px 20px; text-align: center;">
            <p style="margin: 0; font-size: 14px; color: #1e40af; line-height: 1.6;">
                Thank you for your continued commitment to your growth journey!
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Questions? Contact us at
    <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your {lounge_name} subscription has been upgraded to {new_plan}. You're saving {savings}!"
    )

    return plain_text, html


def get_subscription_cancellation_email_template(
    name: str,
    lounge_name: str,
    access_end_date: str,
    feedback_url: Optional[str] = None
) -> tuple[str, str]:
    """
    Generate subscription cancellation confirmation email

    Args:
        name: User's name
        lounge_name: Name of the lounge
        access_end_date: Date when access ends
        feedback_url: Optional URL for feedback form

    Returns:
        Tuple of (plain_text, html)
    """
    feedback_section = ""
    if feedback_url:
        feedback_section = f"""
We'd love to hear from you! If you have a moment, please let us know why you decided to cancel:
{feedback_url}
"""

    plain_text = f"""
Hi {name},

Your subscription to {lounge_name} has been cancelled.

You'll continue to have access until {access_end_date}.

What happens next:
- You can still access all features until {access_end_date}
- Your notes and progress will be saved
- You can resubscribe anytime to regain full access
{feedback_section}
We're sorry to see you go. If there's anything we can do to improve, please let us know.

Best regards,
The Prompterly Team
"""

    feedback_html = ""
    if feedback_url:
        feedback_html = f"""
<!-- Feedback Section -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #eff6ff; border-radius: 12px; margin: 25px 0;">
    <tr>
        <td style="padding: 25px; text-align: center;">
            <p style="margin: 0 0 15px 0; font-size: 15px; color: #1e40af;">
                We'd love to hear from you
            </p>
            <a href="{feedback_url}"
               style="display: inline-block; background-color: #3b82f6; color: #ffffff;
                      padding: 12px 30px; font-size: 14px; font-weight: 600; text-decoration: none;
                      border-radius: 50px;">
                Share Feedback
            </a>
        </td>
    </tr>
</table>
"""

    content = f"""
<!-- Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="margin-bottom: 25px;">
    <tr>
        <td style="text-align: center;">
            <div style="font-size: 48px; margin-bottom: 15px;">👋</div>
            <h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
                Subscription Cancelled
            </h1>
            <p style="margin: 0; font-size: 16px; color: {BRAND_COLORS['text_secondary']};">
                We're sorry to see you go
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your subscription to <strong>{lounge_name}</strong> has been cancelled as requested.
</p>

<!-- Access End Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #fef3c7; border-radius: 12px; border: 1px solid {BRAND_COLORS['warning']}; margin: 25px 0;">
    <tr>
        <td style="padding: 20px; text-align: center;">
            <p style="margin: 0 0 5px 0; font-size: 14px; color: #92400e;">
                You'll continue to have access until
            </p>
            <p style="margin: 0; font-size: 22px; font-weight: 700; color: #92400e;">
                {access_end_date}
            </p>
        </td>
    </tr>
</table>

<!-- What Happens Next -->
<h2 style="margin: 30px 0 20px 0; font-size: 18px; font-weight: 700; color: {BRAND_COLORS['text_primary']};">
    What happens next:
</h2>

<table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        You can still access all features until {access_end_date}
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        Your notes and progress will be saved
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align: top; padding-right: 12px;">
                        <span style="color: {BRAND_COLORS['success']}; font-size: 16px;">✓</span>
                    </td>
                    <td style="font-size: 14px; color: {BRAND_COLORS['text_primary']};">
                        You can resubscribe anytime to regain full access
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

{feedback_html}

<!-- Miss You Section -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; margin: 25px 0;">
    <tr>
        <td style="padding: 25px; text-align: center;">
            <p style="margin: 0 0 10px 0; font-size: 15px; color: {BRAND_COLORS['text_primary']};">
                Changed your mind?
            </p>
            <p style="margin: 0 0 20px 0; font-size: 14px; color: {BRAND_COLORS['text_secondary']};">
                You can resubscribe anytime and pick up where you left off.
            </p>
            <a href="https://prompterly.ai/lounges"
               style="display: inline-block; background-color: {BRAND_COLORS['primary']}; color: #ffffff;
                      padding: 12px 30px; font-size: 14px; font-weight: 600; text-decoration: none;
                      border-radius: 50px;">
                Browse Lounges
            </a>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    If there's anything we can do to improve, please let us know at
    <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your {lounge_name} subscription has been cancelled. You have access until {access_end_date}."
    )

    return plain_text, html


def get_payment_method_update_email_template(
    name: str,
    card_last_four: str,
    card_brand: str,
    updated_at: str
) -> tuple[str, str]:
    """
    Generate payment method update confirmation email
    Note: Does not include full card details for security

    Args:
        name: User's name
        card_last_four: Last 4 digits of the card
        card_brand: Card brand (Visa, Mastercard, etc.)
        updated_at: Timestamp of the update

    Returns:
        Tuple of (plain_text, html)
    """
    plain_text = f"""
Hi {name},

Your payment method has been successfully updated!

Payment Method Details:
- Card: {card_brand} ending in {card_last_four}
- Updated: {updated_at}

Your future subscription payments will be charged to this card.

If you didn't make this change, please contact our support team immediately.

Best regards,
The Prompterly Team

Security Notice: If you didn't update your payment method, please contact us at support@prompterly.ai
"""

    content = f"""
<!-- Success Header -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
              border-radius: 12px; margin-bottom: 30px;">
    <tr>
        <td style="padding: 30px; text-align: center;">
            <div style="width: 60px; height: 60px; background-color: {BRAND_COLORS['success']};
                        border-radius: 50%; margin: 0 auto 15px; text-align: center; line-height: 60px;">
                <span style="font-size: 28px; color: white;">💳</span>
            </div>
            <h1 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 700; color: #065f46;">
                Payment Method Updated
            </h1>
            <p style="margin: 0; font-size: 16px; color: #047857;">
                Your card has been successfully updated
            </p>
        </td>
    </tr>
</table>

<!-- Personal Greeting -->
<p style="margin: 0 0 20px 0; font-size: 16px; color: {BRAND_COLORS['text_primary']}; line-height: 1.6;">
    Hi {name},
</p>
<p style="margin: 0 0 25px 0; font-size: 15px; color: {BRAND_COLORS['text_secondary']}; line-height: 1.7;">
    Your payment method has been successfully updated. Your future subscription payments
    will be charged to this new card.
</p>

<!-- Payment Details Card -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: {BRAND_COLORS['surface']}; border-radius: 12px; border: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">
    <tr>
        <td style="padding: 25px;">
            <h3 style="margin: 0 0 20px 0; font-size: 16px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                New Payment Method
            </h3>
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 15px; background-color: white; border-radius: 8px; border: 1px solid {BRAND_COLORS['border']};">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="vertical-align: middle; padding-right: 15px; width: 50px;">
                                    <div style="width: 50px; height: 32px; background-color: #1a1a1f;
                                                border-radius: 4px; text-align: center; line-height: 32px;
                                                font-size: 12px; color: white; font-weight: 600;">
                                        {card_brand[:4].upper()}
                                    </div>
                                </td>
                                <td style="vertical-align: middle;">
                                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: {BRAND_COLORS['text_primary']};">
                                        {card_brand} •••• {card_last_four}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            <p style="margin: 15px 0 0 0; font-size: 13px; color: {BRAND_COLORS['text_muted']};">
                Updated on {updated_at}
            </p>
        </td>
    </tr>
</table>

<!-- Security Notice -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
       style="background-color: #fef3c7; border-radius: 8px; margin-top: 20px;">
    <tr>
        <td style="padding: 16px 20px;">
            <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.6;">
                <strong>🔒 Security Notice:</strong> If you didn't make this change or don't recognize this activity,
                please contact our support team immediately at
                <a href="mailto:support@prompterly.ai" style="color: #92400e; font-weight: 600;">support@prompterly.ai</a>
            </p>
        </td>
    </tr>
</table>

<!-- Divider -->
<hr style="border: none; border-top: 1px solid {BRAND_COLORS['border']}; margin: 25px 0;">

<!-- Help Section -->
<p style="margin: 0; font-size: 13px; color: {BRAND_COLORS['text_muted']}; line-height: 1.6; text-align: center;">
    Questions about billing? Contact us at
    <a href="mailto:support@prompterly.ai" style="color: {BRAND_COLORS['primary']};">support@prompterly.ai</a>
</p>
"""

    html = get_base_template(
        content=content,
        preview_text=f"Your payment method has been updated to {card_brand} ending in {card_last_four}."
    )

    return plain_text, html
