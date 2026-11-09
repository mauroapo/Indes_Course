"""Permission tests for module gating and the Professor/Aluno presence roles.

Run with::

    python manage.py test --settings=ong_platform.settings_dev
"""

from datetime import date
from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import URLPattern, URLResolver, reverse

import courses.urls as courses_urls
from accounts.models import CustomUser
from core.permissions import MODULE_PERMISSIONS, user_has_module
from courses.models import PresenceRecord, PresenceSession, Turma


def make_user(email, **extra):
    return CustomUser.objects.create_user(email=email, password='testpass123', **extra)


def add_to_group(user, name):
    user.groups.add(Group.objects.get(name=name))
    return user


def iter_url_patterns(patterns):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            yield pattern
        elif isinstance(pattern, URLResolver):
            yield from iter_url_patterns(pattern.url_patterns)


class PermissionTestCase(TestCase):
    """Shared fixtures: one professor, one aluno, one outsider, two turmas."""

    @classmethod
    def setUpTestData(cls):
        # Creates the Aluno / Professor groups exactly like the dev seed does.
        call_command('seed_roles', stdout=StringIO())

        cls.professor = add_to_group(make_user('professor@test.dev'), 'Professor')
        cls.aluno = add_to_group(make_user('aluno@test.dev'), 'Aluno')
        cls.classmate = add_to_group(make_user('classmate@test.dev'), 'Aluno')

        # Authenticated but no module permission at all.
        cls.outsider = make_user('outsider@test.dev')

        # Second professor, to prove scope is checked (not just the group).
        cls.other_professor = add_to_group(make_user('other-prof@test.dev'), 'Professor')
        cls.other_aluno = add_to_group(make_user('other-aluno@test.dev'), 'Aluno')

        cls.superuser = CustomUser.objects.create_superuser(
            email='root@test.dev', password='testpass123'
        )

        cls.turma = Turma.objects.create(name='Turma A', professor=cls.professor)
        cls.turma.students.add(cls.aluno, cls.classmate)

        cls.other_turma = Turma.objects.create(
            name='Turma B', professor=cls.other_professor
        )
        cls.other_turma.students.add(cls.other_aluno)

        cls.open_session = PresenceSession.objects.create(
            turma=cls.turma, date=date.today(), is_open=True
        )
        cls.closed_session = PresenceSession.objects.create(
            turma=cls.turma, date=date.today(), is_open=False
        )
        cls.other_session = PresenceSession.objects.create(
            turma=cls.other_turma, date=date.today(), is_open=True
        )


class ModuleGateTests(PermissionTestCase):
    def test_user_without_module_permission_gets_403(self):
        self.client.force_login(self.outsider)
        for url in (reverse('my_courses'), reverse('turma_list')):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_aluno_can_open_courses_and_classes(self):
        self.client.force_login(self.aluno)
        self.assertEqual(self.client.get(reverse('my_courses')).status_code, 200)
        self.assertEqual(self.client.get(reverse('turma_list')).status_code, 200)

    def test_superuser_bypasses_module_gate(self):
        self.client.force_login(self.superuser)
        for url in (reverse('my_courses'), reverse('turma_list')):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_user_has_module_helper(self):
        self.assertTrue(user_has_module(self.professor, 'cursos'))
        self.assertTrue(user_has_module(self.aluno, 'presenca'))
        self.assertTrue(user_has_module(self.superuser, 'cursos'))
        self.assertFalse(user_has_module(self.outsider, 'cursos'))
        self.assertFalse(user_has_module(self.outsider, 'presenca'))
        self.assertFalse(user_has_module(self.outsider, 'does-not-exist'))


class AlunoPresenceTests(PermissionTestCase):
    def test_aluno_sees_turma_detail_without_professor_controls(self):
        self.client.force_login(self.aluno)
        response = self.client.get(reverse('turma_detail', args=[self.turma.id]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn('Nova Lista de Presença', html)
        self.assertNotIn('presence_session_toggle', html)
        # Roster of classmates must not leak to alunos.
        self.assertNotIn(self.classmate.email, html)
        self.assertNotIn(self.classmate.get_full_name() or 'classmate', html)

    def test_aluno_can_checkin_open_session(self):
        self.client.force_login(self.aluno)
        response = self.client.post(
            reverse('presence_checkin', args=[self.open_session.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PresenceRecord.objects.filter(
                session=self.open_session, student=self.aluno
            ).exists()
        )

    def test_aluno_cannot_checkin_closed_session(self):
        self.client.force_login(self.aluno)
        response = self.client.post(
            reverse('presence_checkin', args=[self.closed_session.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_aluno_cannot_toggle_session(self):
        self.client.force_login(self.aluno)
        response = self.client.post(
            reverse('presence_session_toggle', args=[self.open_session.id])
        )
        self.assertEqual(response.status_code, 403)
        self.open_session.refresh_from_db()
        self.assertTrue(self.open_session.is_open)

    def test_aluno_cannot_create_session_or_remove_record(self):
        self.client.force_login(self.aluno)
        self.assertEqual(
            self.client.post(
                reverse('presence_session_create', args=[self.turma.id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_remove', args=[self.open_session.id, self.aluno.id])
            ).status_code,
            403,
        )

    def test_aluno_session_detail_shows_own_status_only(self):
        self.client.force_login(self.aluno)
        response = self.client.get(
            reverse('presence_session_detail', args=[self.open_session.id])
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('Minha presença', html)
        self.assertNotIn('Remover', html)
        self.assertNotIn(self.other_aluno.email, html)

    def test_non_member_aluno_gets_403_on_other_turma(self):
        self.client.force_login(self.aluno)
        self.assertEqual(
            self.client.get(reverse('turma_detail', args=[self.other_turma.id])).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse('presence_session_detail', args=[self.other_session.id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_checkin', args=[self.other_session.id])
            ).status_code,
            403,
        )


class ProfessorPresenceTests(PermissionTestCase):
    def test_professor_sees_controls_on_own_turma(self):
        self.client.force_login(self.professor)
        response = self.client.get(reverse('turma_detail', args=[self.turma.id]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('Nova Lista de Presença', html)

    def test_professor_can_create_toggle_and_remove(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse('presence_session_create', args=[self.turma.id]),
            {'date': '2026-11-10'},
        )
        self.assertEqual(response.status_code, 302)
        session = PresenceSession.objects.get(turma=self.turma, date='2026-11-10')

        # toggle open -> closed
        response = self.client.post(
            reverse('presence_session_toggle', args=[session.id])
        )
        self.assertEqual(response.status_code, 302)
        session.refresh_from_db()
        self.assertTrue(session.is_open)

        record = PresenceRecord.objects.create(session=session, student=self.aluno)
        response = self.client.post(
            reverse('presence_remove', args=[session.id, self.aluno.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PresenceRecord.objects.filter(pk=record.pk).exists())

    def test_professor_cannot_manage_another_professors_turma(self):
        self.client.force_login(self.professor)
        self.assertEqual(
            self.client.get(reverse('turma_detail', args=[self.other_turma.id])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_session_create', args=[self.other_turma.id]),
                {'date': '2026-11-11'},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_session_toggle', args=[self.other_session.id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_remove', args=[self.other_session.id, self.other_aluno.id])
            ).status_code,
            403,
        )

    def test_professor_cannot_checkin_as_aluno(self):
        self.client.force_login(self.professor)
        response = self.client.post(
            reverse('presence_checkin', args=[self.turma.presence_sessions.first().id])
        )
        self.assertEqual(response.status_code, 403)

    def test_turma_list_scopes_teaching_and_enrolled(self):
        self.client.force_login(self.professor)
        response = self.client.get(reverse('turma_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Turma A')
        self.assertNotContains(response, 'Turma B')


class SuperuserBypassTests(PermissionTestCase):
    def test_superuser_reaches_every_presence_surface(self):
        self.client.force_login(self.superuser)
        self.assertEqual(
            self.client.get(reverse('turma_detail', args=[self.other_turma.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse('presence_session_detail', args=[self.other_session.id])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                reverse('presence_session_toggle', args=[self.other_session.id])
            ).status_code,
            302,
        )


class UrlConventionTests(TestCase):
    """Every public view in courses.urls must carry module_permissions."""

    def test_module_registry_is_the_source_of_truth(self):
        self.assertEqual(MODULE_PERMISSIONS['cursos'], 'courses.access_courses')
        self.assertEqual(MODULE_PERMISSIONS['presenca'], 'courses.access_presence')

    def test_every_view_declares_module_permissions(self):
        known = set(MODULE_PERMISSIONS.values())
        checked = 0
        for pattern in iter_url_patterns(courses_urls.urlpatterns):
            name = pattern.name or ''
            if name.startswith(('admin', 'static')):
                continue
            view = pattern.callback
            with self.subTest(pattern=name or str(pattern.pattern)):
                self.assertTrue(
                    hasattr(view, 'module_permissions'),
                    msg=f'{name} is not decorated with @module_required',
                )
                self.assertTrue(view.module_permissions)
                for permission in view.module_permissions:
                    self.assertIn(permission, known)
            checked += 1
        self.assertGreaterEqual(checked, 15)