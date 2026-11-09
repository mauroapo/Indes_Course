"""
Presence-specific role resolution (Professor / Aluno).

Two independent facts decide what a user may do in a turma:

1. the **group permission** (``courses.manage_presence`` for professors,
   ``courses.checkin_presence`` for alunos) — the gate;
2. the **object relation** (``turma.professor`` / ``turma.students``) — the
   scope.

A professor must not manage another professor's turma; an aluno must not read
another turma's roster. Both checks therefore matter.
"""

from django.core.exceptions import PermissionDenied

PROFESSOR = 'professor'
ALUNO = 'aluno'


def presence_role(user, turma):
    """Return ``'professor'``, ``'aluno'`` or ``None`` for *user* in *turma*.

    * ``professor`` — superuser/staff, or holds ``courses.manage_presence``
      and teaches this turma;
    * ``aluno`` — holds ``courses.checkin_presence`` and belongs to the turma;
    * ``None`` — no access (callers must raise ``PermissionDenied``).
    """
    if user is None or not getattr(user, 'is_authenticated', False) or turma is None:
        return None

    if user.is_superuser or user.is_staff:
        return PROFESSOR

    if user.has_perm('courses.manage_presence') and turma.professor_id == user.id:
        return PROFESSOR

    if user.has_perm('courses.checkin_presence') and turma.students.filter(pk=user.pk).exists():
        return ALUNO

    return None


def require_presence_role(user, turma, *allowed):
    """Return the resolved role, raising ``PermissionDenied`` when not allowed.

    ``allowed`` is the set of roles the caller permits (e.g.
    ``require_presence_role(request.user, turma, PROFESSOR)``).
    """
    role = presence_role(user, turma)
    if role not in allowed:
        raise PermissionDenied(
            'Você não tem permissão para acessar esta turma.'
        )
    return role