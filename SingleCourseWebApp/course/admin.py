from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUserModel, Course, Enrollment,
    Module, Lesson, Submission, StudentProfile,
    InstructorProfile, Exercise, Group
)

# Register your models here.
class UserAdminCustom(UserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_instructor",
                    "is_student",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2"),},
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff", "is_instructor", "is_student")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)
    readonly_fields = ['date_joined', 'last_login']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at', 'difficulty_level')
    list_filter = ('difficulty_level', 'created_at', 'instructor')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'


admin.site.register(Enrollment)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Exercise)
admin.site.register(Group)
admin.site.register(Submission)
admin.site.register(StudentProfile)
admin.site.register(InstructorProfile)
admin.site.register(CustomUserModel)
