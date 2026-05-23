import re
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
phone_regex = re.compile(r"^(?:\+?998)?(?:12|20|22|25|33|50|51|55|70|71|75|77|79|88|90|91|93|94|95|96|97|98|99)\d{7}$")


def check_email_or_phone(email_or_phone):
    cleaned_input = email_or_phone.strip().lower()

    if re.fullmatch(email_regex, cleaned_input):
        return 'email', cleaned_input

    if re.fullmatch(phone_regex, cleaned_input):
        if not cleaned_input.startswith('+998'):
            if cleaned_input.startswith('998'):
                cleaned_input = f"+{cleaned_input}"

            else:
                cleaned_input = f"+998{cleaned_input}"

        return 'phone', cleaned_input

    raise ValidationError({"email_or_phone": "Email yoki telefon raqami noto'g'ri kiritildi!"})
