from django.contrib import admin
from .models import PromotionPrompt

@admin.register(PromotionPrompt)
class PromotionPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'minio_object_key', 'created_at')
    search_fields = ('id', 'minio_object_key')
    readonly_fields = ('id', 'created_at', 'updated_at')
