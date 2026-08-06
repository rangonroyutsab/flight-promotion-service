import uuid
from django.db import models

class PromotionPrompt(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    prompt_text = models.TextField()
    minio_object_key = models.CharField(
        max_length=1024,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.minio_object_key}"
