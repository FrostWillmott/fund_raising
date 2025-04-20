from rest_framework.exceptions import ValidationError


def validate_file_size(value):
    if value.size > 2 * 1024 * 1024:  # 2MB limit
        raise ValidationError("The maximum file size that can be uploaded is 2MB")
    return value
