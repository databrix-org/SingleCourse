from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.conf import settings
from .models import Course, Enrollment, LessonProgress, Lesson, Exercise, Group, Module
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.core.files.base import ContentFile

def require_enrollment_and_group(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Extract course_id from kwargs, or from lesson_id if present
        course_id = kwargs.get('course_id')
        if not course_id and 'lesson_id' in kwargs:
            lesson = get_object_or_404(Lesson, id=kwargs['lesson_id'])
            course_id = lesson.module.course.id
            
        course = get_object_or_404(Course, id=course_id)
        
        # Check enrollment
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('course:home')
            
        # Check group membership
        if not Group.objects.filter(course=course, members=request.user).exists():
            return redirect('course:home')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def home(request):
    course = Course.objects.first()
    if not course:
        return render(request, 'course/course_not_published.html')
    is_enrolled = False
    user_group = None
    available_groups = []
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user).exists()
        user_group = Group.objects.filter(course=course, members=request.user).first()

        # Get available groups (not full and user not already in them)
        if is_enrolled and not user_group:
            available_groups = Group.objects.filter(course=course)\
                .annotate(member_count=models.Count('members'))\
                .filter(member_count__lt=course.max_members)\
                .exclude(members=request.user)
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'user_group': user_group,
        'available_groups': available_groups,
    }
    return render(request, 'course/home.html', context)

@login_required
def course_enroll(request, course_id):
    course = Course.objects.get(id=course_id)
    if request.method == 'POST':
        Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        return redirect('course:home')
    return redirect('course:home')

def dev_login(request):
    if not settings.DEBUG:
        return redirect('course:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('course:home')
    return render(request, 'course/dev_login.html')

@login_required
@require_enrollment_and_group
def course_overview(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if course is published or user is instructor
    if not course.is_published and not request.user.is_instructor:
        return render(request, 'course/course_not_published.html')
    
    # Get all modules with their lessons, ordered by their respective order fields
    modules = course.modules.prefetch_related('lessons').all()
    
    # Get the user's progress for all lessons in the course
    lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=course
    ).select_related('lesson')
    
    # Create a progress lookup dictionary for quick access
    progress_lookup = {
        progress.lesson_id: progress 
        for progress in lesson_progress
    }
    
    # Prepare module data with lessons and progress
    modules_data = []
    for module in modules:
        lessons_data = [{
            'lesson': lesson,
            'progress': progress_lookup.get(lesson.id)
        } for lesson in module.lessons.all()]
        
        modules_data.append({
            'module': module,
            'lessons': lessons_data
        })

    # Calculate total and completed lessons
    total_lessons = sum(len(module.lessons.all()) for module in modules)
    completed_lessons = len([p for p in lesson_progress if p.is_completed])
    
    # Update debug data to include the counts
    debug_data = {
        'course_title': course.title,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'modules': [{
            'title': module_data['module'].title,
            'lessons': [{
                'title': lesson_data['lesson'].title,
                'id': lesson_data['lesson'].id,
                'order': lesson_data['lesson'].order,
                'duration': lesson_data['lesson'].duration,
                'is_completed': bool(lesson_data['progress'] and lesson_data['progress'].is_completed)
            } for lesson_data in module_data['lessons']]
        } for module_data in modules_data]
    }
    
    # Find the first incomplete lesson
    first_incomplete_lesson = None
    for module in modules:
        for lesson in module.lessons.all():
            if lesson.id not in progress_lookup or not progress_lookup[lesson.id].is_completed:
                first_incomplete_lesson = lesson
                break
        if first_incomplete_lesson:
            break
    
    # If all lessons are complete, use the last lesson
    if not first_incomplete_lesson and modules:
        last_module = modules.last()
        if last_module:
            first_incomplete_lesson = last_module.lessons.last()

    context = {
        'course_title': course.title,
        'modules_data': modules_data,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'debug_data_json': json.dumps(debug_data, cls=DjangoJSONEncoder),
        'continue_lesson': first_incomplete_lesson,
    }
    return render(request, 'course/learn.html', context)

@login_required
@require_enrollment_and_group
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    
    # Check if course is published or user is instructor
    if not course.is_published and not request.user.is_instructor:
        return render(request, 'course/course_not_published.html')
    
    # Get or create progress for this lesson
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )
    
    # Get all modules with their lessons, ordered by their respective order fields
    modules = course.modules.prefetch_related('lessons').all()
    
    # Get the user's progress for all lessons in the course
    lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=course
    ).select_related('lesson')
    
    # Create a progress lookup dictionary for quick access
    progress_lookup = {
        progress.lesson_id: progress 
        for progress in lesson_progress
    }
    
    # Prepare module data with lessons and progress
    modules_data = []
    for module in modules:
        lessons_data = [{
            'lesson_title': lesson.title,
            'lesson_id': lesson.id,
            'progress': progress_lookup.get(lesson.id)
        } for lesson in module.lessons.all()]
        
        modules_data.append({
            'module': module,
            'lessons': lessons_data
        })
    
    # Base response data
    response_data = {
        'lesson_id': lesson.id,
        'title': lesson.title,
        'lesson_type': lesson.lesson_type,
        'progress': progress,
        'modules_data': modules_data
    }
    
    # Add type-specific content
    if lesson.lesson_type == 'reading':
        response_data['lesson_content'] = lesson.lesson_content
    elif lesson.lesson_type == 'video':
        response_data['video_url'] = lesson.video_file.url if lesson.video_file else None
    elif lesson.lesson_type == 'exercise':
        # Get the exercise object
        exercise = lesson.lesson_exercise
        response_data.update({
            'lesson_content': lesson.lesson_content,
            'exercise': exercise,
        })
    
    # Add MEDIA_URL to the context
    response_data['MEDIA_URL'] = settings.MEDIA_URL
    
    return render(request, 'course/lesson_base.html', response_data)

@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )[0]
    
    # Toggle the completion status
    progress.is_completed = not progress.is_completed
    progress.save()
    
    # Only find next lesson if we're marking as complete
    next_lesson_id = None
    if progress.is_completed:
        # Find the next lesson
        current_module = lesson.module
        current_course = current_module.course
        
        # Try to get next lesson in the same module
        next_lesson = Lesson.objects.filter(
            module=current_module,
            order__gt=lesson.order
        ).order_by('order').first()
        
        # If no next lesson in current module, try first lesson of next module
        if not next_lesson:
            next_module = current_course.modules.filter(
                order__gt=current_module.order
            ).order_by('order').first()
            
            if next_module:
                next_lesson = next_module.lessons.order_by('order').first()
            else:
                next_lesson = lesson
        
        next_lesson_id = next_lesson.id if next_lesson else None
    else:
        next_lesson_id = lesson_id
    return JsonResponse({
        'success': True,
        'is_completed': progress.is_completed,
        'next_lesson_id': next_lesson_id
    })

@login_required
def create_group(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Check if user is already in a group for this course
        if Group.objects.filter(course=course, members=request.user).exists():
            messages.error(request, 'You are already in a group for this course')
            return redirect('course:home')
            
        # Check if user is enrolled
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.error(request, 'You must be enrolled in the course to create a group')
            return redirect('course:home')
            
        # Create group without any members first
        group = Group.objects.create(course=course)
        
        try:
            # Add the creator as the first member
            group.members.add(request.user)
            group.save()  # This will trigger validation
        except ValidationError as e:
            # If validation fails, delete the group and show error
            group.delete()
            messages.error(request, str(e))
            return redirect('course:home')
        
        messages.success(request, 'Group created successfully')
        return redirect('course:home')
    
    return redirect('course:home')

@login_required
def join_group(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            
            # Check if group is not full
            if group.members.count() < course.max_members:
                group.members.add(request.user)
                group.save()
    
    return redirect('course:home')

@login_required
def manage_course(request):
    # Only allow instructors to access this page
    if not request.user.is_instructor:
        raise PermissionDenied
    
    # Get the course (since your model only allows one course)
    course = Course.objects.first()
    
    if not course:
        # Handle case where no course exists
        course = Course.objects.create(
            title="New Course",
            description="Course description",
            instructor=request.user
        )
    
    context = {
        'course': course,
        'modules': course.modules.prefetch_related('lessons').all().order_by('order'),
    }
    
    return render(request, 'course/ManageCourse_base.html', context)

@login_required
@require_POST
def update_overview(request):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    data = json.loads(request.body)
    field = data.get('field')
    value = data.get('value')
    
    course = Course.objects.first()
    if field in ['title', 'description', 'difficulty_level', 'max_members']:
        if field == 'difficulty_level' or field == 'max_members':
            value = int(value)
        setattr(course, field, value)
        course.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
@require_POST
def create_module(request):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    course = Course.objects.first()
    # Get the highest order number and add 1
    last_order = course.modules.aggregate(models.Max('order'))['order__max'] or 0
    
    module = Module.objects.create(
        course=course,
        title="New Module",
        order=last_order + 1
    )
    
    return JsonResponse({
        'success': True,
        'module_id': module.id,
        'module_title': module.title
    })

@login_required
@require_POST
def delete_module(request, module_id):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    module = get_object_or_404(Module, id=module_id)
    module.delete()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(['GET', 'POST'])
def edit_module(request, module_id):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    module = get_object_or_404(Module, id=module_id)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        module.title = data.get('title')
        module.description = data.get('description')
        module.save()
        return JsonResponse({'success': True})
    
    return render(request, 'course/EditModule.html', {'module': module})

@login_required
@require_http_methods(['GET'])
def get_lesson(request, lesson_id):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return JsonResponse({
        'id': lesson.id,
        'title': lesson.title,
        'lesson_type': lesson.lesson_type,
        'lesson_content': lesson.lesson_content,
        'duration': str(lesson.duration),
        'video_file': lesson.video_file.url if lesson.video_file else None,
    })

@login_required
@require_POST
def create_lesson(request, module_id):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    module = get_object_or_404(Module, id=module_id)
    last_order = module.lessons.aggregate(models.Max('order'))['order__max'] or 0
    
    lesson = Lesson.objects.create(
        module=module,
        title="New Lesson",
        order=last_order + 1,
        lesson_type='reading'
    )
    
    return JsonResponse({
        'success': True,
        'lesson_id': lesson.id,
        'lesson_title': lesson.title,
        'lesson_type': lesson.lesson_type
    })

@login_required
@require_POST
def delete_lesson(request, lesson_id):
    if not request.user.is_instructor:
        raise PermissionDenied
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    lesson.delete()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(['POST'])
def save_lesson(request, lesson_id):
    """
    Endpoint to save changes to a lesson.
    Handles both JSON payload and file uploads.
    """
    if not request.user.is_instructor:
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id)

    try:
        # Check if the request is multipart (contains files)
        if request.content_type and 'multipart/form-data' in request.content_type:
            title = request.POST.get('title')
            lesson_type = request.POST.get('lesson_type')
            
            if 'video_file' in request.FILES:
                # Delete old video file if it exists
                if lesson.video_file:
                    lesson.video_file.delete(save=False)
                # Save new video file
                lesson.video_file = request.FILES['video_file']
            
            lesson.title = title
            lesson.lesson_type = lesson_type
            lesson.lesson_content = ''  # Clear content for video lessons
            lesson.save()
            
            return JsonResponse({'success': True})
        else:
            # Handle JSON data
            data = json.loads(request.body)
            title = data.get('title')
            lesson_type = data.get('lesson_type')
            content = data.get('content')

            if not title or not lesson_type:
                return JsonResponse({'success': False, 'error': 'Title and lesson type are required.'}, status=400)

            lesson.title = title
            lesson.lesson_type = lesson_type
            lesson.lesson_content = content if lesson_type == 'reading' else ''
            
            # Clear video file if switching to non-video type
            if lesson_type != 'video' and lesson.video_file:
                lesson.video_file.delete(save=False)
                lesson.video_file = None

            lesson.save()
            return JsonResponse({'success': True})

    except Exception as e:
        # Log the error for debugging
        print(f"Error saving lesson: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
@csrf_exempt
def toggle_publish(request):
    if not request.user.is_instructor:
        raise PermissionDenied

    course = Course.objects.first()
    course.is_published = not course.is_published
    course.save()

    return JsonResponse({'success': True, 'is_published': course.is_published})

@login_required
def search_group(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        if group.members.count() < group.course.max_members:
            group_data = {
                'id': group.id,
                'members': [{'first_name': member.first_name, 'last_name': member.last_name} for member in group.members.all()],
                'max_members': group.course.max_members
            }
            return JsonResponse({'success': True, 'group': group_data})
        else:
            return JsonResponse({'success': False, 'message': 'Group is full'})
    except Group.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Group not found'})
