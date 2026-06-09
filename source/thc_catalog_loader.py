"""Normalized catalog loading routines for PostgreSQL sync."""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from psycopg2.extras import Json


def load_normalized(
    cursor: Any,
    catalogs: dict[str, Any],
    lang: str,
    sync_run_id: int,
    insert_values: Callable[..., int],
    records: Callable[[Any], list[tuple[str, Any]]],
    relation_rows: Callable[..., Iterable[tuple[Any, ...]]],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    categories = catalogs.get("categories", [])
    counts["item_categories"] = insert_values(
        cursor,
        "item_categories",
        (
            "category_id",
            "lang",
            "title",
            "default_subcategory_id",
            "payload",
            "sync_run_id",
        ),
        (
            (
                str(item["id"]),
                lang,
                item.get("title"),
                item.get("default"),
                Json(item),
                sync_run_id,
            )
            for item in categories
        ),
    )
    counts["item_subcategories"] = insert_values(
        cursor,
        "item_subcategories",
        (
            "subcategory_id",
            "category_id",
            "lang",
            "title",
            "payload",
            "sync_run_id",
        ),
        (
            (
                str(subcategory["id"]),
                str(category["id"]),
                lang,
                subcategory.get("title"),
                Json(subcategory),
                sync_run_id,
            )
            for category in categories
            for subcategory in category.get("subcategories", [])
        ),
    )

    items = catalogs.get("items", [])
    counts["items"] = insert_values(
        cursor,
        "items",
        (
            "item_id",
            "lang",
            "define",
            "name",
            "category_id",
            "subcategory_id",
            "item_type",
            "payload",
            "sync_run_id",
        ),
        (
            (
                item["id"],
                lang,
                item.get("define"),
                item.get("name"),
                str(item.get("cat")) if item.get("cat") is not None else None,
                str(item["subcat"]["id"])
                if isinstance(item.get("subcat"), dict)
                else None,
                str(item.get("type")) if item.get("type") is not None else None,
                Json(item),
                sync_run_id,
            )
            for item in items
        ),
    )

    species = catalogs.get("species", [])
    counts["species"] = insert_values(
        cursor,
        "species",
        ("species_id", "lang", "define", "name", "short_name", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("define"),
                item.get("name"),
                item.get("short"),
                Json(item),
                sync_run_id,
            )
            for item in species
        ),
    )

    reserves = catalogs.get("reserves", [])
    counts["reserves"] = insert_values(
        cursor,
        "reserves",
        ("reserve_id", "lang", "define", "name", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("define"),
                item.get("name"),
                Json(item),
                sync_run_id,
            )
            for item in reserves
        ),
    )
    counts["reserve_species"] = insert_values(
        cursor,
        "reserve_species",
        ("reserve_id", "species_id", "lang", "sync_run_id"),
        relation_rows(reserves, "id", "species", lang, sync_run_id),
    )

    counts["locations"] = insert_values(
        cursor,
        "locations",
        (
            "location_id",
            "lang",
            "reserve_id",
            "define",
            "name",
            "location_type",
            "payload",
            "sync_run_id",
        ),
        (
            (
                item["id"],
                lang,
                item.get("reserve"),
                item.get("define"),
                item.get("name"),
                item.get("type"),
                Json(item),
                sync_run_id,
            )
            for item in catalogs.get("locations", [])
        ),
    )

    missions = catalogs.get("missions", [])
    counts["missions"] = insert_values(
        cursor,
        "missions",
        ("mission_id", "lang", "title", "description", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("title"),
                item.get("desc"),
                Json(item),
                sync_run_id,
            )
            for item in missions
        ),
    )
    for table, relation_key, relation_column in (
        ("mission_species", "species", "species_id"),
        ("mission_weapons", "weapons", "item_id"),
        ("mission_reserves", "reserves", "reserve_id"),
        ("mission_dependencies", "dependencies", "dependency_mission_id"),
    ):
        counts[table] = insert_values(
            cursor,
            table,
            (
                "mission_id",
                relation_column,
                "lang",
                "sync_run_id",
            ),
            relation_rows(missions, "id", relation_key, lang, sync_run_id),
        )

    mission_groups = catalogs.get("mission_groups", [])
    counts["mission_groups"] = insert_values(
        cursor,
        "mission_groups",
        (
            "mission_group_id",
            "lang",
            "title",
            "description",
            "payload",
            "sync_run_id",
        ),
        (
            (
                item["id"],
                lang,
                item.get("title"),
                item.get("desc"),
                Json(item),
                sync_run_id,
            )
            for item in mission_groups
        ),
    )
    for table, relation_key, relation_column in (
        ("mission_group_missions", "missions", "mission_id"),
        ("mission_group_species", "species", "species_id"),
        ("mission_group_weapons", "weapons", "item_id"),
        ("mission_group_reserves", "reserves", "reserve_id"),
    ):
        counts[table] = insert_values(
            cursor,
            table,
            (
                "mission_group_id",
                relation_column,
                "lang",
                "sync_run_id",
            ),
            relation_rows(mission_groups, "id", relation_key, lang, sync_run_id),
        )

    counts["collectables"] = insert_values(
        cursor,
        "collectables",
        (
            "collectable_id",
            "lang",
            "define",
            "name",
            "category",
            "species_define",
            "payload",
            "sync_run_id",
        ),
        (
            (
                item["id"],
                lang,
                item.get("define"),
                item.get("name"),
                item.get("cat"),
                item.get("species_define"),
                Json(item),
                sync_run_id,
            )
            for item in catalogs.get("collectables", [])
        ),
    )

    counts["achievements"] = insert_values(
        cursor,
        "achievements",
        (
            "achievement_id",
            "lang",
            "title",
            "category_id",
            "group_id",
            "payload",
            "sync_run_id",
        ),
        (
            (
                item["id"],
                lang,
                item.get("title"),
                str(item.get("category")) if item.get("category") is not None else None,
                str(item.get("group")) if item.get("group") is not None else None,
                Json(item),
                sync_run_id,
            )
            for _, item in records(catalogs.get("achievements", {}))
        ),
    )
    counts["achievement_categories"] = insert_values(
        cursor,
        "achievement_categories",
        ("achievement_category_id", "lang", "title", "payload", "sync_run_id"),
        (
            (str(item["id"]), lang, item.get("title"), Json(item), sync_run_id)
            for _, item in records(catalogs.get("achievement_categories", {}))
        ),
    )
    counts["rank_categories"] = insert_values(
        cursor,
        "rank_categories",
        ("rank_category_id", "lang", "title", "rank_key", "payload", "sync_run_id"),
        (
            (
                str(item["id"]),
                lang,
                item.get("title"),
                item.get("key"),
                Json(item),
                sync_run_id,
            )
            for _, item in records(catalogs.get("ranks", {}))
        ),
    )
    counts["dog_skills"] = insert_values(
        cursor,
        "dog_skills",
        ("dog_skill_id", "lang", "level", "xp", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("lvl"),
                item.get("xp"),
                Json(item),
                sync_run_id,
            )
            for item in catalogs.get("dog_skills", [])
        ),
    )

    bundles = catalogs.get("bundles", [])
    counts["bundles"] = insert_values(
        cursor,
        "bundles",
        ("bundle_id", "lang", "define", "name", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("define"),
                item.get("name"),
                Json(item),
                sync_run_id,
            )
            for item in bundles
        ),
    )
    counts["bundle_items"] = insert_values(
        cursor,
        "bundle_items",
        ("bundle_id", "item_id", "lang", "quantity", "sync_run_id"),
        (
            (bundle["id"], item_id, lang, quantity, sync_run_id)
            for bundle in bundles
            for item_id, quantity in Counter(bundle.get("items", []) or []).items()
        ),
    )
    counts["tutorials"] = insert_values(
        cursor,
        "tutorials",
        ("tutorial_id", "lang", "reserve_id", "name", "payload", "sync_run_id"),
        (
            (
                item["id"],
                lang,
                item.get("reserve_id"),
                item.get("name"),
                Json(item),
                sync_run_id,
            )
            for item in catalogs.get("tutorials", [])
        ),
    )
    return counts
