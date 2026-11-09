from django.db import models
from django.conf import settings


class Course(models.Model):
    """Course model."""
    
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    image_url = models.URLField(max_length=500, verbose_name='URL da Imagem')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        permissions = [
            ('access_courses', 'Pode acessar o módulo Cursos'),
        ]


class Enrollment(models.Model):
    """User course enrollment."""
    
    SOURCE_CHOICES = [
        ('individual', 'Individual'),
        ('org_package', 'Organization Package'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    acquired_at = models.DateTimeField(auto_now_add=True, verbose_name='Adquirido em')
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='individual',
        verbose_name='Origem'
    )
    
    def __str__(self):
        return f'{self.user.email} - {self.course.name}'
    
    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['user', 'course']
        ordering = ['-acquired_at']


# ============================================================================
# COURSE CONTENT MANAGEMENT MODELS
# ============================================================================

class Module(models.Model):
    """Course module/section grouping related content."""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Curso'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_published = models.BooleanField(default=False, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    def __str__(self):
        return f'{self.course.name} - {self.title}'
    
    class Meta:
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']


class Lesson(models.Model):
    """Individual lesson with rich content."""
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Módulo'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    content = models.TextField(verbose_name='Conteúdo', help_text='Rich text content (HTML supported)')
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='URL do Vídeo',
        help_text='YouTube or Vimeo URL'
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duração (minutos)',
        help_text='Estimated time to complete'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_published = models.BooleanField(default=False, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    @property
    def embed_video_url(self):
        """Returns the appropriate embed URL for the video (e.g., converting Drive view links to preview)."""
        if not self.video_url:
            return ""
            
        url = self.video_url
        if 'drive.google.com' in url and '/view' in url:
            view_idx = url.find('/view')
            if view_idx != -1:
                return url[:view_idx] + '/preview'
        return url

    def __str__(self):
        return f'{self.module.title} - {self.title}'
    
    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']


class Question(models.Model):
    """Reusable question for quizzes."""
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Curso',
        help_text='For organization purposes'
    )
    question_text = models.TextField(verbose_name='Pergunta')
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        verbose_name='Tipo'
    )
    explanation = models.TextField(
        blank=True,
        verbose_name='Explicação',
        help_text='Shown after answering'
    )
    points = models.PositiveIntegerField(default=1, verbose_name='Pontos')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    def __str__(self):
        return f'{self.question_text[:50]}...' if len(self.question_text) > 50 else self.question_text
    
    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-created_at']


class QuestionOption(models.Model):
    """Answer option for multiple choice questions."""
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Pergunta'
    )
    option_text = models.CharField(max_length=500, verbose_name='Opção')
    is_correct = models.BooleanField(default=False, verbose_name='Correta')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    
    def __str__(self):
        return f'{self.option_text} {"✓" if self.is_correct else ""}'
    
    class Meta:
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'
        ordering = ['question', 'order']


class Quiz(models.Model):
    """Assessment activity for a module."""
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name='Módulo'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    passing_score = models.PositiveIntegerField(
        default=70,
        verbose_name='Nota de Aprovação (%)',
        help_text='Percentage required to pass'
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name='Tentativas Máximas'
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo Limite (minutos)',
        help_text='Leave blank for no time limit'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_published = models.BooleanField(default=False, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    def __str__(self):
        return f'{self.module.title} - {self.title}'
    
    def total_points(self):
        """Calculate total points available in quiz."""
        return sum(qq.question.points for qq in self.quiz_questions.all())
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']


class QuizQuestion(models.Model):
    """Many-to-many through table linking quizzes and questions."""
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        verbose_name='Quiz'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        verbose_name='Pergunta'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    
    def __str__(self):
        return f'{self.quiz.title} - Q{self.order}'
    
    class Meta:
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
        ordering = ['quiz', 'order']
        unique_together = ['quiz', 'question']


class StudentProgress(models.Model):
    """Track student completion of lessons and quizzes."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name='Usuário'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_progress',
        verbose_name='Lição'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_progress',
        verbose_name='Quiz'
    )
    completed = models.BooleanField(default=False, verbose_name='Concluído')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Pontuação (%)',
        help_text='For quizzes only'
    )
    time_spent_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo Gasto (segundos)'
    )
    
    def __str__(self):
        item = self.lesson or self.quiz
        return f'{self.user.email} - {item}'
    
    class Meta:
        verbose_name = 'Student Progress'
        verbose_name_plural = 'Student Progress'
        ordering = ['-completed_at']
        # Either lesson OR quiz must be set, not both
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(lesson__isnull=False, quiz__isnull=True) |
                    models.Q(lesson__isnull=True, quiz__isnull=False)
                ),
                name='lesson_or_quiz_not_both'
            )
        ]


class QuizAttempt(models.Model):
    """Record of a student's quiz attempt."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name='Usuário'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Quiz'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Pontuação (%)'
    )
    passed = models.BooleanField(default=False, verbose_name='Aprovado')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Iniciado em')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    attempt_number = models.PositiveIntegerField(verbose_name='Tentativa Nº')
    
    def __str__(self):
        return f'{self.user.email} - {self.quiz.title} (Attempt {self.attempt_number})'
    
    class Meta:
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        ordering = ['-started_at']


class StudentAnswer(models.Model):
    """Student's answer to a quiz question."""
    
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Tentativa'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='Pergunta'
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_answers',
        verbose_name='Opção Selecionada',
        help_text='For multiple choice questions'
    )
    text_answer = models.TextField(
        blank=True,
        verbose_name='Resposta em Texto',
        help_text='For short answer questions'
    )
    is_correct = models.BooleanField(default=False, verbose_name='Correta')
    points_earned = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Pontos Obtidos'
    )
    
    def __str__(self):
        return f'{self.attempt.user.email} - {self.question}'
    
    class Meta:
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
        unique_together = ['attempt', 'question']


# ============================================================================
# PRESENCE CONTROL (TURMAS) MODELS
# ============================================================================

class Turma(models.Model):
    """Class/Cohort managed by a professor with a roster of students."""
    
    name = models.CharField(max_length=200, verbose_name='Nome da Turma')
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='teaching_turmas',
        verbose_name='Professor'
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='enrolled_turmas',
        verbose_name='Alunos'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['-created_at']
        permissions = [
            ('access_presence', 'Pode acessar o módulo Presença'),
            ('manage_presence', 'Professor: gerenciar chamada e presenças'),
            ('checkin_presence', 'Aluno: registrar a própria presença'),
        ]


class PresenceSession(models.Model):
    """A specific session where presences can be recorded."""
    
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='presence_sessions',
        verbose_name='Turma'
    )
    date = models.DateField(verbose_name='Data')
    is_open = models.BooleanField(
        default=False,
        verbose_name='Chamada Aberta',
        help_text='Indicates if students can register presence right now.'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    def __str__(self):
        return f'{self.turma.name} - {self.date}'
    
    class Meta:
        verbose_name = 'Presence Session'
        verbose_name_plural = 'Presence Sessions'
        ordering = ['-date', '-created_at']


class PresenceRecord(models.Model):
    """A single student check-in for a specific presence session."""
    
    session = models.ForeignKey(
        PresenceSession,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='Sessão de Presença'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presence_records',
        verbose_name='Aluno'
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Registrada em')
    
    def __str__(self):
        return f'{self.student.email} present at {self.session}'
    
    class Meta:
        verbose_name = 'Presence Record'
        verbose_name_plural = 'Presence Records'
        ordering = ['-registered_at']
        unique_together = ['session', 'student']

