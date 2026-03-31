"""
Professional email templates for Prompterly
All templates match the approved PDF designs from Lauren's 'Prompterly Automated Emails - MVP1' document.
"""
from typing import Optional

BRAND_COLORS = {
    "primary": "#1A1A1F",
    "cta": "#F97316",
    "surface": "#f9fafb",
    "background": "#ffffff",
    "border": "#e5e7eb",
    "text_primary": "#1f2937",
    "text_secondary": "#6b7280",
    "text_muted": "#9ca3af",
}


def _cta(text: str, url: str) -> str:
    return f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr><td style="padding:5px 0 25px 0;"><a href="{url}" style="display:inline-block;padding:14px 32px;background-color:{BRAND_COLORS["cta"]};color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">{text}</a></td></tr></table>'


def _p(text: str, bold: bool = False) -> str:
    w = "600" if bold else "400"
    c = BRAND_COLORS["text_primary"] if bold else BRAND_COLORS["text_secondary"]
    return f'<p style="margin:0 0 15px 0;font-size:15px;font-weight:{w};color:{c};line-height:1.6;">{text}</p>'


def _detail(label: str, value: str) -> str:
    return f'<p style="margin:0 0 3px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>{label}:</strong> {value}</p>'


def _footer() -> str:
    return f'<p style="margin:20px 0 0 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};font-weight:600;">Prompterly Support</p>'


def _support(prefix: str = "If you have any questions, please view our") -> str:
    return f'<p style="margin:0 0 0 0;font-size:13px;color:{BRAND_COLORS["text_muted"]};line-height:1.6;">{prefix} <a href="https://prompterly.ai/support" style="color:{BRAND_COLORS["primary"]};">support page</a>.</p>'


def _contact() -> str:
    return f'<p style="margin:0 0 0 0;font-size:13px;color:{BRAND_COLORS["text_muted"]};line-height:1.6;">If you need help, you can contact us at <a href="mailto:support@prompterly.ai" style="color:{BRAND_COLORS["primary"]};">support@prompterly.ai</a>.</p>'


def _support_link() -> str:
    return f'<a href="https://prompterly.ai/support" style="color:{BRAND_COLORS["text_secondary"]};font-size:13px;">https://prompterly.ai/support</a>'


def get_base_template(content: str, preview_text: str = "", show_footer_links: bool = True) -> str:
    footer_links = ""
    if show_footer_links:
        footer_links = f'''<tr><td style="padding:0 0 20px 0;text-align:center;"><a href="https://prompterly.ai" style="color:{BRAND_COLORS["text_secondary"]};text-decoration:none;margin:0 10px;font-size:13px;">Website</a><span style="color:{BRAND_COLORS["border"]};">|</span><a href="https://prompterly.ai/about" style="color:{BRAND_COLORS["text_secondary"]};text-decoration:none;margin:0 10px;font-size:13px;">About Us</a><span style="color:{BRAND_COLORS["border"]};">|</span><a href="https://prompterly.ai/contact" style="color:{BRAND_COLORS["text_secondary"]};text-decoration:none;margin:0 10px;font-size:13px;">Contact</a></td></tr>'''
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Prompterly</title></head><body style="margin:0;padding:0;background-color:{BRAND_COLORS["surface"]};font-family:'Inter','Segoe UI',Arial,sans-serif;"><div style="display:none;max-height:0;overflow:hidden;">{preview_text}</div><table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:{BRAND_COLORS["surface"]};"><tr><td style="padding:40px 20px;"><table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px;margin:0 auto;"><tr><td style="text-align:center;padding-bottom:30px;"><img src="https://prompterly.bitsclan.us/images/black-logo.png" alt="Prompterly" width="180" style="display:inline-block;max-width:180px;height:auto;"></td></tr><tr><td><table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:{BRAND_COLORS["background"]};border-radius:16px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);"><tr><td style="padding:40px;">{content}</td></tr></table></td></tr><tr><td style="padding-top:30px;"><table role="presentation" cellpadding="0" cellspacing="0" width="100%">{footer_links}<tr><td style="text-align:center;padding:10px 0;"><p style="margin:0;font-size:12px;color:{BRAND_COLORS["text_muted"]};">&copy; 2025 Prompterly. All rights reserved.</p></td></tr></table></td></tr></table></td></tr></table></body></html>'''


# ── EMAIL #1 — Account Verification Code ─────────────────────────────────────
# Subject: XXXXXX is your prompterly verification code

def get_otp_email_template(name: str, otp: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYou're almost in.\nHere's your verification code:\n\n{otp}\n\nEnter this to continue setting up your prompterly account. For your security, don't forward this email or share this code with anyone.\n\nThis code will expire in 10 minutes.\n\nPrompterly Support\nhttps://prompterly.ai/support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Sign in to prompterly</h1>
{_p(f"Hi {name},", bold=True)}
{_p("You're almost in.")}
{_p("Here's your verification code:")}
<p style="margin:0 0 20px 0;font-size:36px;font-weight:800;color:{BRAND_COLORS["text_primary"]};letter-spacing:4px;">{otp}</p>
<p style="margin:0 0 10px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">Enter this to continue setting up your prompterly account. For your security, don't forward this email or share this code with anyone.</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This code will expire in 10 minutes.</p>
{_footer()}
{_support_link()}'''
    return plain_text, get_base_template(content, f"{otp} is your prompterly verification code")


# ── EMAIL #2 — Welcome / Account Registration ────────────────────────────────
# Subject: Welcome to prompterly

def get_welcome_email_template(name: str, dashboard_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYour Prompterly account is now set up and ready.\n\nWhen you log in, you'll land in your dashboard where you'll see the Coaching Lounge(s) you've subscribed to.\n\nTo get started, simply click \"Enter Lounge\" and begin.\n\nYou can also explore and browse other Coaching Lounges available to you at any time.\n\nEach lounge is trained around a trusted mentor's perspective, giving you direct access to their thinking, guidance and support whenever you need it.\n\nGo to dashboard: {dashboard_url}\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};font-style:italic;">You're in!</h1>
{_p(f"Hi {name},", bold=True)}
{_p("Your Prompterly account is now set up and ready.")}
{_p("When you log in, you'll land in your dashboard where you'll see the Coaching Lounge(s) you've subscribed to.")}
{_p('To get started, simply click <strong>"Enter Lounge"</strong> and begin.')}
{_p("You can also explore and browse other Coaching Lounges available to you at any time.")}
{_p("Each lounge is trained around a trusted mentor's perspective, giving you direct access to their thinking, guidance and support whenever you need it.")}
{_cta("Go to dashboard", dashboard_url)}
{_support()}
{_footer()}'''
    return plain_text, get_base_template(content, "Your Prompterly account is now set up and ready")


# ── EMAIL #3 — Email Change Confirmation (sent to NEW email) ─────────────────
# Subject: Your account details have been updated

def get_email_change_confirmation_template(name: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nThis email address has been successfully linked to your Prompterly account.\n\nIf you made this change, no further action is needed.\n\nIf this wasn't you, please contact us immediately at support@prompterly.ai so we can help secure your account.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("This email address has been successfully linked to your Prompterly account.")}
{_p("If you made this change, no further action is needed.")}
<p style="margin:0 0 25px 0;font-size:15px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If this wasn't you, please contact us immediately at <a href="mailto:support@prompterly.ai" style="color:{BRAND_COLORS["primary"]};font-weight:600;">support@prompterly.ai</a> so we can help secure your account.</p>
{_support("If you have any other questions, please view our")}
{_footer()}'''
    return plain_text, get_base_template(content, "Your account details have been updated")


# ── EMAIL #4 — Email Change Alert (sent to OLD email) ────────────────────────
# Subject: Important: Your account details were updated

def get_email_change_alert_template(name: str, secure_account_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe noticed that the email address linked to your Prompterly account was recently changed.\n\nIf you made this update, you can ignore this message.\n\nIf this wasn't you, please secure your account immediately:\n{secure_account_url}\n\nThis link will allow you to review the change and regain control of your account.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("We noticed that the email address linked to your prompterly account was recently changed.")}
{_p("If you made this update, you can ignore this message.")}
{_p("If this wasn't you, please secure your account immediately.")}
{_cta("Secure my account", secure_account_url)}
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This link will allow you to review the change and regain control of your account.</p>
{_support("If you need support, please view our")}
{_footer()}'''
    return plain_text, get_base_template(content, "Important: Your account details were updated")


# ── EMAIL #5 — Password Reset Request ────────────────────────────────────────
# Subject: Reset your password

def get_password_reset_otp_template(name: str, otp: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe received a request to reset the password for your Prompterly account.\n\nYour password reset code: {otp}\n\nThis code will expire in 10 minutes for security reasons.\n\nIf you did not request this, you can ignore this email, no changes will be made to your account.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("We received a request to reset the password for your Prompterly account.")}
{_p("Your password reset code:")}
<p style="margin:0 0 20px 0;font-size:36px;font-weight:800;color:{BRAND_COLORS["text_primary"]};letter-spacing:4px;">{otp}</p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This code will expire in 10 minutes for security reasons.</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you did not request this, you can ignore this email, no changes will be made to your account.</p>
{_support("Need additional support? Please view our")}
{_footer()}'''
    return plain_text, get_base_template(content, "Reset your Prompterly password")


# ── EMAIL #6 — One Time Password (MFA) ───────────────────────────────────────
# Subject: XXXXXX is your prompterly verification code
# Trigger: New device login or email change

def get_mfa_otp_email_template(name: str, otp: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nTo continue, please enter the verification code below:\n\n{otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, you can ignore this email. For your security, this code cannot be used without access to your account.\n\nPrompterly Support\nhttps://prompterly.ai/support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Sign in to prompterly</h1>
{_p(f"Hi {name},", bold=True)}
{_p("To continue, please enter the verification code below:")}
<p style="margin:0 0 20px 0;font-size:36px;font-weight:800;color:{BRAND_COLORS["text_primary"]};letter-spacing:4px;">{otp}</p>
<p style="margin:0 0 10px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This code will expire in 10 minutes.</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you did not request this, you can ignore this email. For your security, this code cannot be used without access to your account.</p>
{_footer()}
{_support_link()}'''
    return plain_text, get_base_template(content, f"{otp} is your prompterly verification code")


# ── EMAIL #7 — Suspicious Login / New Device Alert ───────────────────────────
# Subject: New login detected

def get_suspicious_login_alert_template(name: str, login_time: str, device_info: str, reset_password_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe noticed a login to your Prompterly account from a new device or location.\n\nTime: {login_time}\nDevice/Location: {device_info}\n\nIf this was you, no further action is needed.\n\nIf this wasn't you, we recommend resetting your password immediately:\n{reset_password_url}\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("We noticed a login to your Prompterly account from a new device or location.")}
<p style="margin:0 0 5px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.6;"><strong>Time:</strong> {login_time}</p>
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.6;"><strong>Device/Location:</strong> {device_info}</p>
{_p("If this was you, no further action is needed.")}
{_p("If this wasn't you, we recommend resetting your password immediately.")}
{_cta("Reset password", reset_password_url)}
{_support("If you need additional support, please view our")}
{_footer()}'''
    return plain_text, get_base_template(content, "New login detected on your Prompterly account")


# ── EMAIL #8 — Subscription / Payment Confirmation ───────────────────────────
# Subject: Subscription confirmed: [Mentor Name]'s Coaching Lounge

def get_subscription_confirmation_email_template(name: str, mentor_name: str, mentor_focus: str, plan_type: str, amount: str, start_date: str, dashboard_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYou now have full access to {mentor_name}'s Coaching Lounge.\n\nMentor: {mentor_name}\nFocus: {mentor_focus}\nPlan: {plan_type}\nAmount: {amount}\nStart date: {start_date}\n\nYou can access your lounge at any time from your dashboard. Simply click \"Enter Lounge\" to begin.\n\nAll the best,\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"You now have full access to <strong>{mentor_name}'s Coaching Lounge</strong>.")}
{_p("Here are your subscription details:")}
{_detail("Mentor", mentor_name)}
{_detail("Focus", mentor_focus)}
{_detail("Plan", plan_type)}
{_detail("Amount", amount)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Start date:</strong> {start_date}</p>
{_p('You can access your lounge at any time from your dashboard. Simply click <strong>"Enter Lounge"</strong> to begin.')}
{_cta("Go to dashboard", dashboard_url)}
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This space is shaped by {mentor_name}'s perspective, designed to give you direct access to their thinking and guidance whenever you need it. Other key things to note:</p>
<ul style="margin:0 0 25px 0;padding-left:20px;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.8;"><li>You can manage or cancel your subscription at any time from your account settings.</li><li>You can also explore other Coaching Lounges available to you from your dashboard.</li></ul>
<p style="margin:0 0 5px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};">All the best,</p>
{_footer()}'''
    return plain_text, get_base_template(content, f"Subscription confirmed: {mentor_name}'s Coaching Lounge")


# ── EMAIL #9 — Annual Auto-Renew (30 Days Before) ────────────────────────────
# Subject: Upcoming renewal for your Coaching Lounge

def get_annual_renewal_30day_template(name: str, mentor_name: str, renewal_date: str, amount: str, manage_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYou've spent time inside {mentor_name}'s Coaching Lounge and your access is set to continue.\n\nRenewal date: {renewal_date}\nPlan: Annual\nAmount: {amount}\n\nYour subscription will automatically renew on this date, with uninterrupted access to the lounge.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"You've spent time inside <strong>{mentor_name}'s Coaching Lounge</strong> and your access is set to continue.")}
{_p("Here are your upcoming renewal details:")}
{_detail("Renewal date", renewal_date)}
{_detail("Plan", "Annual")}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Amount:</strong> {amount}</p>
{_p("Your subscription will automatically renew on this date, with uninterrupted access to the lounge.")}
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This space is shaped by {mentor_name}'s frameworks and perspective and is designed to give you direct access to their thinking and guidance whenever you need it.</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you'd like to make any changes, you can manage your subscription at any time from your account settings.</p>
{_cta("Manage my subscription", manage_url)}
{_footer()}'''
    return plain_text, get_base_template(content, "Upcoming renewal for your Coaching Lounge")


# ── EMAIL #10 — Annual Auto-Renew (7 Days Before) ────────────────────────────
# Subject: Reminder: your subscription renews soon

def get_annual_renewal_7day_template(name: str, mentor_name: str, renewal_date: str, amount: str, manage_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nJust a quick reminder that your subscription to {mentor_name}'s Coaching Lounge will renew soon.\n\nRenewal date: {renewal_date}\nAmount: {amount}\n\nYour access will continue automatically unless you make any changes.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"Just a quick reminder that your subscription to <strong>{mentor_name}'s Coaching Lounge</strong> will renew soon.")}
{_detail("Renewal date", renewal_date)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Amount:</strong> {amount}</p>
{_p("Your access will continue automatically unless you make any changes.")}
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">You can manage your subscription at any time from your account settings.</p>
{_cta("Manage my subscription", manage_url)}
{_footer()}'''
    return plain_text, get_base_template(content, "Reminder: your subscription renews soon")


# ── EMAIL #11 — Annual Subscription Renewed ──────────────────────────────────
# Subject: Renewal confirmed: [Mentor Name]'s Coaching Lounge

def get_annual_renewal_confirmed_template(name: str, mentor_name: str, amount: str, renewal_date: str, next_renewal_date: str, dashboard_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYour subscription to {mentor_name}'s Coaching Lounge has been successfully renewed.\n\nPlan: Annual\nAmount: {amount}\nRenewal date: {renewal_date}\nNext renewal: {next_renewal_date}\n\nAll the best,\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"Your subscription to <strong>{mentor_name}'s Coaching Lounge</strong> has been successfully renewed.")}
{_detail("Plan", "Annual")}
{_detail("Amount", amount)}
{_detail("Renewal date", renewal_date)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Next renewal:</strong> {next_renewal_date}</p>
{_p("Your access continues uninterrupted, so you can keep returning to this space whenever you need it.")}
{_cta("Go to dashboard", dashboard_url)}
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">This space is shaped by {mentor_name}'s perspective, designed to give you direct access to their thinking and guidance whenever you need it. Other key things to note:</p>
<ul style="margin:0 0 25px 0;padding-left:20px;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.8;"><li>You can manage or cancel your subscription at any time from your account settings.</li><li>You can also explore other Coaching Lounges available to you from your dashboard.</li></ul>
<p style="margin:0 0 5px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};">All the best,</p>
{_footer()}'''
    return plain_text, get_base_template(content, f"Renewal confirmed: {mentor_name}'s Coaching Lounge")


# ── EMAIL #12 — Payment Failed Day 0 ─────────────────────────────────────────
# Subject: We couldn't process your payment

def get_payment_failed_day0_template(name: str, mentor_name: str, plan_type: str, amount: str, update_payment_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe weren't able to process your recent payment for {mentor_name}'s Coaching Lounge.\n\nThis is usually due to something simple like an expired card or a temporary issue with your payment method.\n\nTo continue your access without interruption, please update your payment details.\n\nPlan: {plan_type}\nAmount: {amount}\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Update payment details</h1>
{_p(f"Hi {name},", bold=True)}
{_p(f"We weren't able to process your recent payment for <strong>{mentor_name}'s Coaching Lounge</strong>.")}
{_p("This is usually due to something simple like an expired card or a temporary issue with your payment method.")}
{_p("To continue your access without interruption, please update your payment details below:")}
{_cta("Update payment details", update_payment_url)}
{_detail("Plan", plan_type)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Amount:</strong> {amount}</p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">We'll retry the payment shortly, and your access will remain active in the meantime.</p>
{_contact()}
{_footer()}'''
    return plain_text, get_base_template(content, "We couldn't process your payment")


# ── EMAIL #13 — Payment Failed Day 3 ─────────────────────────────────────────
# Subject: Your payment still needs attention

def get_payment_failed_day3_template(name: str, mentor_name: str, plan_type: str, amount: str, update_payment_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe've been unable to process your payment for {mentor_name}'s Coaching Lounge, and your subscription still needs attention.\n\nPlan: {plan_type}\nAmount: {amount}\n\nWe'll make one final attempt to process the payment. If it's still unsuccessful, your access will be paused.\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Update payment details</h1>
{_p(f"Hi {name},", bold=True)}
{_p(f"We've been unable to process your payment for <strong>{mentor_name}'s Coaching Lounge</strong>, and your subscription still needs attention.")}
{_p("To avoid any interruption to your access, please update your payment details below:")}
{_cta("Update payment details", update_payment_url)}
{_detail("Plan", plan_type)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Amount:</strong> {amount}</p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">We'll make one final attempt to process the payment. If it's still unsuccessful, your access will be paused.</p>
{_contact()}
{_footer()}'''
    return plain_text, get_base_template(content, "Your payment still needs attention")


# ── EMAIL #14 — Access Paused (Day 7) ────────────────────────────────────────
# Subject: Access paused - update your payment to continue

def get_access_paused_template(name: str, data_deletion_date: str, update_payment_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWe weren't able to process your most recent payment for your Prompterly subscription, and after a couple of attempts, we've temporarily paused your account.\n\nWe'd love to have you back.\n\nTo reactivate your account, update your payment details.\n\nYour data deletion date is: {data_deletion_date}\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Access paused</h1>
{_p(f"Hi {name},", bold=True)}
{_p("We weren't able to process your most recent payment for your Prompterly subscription, and after a couple of attempts, we've temporarily paused your account.")}
{_p("We'd love to have you back.")}
{_p("To reactivate your account and pick up right where you left off, simply log in and update your payment details:")}
{_cta("Update payment details", update_payment_url)}
<p style="margin:0 0 10px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.6;"><strong><u>Please note:</u></strong></p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">Your data, including your chat history, notebook entries, and any time capsules, will be securely held for 90 days from today. If your account isn't reactivated within that window, your data will be permanently and irreversibly deleted from our system. If it is reactivated within this timeframe, you'll be able to pick up exactly where you left off, and everything in your account will still be there.</p>
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.6;"><strong>Your data deletion date is:</strong> {data_deletion_date}</p>
{_contact()}
{_footer()}'''
    return plain_text, get_base_template(content, "Access paused - update your payment to continue")


# ── EMAIL #15 — Data Deletion Reminder (60 days after pause) ─────────────────
# Subject: Your Prompterly data will be deleted in 30 days

def get_data_deletion_reminder_template(name: str, deletion_date: str, reactivate_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nThis is a quick but important note.\n\nYour Prompterly account was paused 60 days ago, and your data is scheduled for permanent deletion in 30 days on {deletion_date}.\n\nOnce deleted, this cannot be undone or recovered.\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Your data will soon be deleted</h1>
{_p(f"Hi {name},", bold=True)}
{_p("This is a quick but important note.")}
{_p(f"Your Prompterly account was paused 60 days ago, and your data, including your chat history, notebook entries, and time capsules, is scheduled for permanent deletion in 30 days on <strong>{deletion_date}</strong>.")}
{_p("Once deleted, this cannot be undone or recovered.")}
{_p("To reactivate your account, update your payment details below and pick up right where you left off.")}
{_cta("Reactivate account", reactivate_url)}
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you've decided Prompterly isn't for you right now, we completely understand. We just want to make sure you have the chance to keep anything that matters to you before it's gone.</p>
{_footer()}'''
    return plain_text, get_base_template(content, f"Your Prompterly data will be deleted in 30 days")


# ── EMAIL #16 — Data Deleted ─────────────────────────────────────────────────
# Subject: Your Prompterly data has been permanently deleted

def get_data_deleted_template(name: str, signup_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nAs previously notified, your Prompterly account data has now been permanently deleted from our system.\n\nThis includes your chat history, notebook entries, and time capsules. This cannot be undone or recovered.\n\nIf you'd like to start fresh, you can create a new account at {signup_url}\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">Your data has been deleted</h1>
{_p(f"Hi {name},", bold=True)}
{_p("As previously notified, your Prompterly account data has now been permanently deleted from our system.")}
{_p("This includes your chat history, notebook entries, and time capsules. This cannot be undone or recovered.")}
<p style="margin:0 0 15px 0;font-size:15px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you'd like to start fresh with Prompterly in the future, you're always welcome back. You can create a new account and subscribe to any Coaching Lounge at <a href="{signup_url}" style="color:{BRAND_COLORS["primary"]};">{signup_url}</a>.</p>
{_p("We hope Prompterly was valuable to you during your time with us, and we wish you well.")}
{_footer()}'''
    return plain_text, get_base_template(content, "Your Prompterly data has been permanently deleted")


# ── EMAIL #17 — Subscription Cancelled ───────────────────────────────────────
# Subject: You've unsubscribed from [Mentor Name]'s Coaching Lounge

def get_subscription_cancellation_email_template(name: str, mentor_name: str, plan_type: str, access_end_date: str, deletion_date: str, dashboard_url: str) -> tuple[str, str]:
    if plan_type.lower() == "monthly":
        access_msg = f"Your access will remain active until {access_end_date}, after which your subscription will not renew."
    else:
        access_msg = f"You still have time left on your billing cycle, so your access to {mentor_name}'s Coaching Lounge will remain active until {access_end_date}. After that date, your subscription will not renew."
    plain_text = f"Hi {name},\n\nYou've successfully unsubscribed from {mentor_name}'s Coaching Lounge.\n\n{access_msg}\n\nYour data will be permanently deleted 30 days after your access ends, on {deletion_date}.\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">You have unsubscribed</h1>
{_p(f"Hi {name},", bold=True)}
{_p(f"You've successfully unsubscribed from <strong>{mentor_name}'s Coaching Lounge</strong>.")}
{_p(access_msg)}
<p style="margin:0 0 10px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.6;"><strong><u>A note on your data:</u></strong></p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">Your chat history, notebook entries, and time capsules associated with {mentor_name}'s Coaching Lounge will be permanently deleted 30 days after your access ends, on <strong>{deletion_date}</strong>. This cannot be undone or recovered.</p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you'd like to save anything before then, you can export your data in your user settings.</p>
<p style="margin:0 0 15px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">Where applicable, your other Coaching Lounges are unaffected and remain active as usual.</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">If you unsubscribed by mistake or change your mind, you can resubscribe to {mentor_name}'s Coaching Lounge at any time here: <a href="{dashboard_url}" style="color:{BRAND_COLORS["primary"]};">dashboard</a>.</p>
{_footer()}'''
    return plain_text, get_base_template(content, f"You've unsubscribed from {mentor_name}'s Coaching Lounge")


# ── EMAIL #18 — Time Capsule Delivery ────────────────────────────────────────
# Subject: A new message is ready

def get_time_capsule_delivery_template(name: str, login_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nA new time capsule message has been unlocked and ready for viewing.\n\nYou left something here for yourself, and now it's time to take a look.\n\nSign in: {login_url}\n\nPrompterly Support"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">New time capsule message unlocked</h1>
{_p(f"Hi {name},", bold=True)}
{_p("A new time capsule message has been unlocked and ready for viewing.")}
{_p("You left something here for yourself, and now it's time to take a look.")}
{_cta("Sign in to Prompterly", login_url)}
{_footer()}'''
    return plain_text, get_base_template(content, "A new message is ready")


# ── NON-PDF TEMPLATES — Admin/Internal ───────────────────────────────────────

def get_user_credentials_email_template(name: str, email: str, password: str, login_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nAn account has been created for you on Prompterly.\n\nEmail: {email}\nTemporary Password: {password}\n\nPlease login at: {login_url}\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("An account has been created for you on Prompterly.")}
{_detail("Email", email)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Temporary Password:</strong> {password}</p>
<p style="margin:0 0 25px 0;font-size:14px;color:{BRAND_COLORS["text_secondary"]};line-height:1.6;">For security, we recommend changing your password after your first login.</p>
{_cta("Log in to Prompterly", login_url)}
{_footer()}'''
    return plain_text, get_base_template(content, "Welcome to Prompterly - Your Account Credentials")


def get_mentor_welcome_email_template(name: str, prompterly_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nWelcome to Prompterly! You've been added as a mentor on our platform.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p("Welcome to Prompterly! You've been added as a mentor on our platform.")}
{_p("Your expertise will be used to power a Coaching Lounge, giving users direct access to your thinking, frameworks, and guidance through AI.")}
{_cta("Visit Prompterly", prompterly_url)}
{_footer()}'''
    return plain_text, get_base_template(content, "Welcome to Prompterly - You're Now a Mentor!")


def get_contact_confirmation_email_template(name: str, subject: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nThank you for reaching out. We've received your message regarding \"{subject}\" and will get back to you shortly.\n\nPrompterly Support"
    msg = f"Thank you for reaching out. We've received your message regarding <strong>\"{subject}\"</strong> and will get back to you shortly."
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(msg)}
{_footer()}'''
    return plain_text, get_base_template(content, "We've received your message")


def get_contact_admin_notification_template(name: str, email: str, subject: str, message: str, ip_address: str, submitted_at: str, message_id: str) -> tuple[str, str]:
    plain_text = f"New contact form submission:\n\nFrom: {name} ({email})\nSubject: {subject}\nMessage: {message}\n\nIP: {ip_address}\nTime: {submitted_at}\nID: {message_id}"
    content = f'''<h1 style="margin:0 0 20px 0;font-size:22px;font-weight:700;color:{BRAND_COLORS["text_primary"]};">New Contact Form Submission</h1>
{_detail("From", f"{name} ({email})")}
{_detail("Subject", subject)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Message:</strong> {message}</p>
<hr style="border:none;border-top:1px solid {BRAND_COLORS["border"]};margin:15px 0;">
<p style="margin:0;font-size:12px;color:{BRAND_COLORS["text_muted"]};line-height:1.8;">IP: {ip_address} | Time: {submitted_at} | ID: {message_id}</p>'''
    return plain_text, get_base_template(content, f"New contact: {subject} from {name}")


# ── Legacy compatibility aliases ─────────────────────────────────────────────

def get_subscription_expiry_warning_email_template(name: str, plan_name: str, expiry_date: str, days_remaining: int, renewal_url: str, amount: Optional[str] = None) -> tuple[str, str]:
    return get_annual_renewal_7day_template(name=name, mentor_name=plan_name, renewal_date=expiry_date, amount=amount or "", manage_url=renewal_url)


def get_subscription_upgrade_email_template(name: str, old_plan: str, new_plan: str, amount: str, savings: str, next_billing_date: str, dashboard_url: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYour plan has been upgraded from {old_plan} to {new_plan}.\n\nNew amount: {amount}\nSavings: {savings}\nNext billing: {next_billing_date}\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"Your plan has been upgraded from <strong>{old_plan}</strong> to <strong>{new_plan}</strong>.")}
{_detail("New amount", amount)}
{_detail("Savings", savings)}
<p style="margin:0 0 20px 0;font-size:14px;color:{BRAND_COLORS["text_primary"]};line-height:1.8;"><strong>Next billing:</strong> {next_billing_date}</p>
{_cta("Go to dashboard", dashboard_url)}
{_footer()}'''
    return plain_text, get_base_template(content, f"Plan upgraded to {new_plan}")


def get_payment_method_update_email_template(name: str, card_last_four: str, card_brand: str, updated_at: str) -> tuple[str, str]:
    plain_text = f"Hi {name},\n\nYour payment method has been updated to {card_brand} ending in {card_last_four}.\n\nUpdated on {updated_at}.\n\nPrompterly Support"
    content = f'''{_p(f"Hi {name},", bold=True)}
{_p(f"Your payment method has been updated to <strong>{card_brand} ending in {card_last_four}</strong>.")}
<p style="margin:0 0 25px 0;font-size:13px;color:{BRAND_COLORS["text_muted"]};">Updated on {updated_at}</p>
<p style="margin:0;font-size:13px;color:{BRAND_COLORS["text_muted"]};line-height:1.6;">If you didn't make this change, please contact <a href="mailto:support@prompterly.ai" style="color:{BRAND_COLORS["primary"]};">support@prompterly.ai</a> immediately.</p>
{_footer()}'''
    return plain_text, get_base_template(content, f"Payment method updated to {card_brand} ending in {card_last_four}")
