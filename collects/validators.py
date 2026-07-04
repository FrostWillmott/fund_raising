from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_file_size(value: UploadedFile) -> UploadedFile:
    if value.size is not None and value.size > 2 * 1024 * 1024:
        raise ValidationError(
            "The maximum file size that can be uploaded is 2MB"
        )
    return value
