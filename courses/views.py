from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Prefetch
from django.core.signing import Signer
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from core.permissions import MODULE_PERMISSIONS, module_required

from .models import (
    Course, Enrollment, Module, Lesson, Quiz, Question,
    QuestionOption, QuizQuestion, StudentProgress, QuizAttempt, StudentAnswer,
    Turma, PresenceSession, PresenceRecord
)
from .permissions import ALUNO, PROFESSOR, require_presence_role


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def my_courses_view(request):
    """Display user's enrolled courses."""
    search_query = request.GET.get('search', '')
    
    # Get user's enrolled courses
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    courses = [enrollment.course for enrollment in enrollments]
    
    # Apply search filter
    if search_query:
        courses = [c for c in courses if search_query.lower() in c.name.lower()]
    
    return render(request, 'courses/my_courses.html', {
        'courses': courses,
        'search_query': search_query
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def acquire_courses_view(request):
    """Display available courses for purchase."""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '')
    
    # Get user's enrolled course IDs
    enrolled_course_ids = Enrollment.objects.filter(
        user=request.user
    ).values_list('course_id', flat=True)
    
    # Get available courses (active and not enrolled)
    courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)
    
    # Apply search filter
    if search_query:
        courses = courses.filter(name__icontains=search_query)
    
    # Apply sorting
    if sort_by == 'price_asc':
        courses = courses.order_by('price')
    elif sort_by == 'price_desc':
        courses = courses.order_by('-price')
    else:
        courses = courses.order_by('-created_at')
    
    return render(request, 'courses/acquire_courses.html', {
        'courses': courses,
        'search_query': search_query,
        'sort_by': sort_by
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def course_redirect_view(request, course_id):
    """Redirect to internal course player."""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Você precisa estar matriculado neste curso.')
        return redirect('acquire_courses')
    
    # Redirect to course detail view
    return redirect('course_detail', course_id=course.id)


# ============================================================================
# COURSE CONTENT VIEWS
# ============================================================================

@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def course_detail_view(request, course_id):
    """Display course structure with modules and progress."""
    course = get_object_or_404(Course, id=course_id)
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Você não está matriculado neste curso.')
        return redirect('acquire_courses')
    
    # Get modules with lessons and quizzes
    modules = Module.objects.filter(
        course=course,
        is_published=True
    ).prefetch_related(
        Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True).order_by('order')),
        Prefetch('quizzes', queryset=Quiz.objects.filter(is_published=True).order_by('order'))
    ).order_by('order')
    
    # Get user progress
    lesson_progress = StudentProgress.objects.filter(
        user=request.user,
        lesson__module__course=course,
        completed=True
    ).values_list('lesson_id', flat=True)
    
    quiz_progress = StudentProgress.objects.filter(
        user=request.user,
        quiz__module__course=course,
        completed=True
    ).values_list('quiz_id', flat=True)
    
    # Calculate overall progress
    total_items = sum(m.lessons.count() + m.quizzes.count() for m in modules)
    completed_items = len(lesson_progress) + len(quiz_progress)
    progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'lesson_progress': list(lesson_progress),
        'quiz_progress': list(quiz_progress),
        'progress_percentage': round(progress_percentage, 1),
        'completed_items': completed_items,
        'total_items': total_items
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def lesson_view(request, lesson_id):
    """Display lesson content."""
    lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
    course = lesson.module.course
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Você não está matriculado neste curso.')
        return redirect('my_courses')
    
    # Get or create progress
    progress, created = StudentProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': False}
    )
    
    # Mark as complete if requested
    if request.method == 'POST' and request.POST.get('action') == 'complete':
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()
            messages.success(request, 'Lição concluída!')
        return redirect('lesson_view', lesson_id=lesson.id)
    
    # Get navigation (previous/next lessons in module)
    module_lessons = list(lesson.module.lessons.filter(is_published=True).order_by('order'))
    current_index = module_lessons.index(lesson)
    previous_lesson = module_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = module_lessons[current_index + 1] if current_index < len(module_lessons) - 1 else None
    
    return render(request, 'courses/lesson.html', {
        'lesson': lesson,
        'course': course,
        'module': lesson.module,
        'progress': progress,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def quiz_view(request, quiz_id):
    """Display quiz and handle attempts."""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    course = quiz.module.course
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Você não está matriculado neste curso.')
        return redirect('my_courses')
    
    # Get previous attempts
    attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    ).order_by('-attempt_number')
    
    attempts_count = attempts.count()
    best_score = attempts.filter(passed=True).first()
    passed_attempt = attempts.filter(passed=True).count() > 0
    can_attempt = attempts_count < quiz.max_attempts and not passed_attempt
    
    # Get quiz questions
    quiz_questions = QuizQuestion.objects.filter(
        quiz=quiz
    ).select_related('question').prefetch_related(
        'question__options'
    ).order_by('order')
    
    return render(request, 'courses/quiz.html', {
        'quiz': quiz,
        'course': course,
        'module': quiz.module,
        'quiz_questions': quiz_questions,
        'attempts': attempts[:5],  # Show last 5 attempts
        'attempts_count': attempts_count,
        'can_attempt': can_attempt,
        'best_score': best_score
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def quiz_take_view(request, quiz_id):
    """Take a quiz attempt."""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    course = quiz.module.course
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Você não está matriculado neste curso.')
        return redirect('my_courses')
    
    # Check attempts remaining
    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:
        messages.error(request, 'Você atingiu o número máximo de tentativas.')
        return redirect('quiz_view', quiz_id=quiz.id)
    
    if request.method == 'POST':
        # Process quiz submission
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            attempt_number=attempts_count + 1,
            score=0,
            passed=False
        )
        
        total_points = 0
        earned_points = 0
        
        # Process each question
        quiz_questions = QuizQuestion.objects.filter(quiz=quiz).select_related('question')
        
        for qq in quiz_questions:
            question = qq.question
            total_points += question.points
            
            # Get student answer
            if question.question_type == 'MC':
                selected_option_id = request.POST.get(f'question_{question.id}')
                if selected_option_id:
                    selected_option = QuestionOption.objects.get(id=selected_option_id)
                    is_correct = selected_option.is_correct
                    points = question.points if is_correct else 0
                    earned_points += points
                    
                    StudentAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option,
                        is_correct=is_correct,
                        points_earned=points
                    )
            
            elif question.question_type == 'TF':
                selected_option_id = request.POST.get(f'question_{question.id}')
                if selected_option_id:
                    selected_option = QuestionOption.objects.get(id=selected_option_id)
                    is_correct = selected_option.is_correct
                    points = question.points if is_correct else 0
                    earned_points += points
                    
                    StudentAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option,
                        is_correct=is_correct,
                        points_earned=points
                    )
            
            elif question.question_type == 'SA':
                text_answer = request.POST.get(f'question_{question.id}', '').strip()
                # For now, mark as needs manual grading (is_correct=False)
                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=text_answer,
                    is_correct=False,
                    points_earned=0
                )
        
        # Calculate score percentage
        score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score_percentage >= quiz.passing_score
        
        # Update attempt
        attempt.score = round(score_percentage, 2)
        attempt.passed = passed
        attempt.submitted_at = timezone.now()
        attempt.save()
        
        # Update student progress
        progress, created = StudentProgress.objects.get_or_create(
            user=request.user,
            quiz=quiz,
            defaults={'completed': False, 'score': 0}
        )
        
        if passed and (not progress.completed or score_percentage > progress.score):
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.score = score_percentage
            progress.save()
        
        messages.success(request, f'Quiz enviado! Pontuação: {score_percentage:.1f}%')
        return redirect('quiz_result', attempt_id=attempt.id)
    
    # GET request - show quiz form
    quiz_questions = QuizQuestion.objects.filter(
        quiz=quiz
    ).select_related('question').prefetch_related(
        'question__options'
    ).order_by('order')
    
    return render(request, 'courses/quiz_take.html', {
        'quiz': quiz,
        'course': course,
        'module': quiz.module,
        'quiz_questions': quiz_questions,
        'attempt_number': attempts_count + 1
    })


@login_required
@module_required(MODULE_PERMISSIONS['cursos'])
def quiz_result_view(request, attempt_id):
    """Display quiz results."""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    # Get answers with questions
    answers = StudentAnswer.objects.filter(
        attempt=attempt
    ).select_related(
        'question',
        'selected_option'
    ).order_by('question__quiz_questions__order')
    
    return render(request, 'courses/quiz_result.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'course': attempt.quiz.module.course,
        'answers': answers
    })


# ============================================================================
# TURMA / PRESENCE CONTROL VIEWS
# ============================================================================

@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def turma_list_view(request):
    """Turmas the user teaches (staff: all) or is enrolled in as an aluno."""
    if request.user.is_superuser or request.user.is_staff:
        teaching = Turma.objects.filter(is_active=True)
        enrolled = Turma.objects.none()
    else:
        teaching = Turma.objects.filter(professor=request.user, is_active=True)
        enrolled = Turma.objects.filter(students=request.user, is_active=True)
    return render(request, 'courses/turma_list.html', {
        'teaching': teaching,
        'enrolled': enrolled,
    })


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def turma_detail_view(request, turma_id):
    """Turma detail — roster for professors, own check-ins for alunos.

    Non-members get a 403: the roster (names + e-mails) must not leak.
    """
    turma = get_object_or_404(Turma, id=turma_id, is_active=True)
    role = require_presence_role(request.user, turma, PROFESSOR, ALUNO)

    is_professor = role == PROFESSOR
    is_student = role == ALUNO

    sessions = turma.presence_sessions.order_by('-date', '-created_at')

    # The roster is professor-only; alunos never receive it in context.
    students = turma.students.all() if is_professor else []
    sessions_data = [
        {
            'session': session,
            'count': session.records.count() if is_professor else None,
        }
        for session in sessions
    ]

    # For students: open sessions they can still check in to
    open_sessions = []
    if is_student:
        for session in sessions.filter(is_open=True):
            already_checked = session.records.filter(student=request.user).exists()
            open_sessions.append({'session': session, 'already_checked': already_checked})

    return render(request, 'courses/turma_detail.html', {
        'turma': turma,
        'presence_role': role,
        'is_professor': is_professor,
        'is_student': is_student,
        'students': students,
        'sessions_data': sessions_data,
        'open_sessions': open_sessions,
    })


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def presence_session_create_view(request, turma_id):
    """Professor creates a new presence session (scoped to their own turma)."""
    turma = get_object_or_404(Turma, id=turma_id, is_active=True)
    require_presence_role(request.user, turma, PROFESSOR)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        if date_str:
            from datetime import date as dt
            try:
                session_date = dt.fromisoformat(date_str)
            except ValueError:
                messages.error(request, 'Data inválida.')
                return redirect('presence_session_create', turma_id=turma.id)

            session = PresenceSession.objects.create(turma=turma, date=session_date, is_open=False)
            messages.success(request, f'Lista de presença para {session_date.strftime("%d/%m/%Y")} criada.')
            return redirect('presence_session_detail', session_id=session.id)

    from datetime import date as dt
    today = dt.today().isoformat()
    return render(request, 'courses/presence_session_form.html', {
        'turma': turma,
        'today': today,
    })


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def presence_session_detail_view(request, session_id):
    """Session panel — full roster for professors, own status for alunos.

    Members of the turma only; anybody else gets a 403.
    """
    session = get_object_or_404(PresenceSession, id=session_id)
    turma = session.turma
    role = require_presence_role(request.user, turma, PROFESSOR, ALUNO)

    if role == PROFESSOR:
        all_students = turma.students.all()
        present_ids = session.records.values_list('student_id', flat=True)
        present_students = all_students.filter(id__in=present_ids)
        absent_students = all_students.exclude(id__in=present_ids)
        student_count = all_students.count()
        my_record = None
    else:
        # Aluno: never expose the roster, only their own attendance.
        present_students = []
        absent_students = []
        student_count = None
        my_record = session.records.filter(student=request.user).first()

    return render(request, 'courses/presence_session_detail.html', {
        'session': session,
        'turma': turma,
        'presence_role': role,
        'is_professor': role == PROFESSOR,
        'is_student': role == ALUNO,
        'present_students': present_students,
        'absent_students': absent_students,
        'student_count': student_count,
        'my_record': my_record,
        'can_checkin': role == ALUNO and session.is_open and my_record is None,
    })


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def presence_session_toggle_view(request, session_id):
    """Professor opens/closes a session (Professor-only surface)."""
    session = get_object_or_404(PresenceSession, id=session_id)
    require_presence_role(request.user, session.turma, PROFESSOR)

    if request.method == 'POST':
        session.is_open = not session.is_open
        session.save()
        status = 'aberta' if session.is_open else 'fechada'
        messages.success(request, f'Chamada {status}.')

    return redirect('presence_session_detail', session_id=session.id)


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def presence_checkin_view(request, session_id):
    """Aluno registers their own presence in an open session."""
    session = get_object_or_404(PresenceSession, id=session_id)
    turma = session.turma

    # Professors do not check in as students; non-members are rejected too.
    require_presence_role(request.user, turma, ALUNO)

    if not session.is_open:
        raise PermissionDenied('A chamada não está aberta.')

    if request.method == 'POST':
        _, created = PresenceRecord.objects.get_or_create(session=session, student=request.user)
        if created:
            messages.success(request, 'Presença registrada com sucesso! ✅')
        else:
            messages.info(request, 'Você já registrou presença nesta aula.')

    return redirect('turma_detail', turma_id=turma.id)


@login_required
@module_required(MODULE_PERMISSIONS['presenca'])
def presence_remove_view(request, session_id, student_id):
    """Professor removes a student's presence from a session."""
    session = get_object_or_404(PresenceSession, id=session_id)
    require_presence_role(request.user, session.turma, PROFESSOR)

    if request.method == 'POST':
        record = PresenceRecord.objects.filter(session=session, student_id=student_id).first()
        if record:
            record.delete()
            messages.success(request, 'Presença removida com sucesso.')
        else:
            messages.error(request, 'Registro de presença não encontrado.')

    return redirect('presence_session_detail', session_id=session.id)

