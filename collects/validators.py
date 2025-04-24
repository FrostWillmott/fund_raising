from django.core.files.uploadedfile import UploadedFile
from rest_framework.exceptions import ValidationError


def validate_file_size(value: UploadedFile) -> UploadedFile:
    if value.size > 2 * 1024 * 1024:
        raise ValidationError("The maximum file size that can be uploaded is 2MB")
    return value
