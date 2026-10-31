import sqlite3
from urllib.parse import urlencode
from fastapi import HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from localbrain.app.forms import FormError, bounded_urlencoded_form
from localbrain.persistence.db import connect
from localbrain.natural_search.presentation import (
    safe_return as natural_search_return,
    state_copy as natural_search_state,
)
from localbrain.app.request_guards import _auto_work_local_request
from localbrain.app.templating import templates


def _natural_search_status(request):
    try:
        return natural_search_state(request.app.state.natural_search.status())
    except (ValueError, OSError, sqlite3.Error):
        return natural_search_state({"state": "failed"})


def natural_search_page(request: Request, q: str = Query(default="", max_length=300),
                        page: int = Query(default=1, ge=1, le=1000000),
                        mode: str = Query(default="keyword", pattern="^(keyword|ai)$")):
    _auto_work_local_request(request)
    if mode == "keyword":
        from localbrain.search.keyword import keyword_search
        with connect() as connection:
            results = keyword_search(connection, q) if q.strip() else []
        return templates.TemplateResponse(request, "keyword-search.html", {
            "request": request, "active_page": "natural-search", "natural_query": q,
            "results": results, "search_status": _natural_search_status(request), "search_mode": "keyword",
        })
    status, result, query_error = _natural_search_status(request), None, None
    if q.strip() and status["state"] not in {"disabled", "model-missing", "no-data"}:
        try:
            result = request.app.state.natural_search.search(q, page=page)
            if result["partial"]:
                status = natural_search_state({**status, "state": "partial"})
        except (ValueError, OSError, sqlite3.Error, RuntimeError) as error:
            if str(error) == "SEARCH_INPUT_TOO_LONG":
                query_error = "검색어를 더 짧게 입력해 주세요. 이 표현은 검색 모델의 입력 한도를 넘었습니다."
            elif str(error) != "SEARCH_INDEX_UNAVAILABLE":
                query_error = "검색을 완료하지 못했습니다. 잠시 후 다시 검색해 주세요."
    return templates.TemplateResponse(request, "natural-search.html", {
        "request": request, "active_page": "natural-search", "natural_query": q,
        "search_status": status, "search_response": result, "query_error": query_error, "search_mode": "ai",
        "previous_url": "/natural-search?" + urlencode({"q": q, "mode": "ai", "page": max(1, page - 1)}),
        "next_url": "/natural-search?" + urlencode({"q": q, "mode": "ai", "page": page + 1}),
    })


def natural_search_status(request: Request):
    _auto_work_local_request(request)
    return JSONResponse(_natural_search_status(request), headers={"Cache-Control": "no-store"})


async def _natural_search_action(request, *, cancel=False):
    _auto_work_local_request(request)
    try:
        form = await bounded_urlencoded_form(request)
        query = form.get("q", "")
        if len(query) > 300:
            raise ValueError("INVALID_SEARCH_QUERY")
    except (FormError, ValueError) as error:
        raise HTTPException(422, "검색어 또는 요청 형식을 확인해 주세요.") from error
    if cancel:
        request.app.state.natural_search.cancel()
    else:
        try:
            request.app.state.natural_search.request_prepare()
        except (OSError, ValueError) as error:
            raise HTTPException(503, "검색 설정을 저장하지 못했습니다.") from error
    return RedirectResponse("/natural-search?" + urlencode({"q": query, "mode": "ai"}), status_code=303)


async def natural_search_prepare(request: Request):
    return await _natural_search_action(request)


async def natural_search_cancel(request: Request):
    return await _natural_search_action(request, cancel=True)


def natural_search_evidence(request: Request, rowid: int,
                            generation: str = Query(default="", max_length=64),
                            return_to: str = Query(default="/natural-search", max_length=4000)):
    _auto_work_local_request(request)
    evidence = None
    try:
        evidence = request.app.state.natural_search.evidence(rowid, generation)
    except (ValueError, OSError, sqlite3.Error, RuntimeError):
        pass
    return templates.TemplateResponse(request, "natural-search-evidence.html", {
        "request": request, "active_page": "natural-search", "evidence": evidence,
        "return_to": natural_search_return(return_to),
    }, status_code=200 if evidence else 409)
