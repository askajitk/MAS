from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                'The password must contain at least 8 characters.',
                code='password_too_short',
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'The password must contain at least one uppercase letter.',
                code='password_no_upper',
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                'The password must contain at least one number.',
                code='password_no_number',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                'The password must contain at least one symbol (!@#$%^&*(),.?":{}|<>).',
                code='password_no_symbol',
            )

    def get_help_text(self):
        return "" # Empty since we show requirements in the UI