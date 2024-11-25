from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import (
    CustomUserModel, Course, Enrollment, Module, 
    Lesson, Exercise, Group, Submission, LessonProgress
)

class CustomUserModelTests(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        self.user = CustomUserModel.objects.create_user(**self.user_data)

    def test_create_user(self):
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.is_student)
        self.assertFalse(self.user.is_instructor)

class CourseModelTests(TestCase):
    def setUp(self):
        self.instructor = CustomUserModel.objects.create_user(
            email='instructor@example.com',
            first_name='Test',
            last_name='Instructor',
            password='testpass123',
            is_instructor=True
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            instructor=self.instructor,
            difficulty_level=1
        )

    def test_course_creation(self):
        self.assertEqual(str(self.course), 'Test Course')
        self.assertEqual(self.course.difficulty_level, 1)
        self.assertFalse(self.course.is_published)

class EnrollmentTests(TestCase):
    def setUp(self):
        self.student = CustomUserModel.objects.create_user(
            email='student@example.com',
            first_name='Test',
            last_name='Student',
            password='testpass123'
        )
        self.instructor = CustomUserModel.objects.create_user(
            email='instructor@example.com',
            first_name='Test',
            last_name='Instructor',
            password='testpass123',
            is_instructor=True
        )
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.instructor
        )

    def test_enrollment_creation(self):
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        self.assertEqual(enrollment.progress, 0.0)
        self.assertEqual(
            str(enrollment),
            f"{self.student.first_name} enrolled in {self.course.title}"
        )

class ExerciseAndGroupTests(TestCase):
    def setUp(self):
        # Create basic course structure
        self.instructor = CustomUserModel.objects.create_user(
            email='instructor@example.com',
            first_name='Test',
            last_name='Instructor',
            password='testpass123',
            is_instructor=True
        )
        self.student1 = CustomUserModel.objects.create_user(
            email='student1@example.com',
            first_name='Student',
            last_name='One',
            password='testpass123'
        )
        self.student2 = CustomUserModel.objects.create_user(
            email='student2@example.com',
            first_name='Student',
            last_name='Two',
            password='testpass123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.instructor
        )
        self.module = Module.objects.create(
            course=self.course,
            title='Test Module',
            order=1
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Test Lesson',
            order=1
        )
        self.exercise = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type='programming',
            max_members=2
        )
        # Create enrollments
        Enrollment.objects.create(student=self.student1, course=self.course)
        Enrollment.objects.create(student=self.student2, course=self.course)

    def test_group_member_limit(self):
        group = Group.objects.create(exercise=self.exercise)
        group.members.add(self.student1)
        group.members.add(self.student2)
        
        # Try to add a third student
        student3 = CustomUserModel.objects.create_user(
            email='student3@example.com',
            first_name='Student',
            last_name='Three',
            password='testpass123'
        )
        Enrollment.objects.create(student=student3, course=self.course)
        
        with self.assertRaises(ValidationError):
            group.members.add(student3)
            group.clean()

class LessonProgressTests(TestCase):
    def setUp(self):
        self.student = CustomUserModel.objects.create_user(
            email='student@example.com',
            first_name='Test',
            last_name='Student',
            password='testpass123'
        )
        self.instructor = CustomUserModel.objects.create_user(
            email='instructor@example.com',
            first_name='Test',
            last_name='Instructor',
            password='testpass123',
            is_instructor=True
        )
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.instructor
        )
        self.module = Module.objects.create(
            course=self.course,
            title='Test Module',
            order=1
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Test Lesson',
            order=1,
            duration=timedelta(minutes=30)
        )

    def test_lesson_progress_tracking(self):
        progress = LessonProgress.objects.create(
            student=self.student,
            lesson=self.lesson
        )
        self.assertFalse(progress.is_completed)
        self.assertEqual(progress.time_spent, timedelta(minutes=0))
