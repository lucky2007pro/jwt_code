from django.contrib import admin
from .models import Review, ReviewImage, ReviewReply


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0


class ReviewReplyInline(admin.StackedInline):
    model = ReviewReply
    extra = 0
    readonly_fields = ['user', 'created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']
    list_editable = ['is_approved']
    inlines = [ReviewImageInline, ReviewReplyInline]
    ordering = ['-created_at']
