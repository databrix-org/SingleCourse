from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from datetime import timedelta
from django.core.exceptions import ValidationError

# Create your models here.
class CustomUserModel(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("Email Address"), unique=True, max_length=255)
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    username = models.CharField(_("Username"), max_length=255, unique=True)  # Added for Shibboleth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_instructor = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['first_name', 'last_name','is_instructor','is_student','is_staff']),
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name


# Profile Models (Optional)
class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUserModel, on_delete=models.CASCADE, related_name='student_profile')
    # Additional student-specific fields

class InstructorProfile(models.Model):
    user = models.OneToOneField(CustomUserModel, on_delete=models.CASCADE, related_name='instructor_profile')
    # Additional instructor-specific fields

# Course Model
class Course(models.Model):
    DIFFICULTY_CHOICES = (
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Professional'),
    )
    title = models.CharField(max_length=255, default="Untitled Course")
    description = models.TextField(default="No description")
    instructor = models.ForeignKey(
        CustomUserModel, on_delete=models.CASCADE, related_name='courses',
        limit_choices_to={'is_instructor': True},
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    difficulty_level = models.IntegerField(
        choices=DIFFICULTY_CHOICES,
        default=1,
        help_text="Course difficulty level"
    )
    is_published = models.BooleanField(default=False)
    # Additional fields

    def __str__(self):
        return self.title

# Enrollment Model
class Enrollment(models.Model):
    student = models.ForeignKey(
        CustomUserModel, on_delete=models.CASCADE, related_name='enrollments',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.first_name} enrolled in {self.course.title}"


# Module Model
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.course.title})"


# Lesson Model
class Lesson(models.Model):
    LESSON_TYPES = (
        ('video', 'Video Lesson'),
        ('reading', 'Reading Material'),
        ('exercise', 'Exercise'),
    )
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPES,
        default='reading',
        help_text="Type of lesson content"
    )
    duration = models.DurationField(default=timedelta(minutes=10), help_text="Expected time to complete this lesson")
    video_file = models.FileField(
        upload_to='lesson_videos/',
        blank=True,
        null=True,
        help_text="Upload video content for the lesson"
    )
    lesson_content = models.TextField(blank=True, null=True, help_text="Main lesson content/text material")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.module.title})"

class Exercise(models.Model):
    EXERCISE_TYPES = (
        ('programming', 'Programming Exercise'),
        ('traditional', 'Traditional Exercise'),
    )
    lesson = models.OneToOneField(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='lesson_exercise'
    )
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPES,
        default='traditional',
        help_text="Type of exercise"
    )
    max_members = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of students allowed in a group (for group exercises)",
    )
    jupyterhub_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL for JupyterHub notebook (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['lesson', 'exercise_type']),
        ]

    def __str__(self):
        return f"{self.lesson.title} ({self.get_exercise_type_display()})"

class Group(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='groups')
    members = models.ManyToManyField(
        CustomUserModel,
        related_name='exercise_groups',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['exercise']),
        ]

    def __str__(self):
        return f"Group for {self.exercise.name}"

    def clean(self):
        if self.exercise.max_members and self.members.count() > self.exercise.max_members:
            raise ValidationError(
                f'Group cannot have more than {self.exercise.max_members} members'
            )
        
        course = self.exercise.lesson.module.course
        for member in self.members.all():
            existing_group = Group.objects.filter(
                exercise=self.exercise,
                members=member
            ).exclude(pk=self.pk).first()
            
            if existing_group:
                raise ValidationError(
                    f'User {member.get_full_name()} is already in another group for this exercise'
                )
            
            if not course.enrollments.filter(student=member).exists():
                raise ValidationError(
                    f'Student {member.get_full_name()} is not enrolled in the course'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# Submission Model
class Submission(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    submission_file = models.FileField(
        upload_to='exercise_submissions/',
        help_text="The submitted file from the student"
    )

    def __str__(self):
        return f"{self.student.get_full_name()}'s submission for {self.exercise.lesson.title}"


# Lesson Progress Model
class LessonProgress(models.Model):
    student = models.ForeignKey(
        CustomUserModel, 
        on_delete=models.CASCADE, 
        related_name='lesson_progress',
    )
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='student_progress'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.DurationField(default=timedelta(minutes=0))

    class Meta:
        unique_together = ('student', 'lesson')
        indexes = [
            models.Index(fields=['student', 'lesson']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.lesson.title} Progress"