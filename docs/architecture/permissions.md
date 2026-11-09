# Permissões de módulo — padrão obrigatório

Este documento define o **padrão obrigatório** para todo módulo funcional do
Indes Portal. Desde a implementação de Cursos e Presença, um módulo só é
considerado pronto quando cumpre **todos** os itens do checklist abaixo.
A regra é obrigatória, não opcional: qualquer módulo novo (ou refatorado) que
não a siga não deve ser mesclado.

Origem do requisito: o dono do produto definiu que **Cursos é permissionado** e
que **Presença também**, sendo este o modelo a repetir em todos os módulos
seguintes.

---

## 1. Conceitos

| Peça | Onde vive | Função |
| --- | --- | --- |
| `MODULE_PERMISSIONS` | `core/permissions.py` | Dicionário `chave_do_módulo -> permissão Django`. Fonte única da verdade. |
| `module_required(*perms)` | `core/permissions.py` | Decorator de views de função. Superuser passa; senão exige **todas** as permissões listadas (`has_perms`). Falha → `PermissionDenied` (403). |
| `ModuleRequiredMixin` | `core/permissions.py` | Equivalente para CBVs. |
| `user_has_module(user, key)` | `core/permissions.py` | Checagem pontual (menus, relatórios, APIs). |
| `presence_role(user, turma)` | `courses/permissions.py` | Resolve `'professor'`, `'aluno'` ou `None` para uma turma. |

Duas camadas, sempre as duas:

1. **Portão (gate):** a permissão de grupo (`courses.access_<modulo>`).
2. **Escopo (scope):** a relação com o objeto (`turma.professor`,
   `turma.students`, `Enrollment.user`, …).

Um professor não gerencia a turma de outro professor; um aluno não lê a lista
de outra turma. A permissão sozinha nunca basta quando existe um objeto.

---

## 2. Checklist obrigatório de um módulo novo

Siga na ordem. Cada item tem um teste correspondente.

### 2.1 Declarar a permissão no model

```python
class Meta:
    permissions = [
        ('access_relatorios', 'Pode acessar o módulo Relatórios'),
    ]
```

Gere a migração (`makemigrations`) e rode `migrate`. Nomeie o arquivo de forma
semântica (`00XX_module_permissions.py`), não deixe o nome automático.

### 2.2 Registrar em `MODULE_PERMISSIONS`

```python
MODULE_PERMISSIONS = {
    'cursos': 'courses.access_courses',
    'presenca': 'courses.access_presence',
    'relatorios': 'courses.access_relatorios',   # novo
}
```

Sem essa entrada o módulo não é reconhecido por `user_has_module` (falha
fechada) nem pela checagem de convenção dos testes.

### 2.3 Decorar **todas** as views do módulo

```python
@login_required                                   # sempre por fora
@module_required(MODULE_PERMISSIONS['relatorios']) # sempre por dentro
def relatorio_view(request):
    ...
```

Regras de ordem:

* `login_required` **antes** (mais externo) para que anônimos sejam
  redirecionados ao login, não recebam 403.
* `module_required` **depois** (mais interno) para que o usuário autenticado
  sem permissão receba 403.
* Views que pertencem a mais de um módulo recebem os decorators em sequência.
* Ações sensíveis dentro do módulo exigem permissão extra **e** escopo de
  objeto (ex.: `manage_presence` + `turma.professor == request.user`).

### 2.4 Gatear a navegação

```django
{% if perms.relatorios.access_relatorios %}
<li><a href="{% url 'relatorio_list' %}">Relatórios</a></li>
{% endif %}
```

Nunca renderize um link para uma view que o usuário não pode abrir.

### 2.5 Criar grupos de papel, se o módulo tiver papéis

Papéis (ex.: Professor / Aluno) são **grupos do Django**, nunca flags no
perfil. Adicione o papel ao comando idempotente:

```python
ROLES = {
    'Aluno':     ['courses.access_presence', 'courses.checkin_presence'],
    'Professor': ['courses.access_presence', 'courses.manage_presence'],
}
```

`python manage.py seed_roles` cria/atualiza os grupos; `seed_demo` o chama.

### 2.6 Escrever testes

Mínimo exigido por módulo:

* usuário autenticado **sem** a permissão → **403** em cada rota;
* usuário com o papel de leitura → **200** nas rotas permitidas;
* usuário com o papel de gestão → **200/302** nas ações de gestão;
* usuário de outro escopo (não membro / outro professor) → **403**;
* superuser → passa em tudo;
* a varredura de convenção (abaixo) continua verde.

---

## 3. Teste de convenção (anti-erosão)

`courses/tests_permissions.py::UrlConventionTests` percorre
`courses.urls.urlpatterns`, resolve cada `URLPattern` (ignorando `admin` e
`static`) e exige:

* `view.module_permissions` existe e não está vazio;
* cada permissão declarada está em `MODULE_PERMISSIONS.values()`.

**Todo módulo novo precisa do seu próprio teste equivalente.** O teste da
varredura é o que impede que a convenção se degrade com o tempo.

---

## 4. Handler de 403

`ong_platform/urls.py` define `handler403 = 'core.views.error_403'`, que
renderiza `core/templates/403.html` com a identidade do Indes Portal
("Acesso restrito"). Não deixe `PermissionDenied` cair em página técnica.

---

## 5. Matriz atual (referência)

| Módulo | Permissão de acesso | Papel | Comportamento |
| --- | --- | --- | --- |
| Cursos | `courses.access_courses` | Professor / Aluno | Vê as próprias matrículas, aulas e quizzes. |
| Presença | `courses.access_presence` | Professor | Vê suas turmas (staff: todas), roster, cria/abre/fecha chamada e remove presença. Só na própria turma. |
| Presença | `courses.access_presence` | Aluno | Vê as turmas em que está matriculado, faz check-in em chamada aberta e vê só a própria presença. Sem roster. |
| Presença | `courses.manage_presence` | Professor | Ações de gestão (criar sessão, abrir/fechar, remover). |
| Presença | `courses.checkin_presence` | Aluno | Registrar a própria presença. |

Superuser (`admin@indes.dev`) ignora todos os portões.

---

## 6. Anti-padrões

* `if request.user.is_staff:` no corpo da view como única proteção.
* Checar `user.groups.filter(name='Professor')` diretamente — use permissões.
* Decorar só a view de listagem e esquecer as de detalhe/ação.
* Confiar na permissão de grupo sem checar o escopo do objeto.
* Devolver `redirect()` em vez de 403 quando o usuário autenticado não tem
  permissão — isso mascara falhas de autorização.