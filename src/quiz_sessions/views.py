import io

import qrcode
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.db.models import F
from django.views.decorators.csrf import ensure_csrf_cookie

from quizzes.models import Quiz, Question, Option
from .models import Session, Participant, ParticipantAnswer
from .utils import generate_session_code


@login_required
def create_session(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    session = Session.objects.create(
        quiz=quiz,
        code=generate_session_code(6),
        status=Session.Status.WAITING,
        current_question=None,
    )
    return redirect("host_session", code=session.code)


@login_required
def host_session(request, code: str):
    session = get_object_or_404(Session, code=code)

    # Защита: только владелец викторины
    if session.quiz.owner_id != request.user.id:
        raise Http404("Session not found")

    error = None

    # Обработка кнопок управления (POST)
    if request.method == "POST":
        action = request.POST.get("action")

        # Вопросы викторины в правильном порядке
        questions = list(session.quiz.questions.order_by("order", "id"))

        if action == "start":
            if not questions:
                error = "В этой викторине нет вопросов. Добавь хотя бы один вопрос."
            else:
                session.status = Session.Status.RUNNING
                session.current_question = questions[0]
                session.save(update_fields=["status", "current_question"])

                return redirect("host_session", code=session.code)

        elif action == "next":
            if session.status != Session.Status.RUNNING:
                error = "Сессию нельзя переключать, пока она не запущена."
            elif not questions:
                error = "Нет вопросов."
            elif session.current_question is None:
                # Если почему-то пусто — ставим первый
                session.current_question = questions[0]
                session.save(update_fields=["current_question"])
                return redirect("host_session", code=session.code)
            else:
                # Найти текущий индекс и перейти на следующий
                try:
                    idx = next(i for i, q in enumerate(questions) if q.id == session.current_question_id)
                except StopIteration:
                    idx = -1

                next_idx = idx + 1
                if next_idx >= len(questions):
                    # Вопросы закончились -> завершаем
                    session.status = Session.Status.FINISHED
                    session.current_question = None
                    session.save(update_fields=["status", "current_question"])
                    return redirect("host_session", code=session.code)

                session.current_question = questions[next_idx]
                session.save(update_fields=["current_question"])
                return redirect("host_session", code=session.code)

        elif action == "finish":
            session.status = Session.Status.FINISHED
            session.current_question = None
            session.save(update_fields=["status", "current_question"])
            return redirect("host_session", code=session.code)

        else:
            error = "Неизвестное действие."

    # Для отображения прогресса
    questions = list(session.quiz.questions.order_by("order", "id"))
    current_index = None
    if session.current_question_id:
        for i, q in enumerate(questions):
            if q.id == session.current_question_id:
                current_index = i + 1  # 1-based
                break
    join_url = request.build_absolute_uri(f"/sessions/join/{session.code}/")

    return render(
        request,
        "quiz_sessions/host_session.html",
        {
            "session": session,
            "error": error,
            "questions_total": len(questions),
            "current_index": current_index,
            "join_url": join_url,
        },
    )

@login_required
def session_qr_png(request, code: str):
    """
    Отдаёт QR-картинку (PNG) для входа участника в сессию.
    Доступно только владельцу викторины.
    """
    session = get_object_or_404(Session, code=code)

    # Защита: только владелец
    if session.quiz.owner_id != request.user.id:
        raise Http404("Session not found")

    join_url = request.build_absolute_uri(f"/sessions/join/{session.code}/")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(join_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return HttpResponse(buf.getvalue(), content_type="image/png")

@require_http_methods(["GET", "POST"])
def join_session(request, code: str):
    """
    Участник заходит по QR: /join/<code>/
    Вводит имя -> создаём Participant -> сохраняем id в django-session -> редирект на /play/<code>/
    """
    session = get_object_or_404(Session, code=code)

    if session.status == Session.Status.FINISHED:
        return render(request, "quiz_sessions/join.html", {"session": session, "error": "Сессия уже завершена."})

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()

        if not name:
            error = "Введите имя."
        elif len(name) > 50:
            error = "Имя слишком длинное (макс 50 символов)."
        else:
            # уникальность имени в рамках сессии
            if Participant.objects.filter(session=session, name=name).exists():
                error = "Это имя уже занято в этой комнате. Выберите другое."
            else:
                p = Participant.objects.create(session=session, name=name)

                # запоминаем участника в django-сессии
                request.session[f"participant_id:{session.code}"] = p.id
                return redirect("play_session", code=session.code)

    return render(request, "quiz_sessions/join.html", {"session": session, "error": error})


def _get_participant_or_redirect(request, session: Session):
    """
    Достаём participant_id из django-session.
    Если нет — отправляем на join.
    """
    pid = request.session.get(f"participant_id:{session.code}")
    if not pid:
        return None

    try:
        return Participant.objects.get(id=pid, session=session)
    except Participant.DoesNotExist:
        return None


def play_session(request, code: str):
    """
    Страница участника: показывает текущий вопрос (если есть),
    иначе "ждите". Отправка ответов отдельным POST.
    """
    session = get_object_or_404(Session, code=code)
    participant = _get_participant_or_redirect(request, session)
    if participant is None:
        return redirect("join_session", code=session.code)

    return render(
        request,
        "quiz_sessions/play.html",
        {"session": session, "participant": participant},
    )


def session_state(request, code: str):
    """
    JSON для polling: состояние сессии и текущий вопрос.
    Клиент дёргает раз в 1-2 сек.
    """
    session = get_object_or_404(Session, code=code)
    participant = _get_participant_or_redirect(request, session)
    if participant is None:
        return JsonResponse({"error": "not_joined"}, status=401)

    data = {
        "status": session.status,
        "participant": {"name": participant.name, "score": participant.score},
        "current_question": None,
        "already_answered": False,
    }

    if session.current_question_id:
        q = session.current_question
        options = list(q.options.order_by("id").values("id", "text"))

        already = ParticipantAnswer.objects.filter(participant=participant, question=q).exists()

        data["current_question"] = {
            "id": q.id,
            "text": q.text,
            "options": options,
        }
        data["already_answered"] = already

    return JsonResponse(data)


@require_http_methods(["POST"])
def submit_answer(request, code: str):
    """
    Участник отправляет ответ на текущий вопрос.
    Начисляем 1 балл за правильный.
    """
    session = get_object_or_404(Session, code=code)
    participant = _get_participant_or_redirect(request, session)
    if participant is None:
        return JsonResponse({"error": "not_joined"}, status=401)

    if session.status != Session.Status.RUNNING or session.current_question_id is None:
        return JsonResponse({"error": "not_running"}, status=400)

    q = session.current_question

    # запрет повторного ответа
    if ParticipantAnswer.objects.filter(participant=participant, question=q).exists():
        return JsonResponse({"ok": True, "already_answered": True})

    try:
        option_id = int(request.POST.get("option_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "bad_option"}, status=400)

    option = get_object_or_404(Option, id=option_id, question=q)
    is_correct = bool(option.is_correct)

    ParticipantAnswer.objects.create(
        participant=participant,
        question=q,
        option=option,
        is_correct=is_correct,
    )

    if is_correct:
        participant.score += 1
        participant.save(update_fields=["score"])

    return JsonResponse({"ok": True, "is_correct": is_correct, "score": participant.score})

@login_required
def host_results(request, code: str):
    session = get_object_or_404(Session, code=code)

    # только владелец викторины
    if session.quiz.owner_id != request.user.id:
        raise Http404("Session not found")

    participants = (
        session.participants
        .all()
        .order_by("-score", "joined_at", "id")
    )

    return render(
        request,
        "quiz_sessions/host_results.html",
        {
            "session": session,
            "participants": participants,
        },
    )

@ensure_csrf_cookie
def play_session(request, code: str):
    session = get_object_or_404(Session, code=code)
    participant = _get_participant_or_redirect(request, session)
    if participant is None:
        return redirect("join_session", code=session.code)

    return render(request, "quiz_sessions/play.html", {"session": session, "participant": participant})


def final_session(request, code: str):
    session = get_object_or_404(Session, code=code)
    participant = _get_participant_or_redirect(request, session)
    if participant is None:
        return redirect("join_session", code=session.code)

    # если ещё не finished — отправим обратно играть
    if session.status != Session.Status.FINISHED:
        return redirect("play_session", code=session.code)

    ordered = list(
        session.participants.all().order_by("-score", "joined_at", "id")
    )

    rank = None
    for i, p in enumerate(ordered, start=1):
        if p.id == participant.id:
            rank = i
            break

    return render(
        request,
        "quiz_sessions/final.html",
        {
            "session": session,
            "participant": participant,
            "rank": rank,
            "total": len(ordered),
            "top": ordered[:10],
        },
    )

@login_required
def quiz_sessions_list(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner_id != request.user.id:
        raise Http404("Quiz not found")

    sessions = quiz.sessions.all().order_by("-created_at")

    return render(
        request,
        "quiz_sessions/quiz_sessions_list.html",
        {"quiz": quiz, "sessions": sessions},
    )

@login_required
def host_stats(request, code: str):
    session = get_object_or_404(Session, code=code)
    if session.quiz.owner_id != request.user.id:
        raise Http404("Session not found")

    return JsonResponse({
        "status": session.status,
        "participants": session.participants.count(),
        "current_question_id": session.current_question_id,
    })