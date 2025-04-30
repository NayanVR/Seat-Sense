import os

import resend
from jinja2 import Template

from app.config import settings

resend.api_key = settings.resend_api_key

def read_template(template_path: str) -> str:
    with open(template_path, "r") as file:
        return file.read()

template_path = os.path.join(os.path.dirname(__file__), "../templates/verification_otp.html")
template_content = read_template(template_path)

def send_otp_verification_email(email: str, otp: str) -> None:
    # Use Jinja2 to render the template
    template = Template(template_content)
    formatted_template = template.render(otp=otp)

    r = resend.Emails.send({
        "from": "Seat Sense <seat-sense@mail.nayanvr.in>",
        "to": email,
        "subject": "Your Email Verification Code",
        "html": formatted_template
    })