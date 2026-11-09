"""
Idempotent demo seed for local development.

Usage::

    python manage.py seed_demo --settings=ong_platform.settings_dev

Creates (only what is missing, so it is safe to run repeatedly):

* 1 superuser            — admin@indes.dev
* 1 professor + 3 alunos — senha comum de demonstração
* 2 organizações         — ONGs parceiras
* 3 cursos               — com módulos, aulas (uma com vídeo do YouTube)
* 2 turmas por curso     — com professor e alunos
* matrículas             — o aluno demo vê "Minhas turmas"
* 1 chamada aberta       — para testar o fluxo de presença

Nothing is deleted and existing rows are never overwritten.
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser
from courses.models import (
    Course, Enrollment, Lesson, Module, PresenceSession, Turma,
)
from orgs.models import Organization, OrgMember

ADMIN_EMAIL = 'admin@indes.dev'
ADMIN_PASSWORD = 'indesdev2026'

DEMO_PASSWORD = 'indesdev2026'

PROFESSOR = {
    'email': 'professor@indes.dev',
    'first_name': 'Marina',
    'last_name': 'Albuquerque',
}

STUDENTS = [
    {'email': 'aluno@indes.dev', 'first_name': 'Ana', 'last_name': 'Souza'},
    {'email': 'beatriz@indes.dev', 'first_name': 'Beatriz', 'last_name': 'Lima'},
    {'email': 'carlos@indes.dev', 'first_name': 'Carlos', 'last_name': 'Ferreira'},
]

ORGANIZATIONS = [
    'Associação Inclusão para Todos',
    'Instituto Semear',
]

COURSES = [
    {
        'name': 'Inclusão Escolar na Prática',
        'description': (
            'Estratégias pedagógicas e adaptações curriculares para receber '
            'estudantes com deficiência intelectual na escola regular.'
        ),
        'price': Decimal('149.90'),
        'image_url': 'https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=800&h=500&fit=crop',
        'modules': [
            {
                'title': 'Fundamentos da educação inclusiva',
                'description': 'Conceitos, legislação e o papel da escola.',
                'lessons': [
                    {
                        'title': 'O que é educação inclusiva',
                        'duration_minutes': 12,
                        'content': (
                            '<p>A educação inclusiva parte do princípio de que '
                            '<strong>toda pessoa aprende</strong> e que a escola '
                            'deve se adaptar ao estudante — e não o contrário.</p>'
                            '<p>Nesta aula vamos revisar os marcos legais '
                            'brasileiros (Constituição de 1988, LDB e a Lei '
                            'Brasileira de Inclusão) e o que eles mudam no '
                            'cotidiano da sala de aula.</p>'
                            '<h3>Pontos-chave</h3>'
                            '<ul><li>Matrícula obrigatória na rede regular.</li>'
                            '<li>Atendimento Educacional Especializado (AEE).</li>'
                            '<li>Plano Educacional Individualizado (PEI).</li></ul>'
                        ),
                    },
                    {
                        'title': 'Desenho Universal para Aprendizagem',
                        'duration_minutes': 18,
                        'content': (
                            '<p>O DUA propõe três princípios: múltiplas formas de '
                            '<em>representação</em>, de <em>ação e expressão</em> e '
                            'de <em>engajamento</em>.</p>'
                            '<p>Na prática, isso significa oferecer o mesmo conteúdo '
                            'em texto, áudio e vídeo, e permitir que o estudante '
                            'demonstre o aprendizado de formas diferentes.</p>'
                        ),
                    },
                    {
                        'title': 'Vídeo: adaptando a sala de aula',
                        'duration_minutes': 9,
                        'video_url': 'https://www.youtube.com/embed/tgbNymZ7vqY',
                        'content': (
                            '<p>Assista ao vídeo e, em seguida, liste três '
                            'adaptações simples que você poderia aplicar na sua '
                            'próxima aula.</p>'
                        ),
                    },
                ],
            },
            {
                'title': 'Prática em sala',
                'description': 'Planejamento, avaliação e parceria com as famílias.',
                'lessons': [
                    {
                        'title': 'Planejando aulas acessíveis',
                        'duration_minutes': 15,
                        'content': (
                            '<p>Um bom planejamento acessível começa por objetivos '
                            'claros e por materiais que não dependem de uma única '
                            'forma de leitura.</p>'
                            '<p>Comece pequeno: escolha uma aula da próxima semana '
                            'e adapte o material, a instrução e a avaliação.</p>'
                        ),
                    },
                    {
                        'title': 'Avaliação formativa e feedback',
                        'duration_minutes': 11,
                        'content': (
                            '<p>A avaliação inclusiva é contínua e descritiva. '
                            'Ela registra o percurso do estudante em vez de '
                            'compará-lo a uma média.</p>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'name': 'Comunicação Alternativa e Acessibilidade',
        'description': (
            'Recursos de comunicação alternativa, tecnologia assistiva e '
            'acessibilidade digital para ampliar a autonomia dos estudantes.'
        ),
        'price': Decimal('129.90'),
        'image_url': 'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=800&h=500&fit=crop',
        'modules': [
            {
                'title': 'Introdução à comunicação alternativa',
                'description': 'Pranchas, pictogramas e sistemas alternativos.',
                'lessons': [
                    {
                        'title': 'Quando usar comunicação alternativa',
                        'duration_minutes': 10,
                        'content': (
                            '<p>Comunicação alternativa é qualquer recurso que '
                            'substitua ou complemente a fala.</p>'
                            '<p>Ela é indicada quando a comunicação oral não é '
                            'suficiente para a pessoa expressar necessidades, '
                            'escolhas e afetos.</p>'
                        ),
                    },
                    {
                        'title': 'Pranchas e pictogramas na rotina',
                        'duration_minutes': 14,
                        'content': (
                            '<p>Pranchas funcionam melhor quando estão no contexto '
                            'de uso: na mesa, na cozinha, no parque.</p>'
                            '<p>Modelar o uso é parte do ensino — o adulto também '
                            'aponta e usa a prancha.</p>'
                        ),
                    },
                ],
            },
            {
                'title': 'Acessibilidade digital',
                'description': 'Documentos, sites e materiais que todos conseguem usar.',
                'lessons': [
                    {
                        'title': 'Contraste, fonte e legibilidade',
                        'duration_minutes': 8,
                        'content': (
                            '<p>Texto com bom contraste e corpo mínimo de 16px '
                            'reduz o esforço de leitura.</p>'
                            '<p>Evite blocos longos em itálico e prefira '
                            'alinhamento à esquerda.</p>'
                        ),
                    },
                    {
                        'title': 'Vídeo: audiodescrição e legendas',
                        'duration_minutes': 7,
                        'video_url': 'https://www.youtube.com/embed/aqz-KE-bpKQ',
                        'content': (
                            '<p>Legendas e audiodescrição são complementares: '
                            'uma atende quem não ouve, a outra quem não vê.</p>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'name': 'Autonomia e Vida Independente',
        'description': (
            'Habilidades para o dia a dia, preparação para o trabalho e '
            'construção de projetos de vida com apoio da rede familiar.'
        ),
        'price': Decimal('0.00'),
        'image_url': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&h=500&fit=crop',
        'modules': [
            {
                'title': 'Habilidades do cotidiano',
                'description': 'Organização pessoal, dinheiro e deslocamento.',
                'lessons': [
                    {
                        'title': 'Organizando a rotina da semana',
                        'duration_minutes': 12,
                        'content': (
                            '<p>Agendas visuais ajudam a antecipar o que vai '
                            'acontecer e reduzem a ansiedade.</p>'
                            '<p>Use poucos itens por dia e revise a agenda '
                            'junto com o estudante todas as manhãs.</p>'
                        ),
                    },
                    {
                        'title': 'Dinheiro e escolhas do dia a dia',
                        'duration_minutes': 16,
                        'content': (
                            '<p>Trabalhar com cédulas reais ou simuladas torna o '
                            'aprendizado concreto.</p>'
                            '<p>Comece com compras simples e evolua para '
                            'orçamentos curtos.</p>'
                        ),
                    },
                ],
            },
            {
                'title': 'Mundo do trabalho',
                'description': 'Currículo, entrevistas e direitos.',
                'lessons': [
                    {
                        'title': 'Meu primeiro currículo',
                        'duration_minutes': 13,
                        'content': (
                            '<p>Um currículo curto e verdadeiro é melhor do que '
                            'uma lista longa de cursos que não foram concluídos.</p>'
                            '<p>Destaque o que a pessoa sabe fazer e gosta de '
                            'fazer.</p>'
                        ),
                    },
                ],
            },
        ],
    },
]

TURMA_SUFFIXES = ['Manhã', 'Noite']


class Command(BaseCommand):
    help = 'Cria dados de demonstração idempotentes para o Indes Portal (dev).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEMO_PASSWORD,
            help='Senha aplicada apenas a usuários recém-criados.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        stats = {
            'users': 0, 'orgs': 0, 'courses': 0, 'modules': 0,
            'lessons': 0, 'turmas': 0, 'enrollments': 0, 'sessions': 0,
        }

        admin = self._user(
            ADMIN_EMAIL, password, 'Administrador', 'Indes',
            is_staff=True, is_superuser=True, stats=stats,
        )
        professor = self._user(
            PROFESSOR['email'], password,
            PROFESSOR['first_name'], PROFESSOR['last_name'], stats=stats,
        )
        students = [
            self._user(s['email'], password, s['first_name'], s['last_name'], stats=stats)
            for s in STUDENTS
        ]

        for org_name in ORGANIZATIONS:
            org, created = Organization.objects.get_or_create(name=org_name)
            if created:
                stats['orgs'] += 1
            OrgMember.objects.get_or_create(
                organization=org, user=professor, defaults={'role': 'admin'}
            )

        courses = []
        for position, data in enumerate(COURSES):
            course, created = Course.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'price': data['price'],
                    'image_url': data['image_url'],
                    'is_active': True,
                },
            )
            if created:
                stats['courses'] += 1
            courses.append(course)

            for module_order, module_data in enumerate(data['modules'], start=1):
                module, module_created = Module.objects.get_or_create(
                    course=course,
                    order=module_order,
                    defaults={
                        'title': module_data['title'],
                        'description': module_data['description'],
                        'is_published': True,
                    },
                )
                if module_created:
                    stats['modules'] += 1
                if not module.is_published:
                    module.is_published = True
                    module.save(update_fields=['is_published'])

                for lesson_order, lesson_data in enumerate(
                    module_data['lessons'], start=1
                ):
                    _, lesson_created = Lesson.objects.get_or_create(
                        module=module,
                        order=lesson_order,
                        defaults={
                            'title': lesson_data['title'],
                            'content': lesson_data['content'],
                            'video_url': lesson_data.get('video_url', ''),
                            'duration_minutes': lesson_data.get('duration_minutes'),
                            'is_published': True,
                        },
                    )
                    if lesson_created:
                        stats['lessons'] += 1

            # Duas turmas por curso: manhã e noite
            morning_turma = None
            for suffix in TURMA_SUFFIXES:
                turma, turma_created = Turma.objects.get_or_create(
                    name=f'{course.name} — Turma {suffix}',
                    defaults={'professor': professor, 'is_active': True},
                )
                if turma_created:
                    stats['turmas'] += 1
                if turma.professor_id is None:
                    turma.professor = professor
                    turma.save(update_fields=['professor'])
                turma.students.add(*students)
                if suffix == TURMA_SUFFIXES[0]:
                    morning_turma = turma

            # Chamada aberta na turma da manhã do primeiro curso
            if position == 0 and morning_turma is not None:
                _, session_created = PresenceSession.objects.get_or_create(
                    turma=morning_turma,
                    date=date.today(),
                    defaults={'is_open': True},
                )
                if session_created:
                    stats['sessions'] += 1

        # Matrículas: o aluno demo enxerga 2 cursos em "Meus cursos"
        enrollment_plan = [
            (students[0], courses[0]),
            (students[0], courses[1]),
            (students[1], courses[0]),
            (students[2], courses[2]),
        ]
        for user, course in enrollment_plan:
            _, created = Enrollment.objects.get_or_create(
                user=user, course=course, defaults={'source': 'individual'}
            )
            if created:
                stats['enrollments'] += 1

        # Garante que o admin também tenha acesso de leitura a um curso
        Enrollment.objects.get_or_create(
            user=admin, course=courses[0], defaults={'source': 'individual'}
        )

        self._report(stats, password, admin)

    # ------------------------------------------------------------------
    def _user(self, email, password, first_name, last_name, stats,
              is_staff=False, is_superuser=False):
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
                'is_active': True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
            stats['users'] += 1
        else:
            changed = False
            for field in ('is_staff', 'is_superuser'):
                wanted = is_staff if field == 'is_staff' else is_superuser
                if wanted and not getattr(user, field):
                    setattr(user, field, True)
                    changed = True
            if changed:
                user.save()
        return user

    def _report(self, stats, password, admin):
        write = self.stdout.write
        write(self.style.SUCCESS('\nIndes Portal — dados de demonstração'))
        write('-' * 52)
        write(f"Usuários criados .......... {stats['users']}")
        write(f"Organizações criadas ...... {stats['orgs']}")
        write(f"Cursos criados ............ {stats['courses']}")
        write(f"Módulos criados ........... {stats['modules']}")
        write(f"Aulas criadas ............. {stats['lessons']}")
        write(f"Turmas criadas ............ {stats['turmas']}")
        write(f"Matrículas criadas ........ {stats['enrollments']}")
        write(f"Chamadas abertas .......... {stats['sessions']}")
        write('-' * 52)
        write('Contas de acesso (senha: %s)' % password)
        write(f'  admin (superuser)  {admin.email}')
        write(f'  professor          {PROFESSOR["email"]}')
        for s in STUDENTS:
            write(f'  aluno              {s["email"]}')
        write('-' * 52)
        write(
            'Totais no banco: %d cursos, %d aulas, %d turmas, %d matrículas'
            % (
                Course.objects.count(), Lesson.objects.count(),
                Turma.objects.count(), Enrollment.objects.count(),
            )
        )