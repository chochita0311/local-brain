from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .schema_presentation import load_schema_presentation


INVALID_AREA_MESSAGE = "해당 주제 영역을 찾을 수 없어 전체 모델을 표시합니다."
INVALID_TABLE_MESSAGE = "해당 영역에서 테이블을 찾을 수 없어 영역 개요를 표시합니다."
TABLE_REQUIRES_AREA_MESSAGE = "테이블을 보려면 먼저 주제 영역을 선택하세요."
UNAVAILABLE_MESSAGE = (
    "스키마 설명을 불러올 수 없습니다. 패키지 데이터가 갱신된 뒤 다시 시도하세요."
)


def schema_explorer_page_data(
    area: Optional[str] = None,
    table: Optional[str] = None,
) -> Dict[str, Any]:
    loaded = load_schema_presentation()
    if not loaded.available or loaded.manifest is None:
        return {
            "available": False,
            "error_code": loaded.error_code,
            "message": UNAVAILABLE_MESSAGE,
        }
    return build_schema_explorer_view(loaded.manifest, area=area, table=table)


def build_schema_explorer_view(
    manifest: Dict[str, Any],
    *,
    area: Optional[str] = None,
    table: Optional[str] = None,
) -> Dict[str, Any]:
    subjects_by_id = {subject["id"]: subject for subject in manifest["subjects"]}
    tables_by_id = {item["id"]: item for item in manifest["tables"]}

    selected_subject = subjects_by_id.get(area) if area is not None else None
    notice = None
    if area is not None and selected_subject is None:
        notice = {"code": "invalid-area", "message": INVALID_AREA_MESSAGE}

    selected_table = None
    if selected_subject is None:
        if table is not None and notice is None:
            notice = {
                "code": "table-requires-area",
                "message": TABLE_REQUIRES_AREA_MESSAGE,
            }
    elif table is not None:
        candidate = tables_by_id.get(table)
        if candidate is not None and candidate["subject_id"] == selected_subject["id"]:
            selected_table = candidate
        else:
            notice = {"code": "invalid-table", "message": INVALID_TABLE_MESSAGE}

    subject_views = [
        {
            **subject,
            "href": schema_href(area=subject["id"]),
            "current": selected_subject is not None
            and subject["id"] == selected_subject["id"],
        }
        for subject in manifest["subjects"]
    ]
    subject_view_by_id = {subject["id"]: subject for subject in subject_views}
    selected_subject_view = (
        subject_view_by_id[selected_subject["id"]] if selected_subject else None
    )

    area_tables: List[Dict[str, Any]] = []
    if selected_subject:
        area_tables = [
            {
                "id": table_id,
                "kind": tables_by_id[table_id]["kind"],
                "column_count": len(tables_by_id[table_id]["columns"]),
                "purpose": tables_by_id[table_id]["semantics"][
                    "purpose_and_authority"
                ],
                "href": schema_href(area=selected_subject["id"], table=table_id),
                "current": selected_table is not None and table_id == selected_table["id"],
            }
            for table_id in selected_subject["table_ids"]
        ]

    mode = "global"
    diagram = manifest["global"]["mermaid"]
    diagram_label = "전체 LocalBrain 데이터 모델"
    if selected_subject_view:
        mode = "table" if selected_table else "area"
        diagram = selected_subject_view["mermaid"]
        diagram_label = f"{selected_subject_view['label']} 관계 모델"

    relationships = {"physical": [], "application": []}
    if selected_table:
        for enforcement in relationships:
            relationships[enforcement] = [
                item
                for item in manifest["relationships"][enforcement]
                if selected_table["id"]
                in {item["source_table"], item["target_table"]}
            ]

    baseline = manifest["baseline"]
    return {
        "available": True,
        "schema": manifest["schema"],
        "mode": mode,
        "notice": notice,
        "baseline": {
            **baseline,
            "object_count": baseline["ordinary_table_count"]
            + baseline["fts5_table_count"],
        },
        "subjects": subject_views,
        "selected_subject": selected_subject_view,
        "area_tables": area_tables,
        "selected_table": selected_table,
        "relationships": relationships,
        "diagram": diagram,
        "diagram_label": diagram_label,
        "global_href": schema_href(),
    }


def schema_href(*, area: Optional[str] = None, table: Optional[str] = None) -> str:
    parameters = []
    if area is not None:
        parameters.append(("area", area))
    if table is not None:
        parameters.append(("table", table))
    return "/schema" + (f"?{urlencode(parameters)}" if parameters else "")
