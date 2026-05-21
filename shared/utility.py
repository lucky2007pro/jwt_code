import re
from rest_framework.exceptions import ValidationError
from rest_framework import status


email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
phone_regex = re.compile(r"^(?:\+998)?(90|91|93|94|95|97|98|99|77|88|20|33)\d{7}$")

def check_email_or_phone(email_or_phone):
    if re.fullmatch(email_regex, email_or_phone):
        result = 'email'

    elif re.fullmatch(phone_regex, email_or_phone):
        result = 'phone'

    else:
        raise ValidationError(
            detail='Email yoki telefon raqami noto\'g\'ri formatda kiritildi.',
            code=status.HTTP_400_BAD_REQUEST,
        )
    return result