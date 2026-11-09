"""
Idempotent seed of the module role groups (Professor / Aluno).

Usage::

    python manage.py seed_roles --settings=ong_platform.settings_dev

Creates/updates two Django groups and attaches the module permissions
declared in ``core.permissions.MODULE_PERMISSIONS``:

* **Aluno**     — access_courses, access_presence, checkin_presence
* **Professor** — access_courses, access_presence, manage_presence,
                  checkin_presence

Demo users are assigned to their group when they exist, so the dev flows are
testable right after ``seed_demo``. Safe to run repeatedly: permissions are
added (never removed) and memberships are idempotent.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser


ROLES = {
    'Aluno': [
        'courses.access_courses',
        'courses.access_presence',
        'courses.checkin_presence',
    ],
    'Professor': [
        'courses.access_courses',
        'courses.access_presence',
        'courses.manage_presence',
        'courses.checkin_presence',
    ],
}

DEMO_MEMBERS = {
    'Professor': ['professor@indes.dev'],
    'Aluno': ['aluno@indes.dev', 'beatriz@indes.dev', 'carlos@indes.dev'],
}


class Command(BaseCommand):
    help = 'Cria/atualiza os grupos de módulo Professor e Aluno (dev).'

    @transaction.atomic
    def handle(self, *args, **options):
        write = self.stdout.write

        for role, labels in ROLES.items():
            group, _ = Group.objects.get_or_create(name=role)
            permissions = [self._permission(label) for label in labels]
            group.permissions.add(*permissions)

            members = 0
            for email in DEMO_MEMBERS.get(role, []):
                user = CustomUser.objects.filter(email=email).first()
                if user is None:
                    continue
                group.user_set.add(user)
                members += 1

            write(self.style.SUCCESS(
                f'{role}: {len(permissions)} permissões, {members} usuário(s) demo'
            ))

    @staticmethod
    def _permission(label):
        app_label, codename = label.split('.', 1)
        return Permission.objects.get(
            content_type__app_label=app_label, codename=codename
        )