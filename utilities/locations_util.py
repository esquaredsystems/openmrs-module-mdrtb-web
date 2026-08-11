"""
Location helpers, shared by two kinds of caller.

The patient screens (enrollment, report forms) need the live
REGION/DISTRICT/FACILITY hierarchy: non-retired locations only, with the built
hierarchy cached under the "locations" key.

Administration -> Manage Locations needs everything, retired rows included, and
is the only place that writes. Every write drops the cached hierarchy, so the
patient screens do not keep serving pre-edit names.

Admin traffic goes through utilities/rest_admin.py rather than restapi_utils so
that OpenMRS validation errors reach the user instead of a generic "an error
occurred", and so that lists are fetched page by page. Paging is deliberate:
the maximum page size is a server setting (webservices.rest.maxResultsAbsolute)
that has already reverted to its default once during a data migration, and
paging works whatever it is set to.
"""

import logging
from urllib.parse import quote

import utilities.restapi_utils as ru
from django.core.cache import caches
from resources.enums.constants import Constants

from utilities.rest_admin import (  # noqa: F401  (re-exported for the views)
    SessionExpired,
    get_all_pages as _get_all_pages,
    rest_delete as _delete,
    rest_get as _get,
    rest_post as _post,
)

logger = logging.getLogger("django")

metadata_cache = caches["metadata"]


# ---------------------------------------------------------------- reads


def get_locations(req, include_retired=False):
    """
    Every location, as a flat list.

    Retired locations are excluded unless include_retired is set — the admin
    tree's "show voided" toggle is the only caller that wants them.
    """
    params = {"v": "full"}
    if include_retired:
        # A normal REST query filters out retired metadata entirely.
        params["includeAll"] = "true"
    locations = _get_all_pages(req, "location", params)
    if include_retired:
        return locations
    return [location for location in locations if not location.get("retired")]


def get_location(req, uuid):
    """
    A single location, with its attributes.

    Falls back to the default representation if the full one fails, so one
    location with an attribute the server cannot serialise does not stop the
    edit screen from opening. The fallback is logged.
    """
    try:
        return _get(req, f"location/{uuid}", {"v": "full"})
    except SessionExpired:
        raise
    except Exception as e:
        logger.warning(
            f"v=full failed for location {uuid} ({e}); retrying with v=default. "
            "Attribute values will not be shown for this location."
        )
        return _get(req, f"location/{uuid}", {"v": "default"})


def get_location_site_codes(req):
    """Locations that carry a SITE_CODE attribute, sorted by that code."""
    site_codes = []
    for location in get_locations(req):
        for attribute in location.get("attributes") or []:
            attr_type = attribute.get("attributeType") or {}
            if attr_type.get("display") == "SITE_CODE":
                site_codes.append(
                    {"name": location["name"], "sitecode": attribute["value"]}
                )
                break
    return sorted(site_codes, key=lambda entry: entry["sitecode"])


def get_location_tags(req):
    """Non-retired location tags, alphabetical. Drives the tag checkboxes."""
    # No includeAll: retired tags should not be offered as choices.
    tags = [t for t in _get_all_pages(req, "locationtag", {"v": "full"}) if not t.get("retired")]
    return sorted(tags, key=lambda t: (t.get("name") or "").lower())


def get_location_attribute_types(req):
    """
    Non-retired location attribute types (currently just LEVEL).

    Each is annotated with:
      options  - choices parsed from handlerConfig ("UNKNOWN,REGION,...")
      multiple - True only when the server allows more than one value
                 (maxOccurs None or > 1). LEVEL has maxOccurs=1, so it renders
                 as a single-select and we never post two values.
    """
    types = []
    for attr_type in _get_all_pages(req, "locationattributetype", {"v": "full"}):
        if attr_type.get("retired"):
            continue
        max_occurs = attr_type.get("maxOccurs")
        attr_type["options"] = _parse_handler_options(attr_type.get("handlerConfig"))
        attr_type["multiple"] = max_occurs is None or max_occurs > 1
        attr_type["required"] = (attr_type.get("minOccurs") or 0) > 0
        types.append(attr_type)
    return sorted(types, key=lambda t: (t.get("name") or "").lower())


def _parse_handler_options(handler_config):
    """'UNKNOWN,REGION,SUBREGION' -> ['UNKNOWN', 'REGION', 'SUBREGION']."""
    if not handler_config:
        return []
    return [option.strip() for option in handler_config.split(",") if option.strip()]


def get_countries(locations):
    """Distinct non-empty country values, for the form's datalist."""
    countries = {
        (loc.get("country") or "").strip()
        for loc in locations
        if (loc.get("country") or "").strip()
    }
    return sorted(countries)


def _level_from_attributes(attributes):
    """
    The LEVEL value (REGION/DISTRICT/...) out of an attribute list, or None.

    Reads the attribute's value rather than re-parsing its display string
    ("LEVEL: REGION"), which is absent in some representations and used to
    raise AttributeError. Display is still used as a fallback.
    """
    for attribute in attributes or []:
        if (attribute.get("attributeType") or {}).get("uuid") != Constants.LEVEL.value:
            continue
        value = _attribute_display_value(attribute)
        if value:
            return value
        display = attribute.get("display") or ""
        return display.split(":")[1].strip() if ":" in display else None
    return None


def get_location_level(uuid, location_by_uuids):
    """The LEVEL of a location from a uuid-keyed lookup, or None."""
    return _level_from_attributes(location_by_uuids.get(uuid, {}).get("attributes"))


# ---------------------------------------------------------------- patient-facing hierarchy


def create_location_hierarchy(req):
    """
    The REGION -> DISTRICT -> FACILITY tree used by the patient-facing
    dropdowns. Cached; any admin write below clears it.
    """
    locations = metadata_cache.get("locations")
    if locations:
        return locations
    locations = get_locations(req)
    location_by_uuids = {location["uuid"]: location for location in locations}
    location_hierarchy = []

    for location in locations:
        if location.get("parentLocation") is None and not location.get("retired", True):
            location_hierarchy.append(
                {
                    "uuid": location["uuid"],
                    "name": location["name"],
                    "level": get_location_level(location["uuid"], location_by_uuids),
                    "children": [
                        {
                            "uuid": child["uuid"],
                            "name": child["name"],
                            "level": get_location_level(
                                child["uuid"], location_by_uuids
                            ),
                            "children": [
                                {
                                    "uuid": subchild["uuid"],
                                    "name": subchild.get("name", subchild["display"]),
                                    "level": get_location_level(
                                        subchild["uuid"], location_by_uuids
                                    ),
                                }
                                for subchild in child.get("childLocations", [])
                                if not subchild.get(
                                    "retired",
                                    location_by_uuids.get(
                                        subchild["uuid"], {"retired": True}
                                    )["retired"],
                                )
                            ]
                            if child.get("childLocations")
                            else [],
                        }
                        for child in location.get("childLocations", [])
                        if not child.get(
                            "retired",
                            location_by_uuids.get(child["uuid"], {"retired": True})[
                                "retired"
                            ],
                        )
                    ]
                    if location.get("childLocations")
                    else [],
                }
            )
    metadata_cache.set("locations", location_hierarchy)
    return location_hierarchy


def get_single_location_hierarchy(location):
    """Resolves one location into its {region, district, facility} ancestry."""
    location_hierarchy = {}
    level = _level_from_attributes(location.get("attributes"))

    if level and level == "REGION":
        location_hierarchy["region"] = {
            "uuid": location["uuid"],
            "name": location["name"],
        }
        location_hierarchy["district"] = None
        location_hierarchy["facility"] = None

    if level and level == "DISTRICT":
        location_hierarchy["district"] = {
            "uuid": location["uuid"],
            "name": location["name"],
        }
        location_hierarchy["region"] = {
            "uuid": location["parentLocation"]["uuid"],
            "name": location["parentLocation"]["display"],
        }
        location_hierarchy["facility"] = None

    if level and level == "FACILITY":
        location_hierarchy["facility"] = {
            "uuid": location["uuid"],
            "name": location["name"],
        }
        location_hierarchy["district"] = {
            "uuid": location["parentLocation"]["uuid"],
            "name": location["parentLocation"]["display"],
        }

        location_hierarchy["region"] = {
            "uuid": location["parentLocation"]["parentLocation"]["uuid"],
            "name": location["parentLocation"]["parentLocation"]["display"],
        }

    return location_hierarchy


# ---------------------------------------------------------------- admin tree


def _attribute_summary(location):
    """
    Returns ([{'name': 'LEVEL', 'value': 'REGION'}], duplicate_count).

    Identical (type, value) pairs are collapsed: locations in this database
    carry duplicate LEVEL attributes, which is invalid since LEVEL has
    maxOccurs=1. They are counted rather than silently hidden.
    """
    summary = []
    seen = set()
    duplicates = 0
    for attribute in location.get("attributes") or []:
        if attribute.get("voided"):
            continue
        attr_type = attribute.get("attributeType") or {}
        entry = {
            "name": attr_type.get("name") or attr_type.get("display") or "",
            "value": _attribute_display_value(attribute),
        }
        key = (entry["name"], entry["value"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        summary.append(entry)
    return summary, duplicates


def attribute_display_value(attribute):
    """Public alias of _attribute_display_value, for views and templates."""
    return _attribute_display_value(attribute)


def _attribute_display_value(attribute):
    """Attribute values arrive as a plain string or as a {uuid,display} object."""
    value = attribute.get("value")
    if isinstance(value, dict):
        return value.get("display") or value.get("uuid") or ""
    if value is None:
        return ""
    return str(value)


def build_location_tree(locations, include_retired=False):
    """
    Nests the flat list via parentLocation into a file-tree structure.

    A location whose parent was filtered out is promoted to a root rather than
    dropped, so nothing can silently disappear from the admin screen.
    """
    nodes = {}
    locations_with_duplicate_attributes = 0
    for location in locations:
        if location.get("retired") and not include_retired:
            continue
        parent = location.get("parentLocation") or {}
        attributes, duplicates = _attribute_summary(location)
        if duplicates:
            locations_with_duplicate_attributes += 1
        nodes[location["uuid"]] = {
            "uuid": location["uuid"],
            "name": location.get("name") or "",
            "retired": bool(location.get("retired")),
            "parent_uuid": parent.get("uuid"),
            "country": location.get("country") or "",
            "city_village": location.get("cityVillage") or "",
            "state_province": location.get("stateProvince") or "",
            "county_district": location.get("countyDistrict") or "",
            "attributes": attributes,
            "children": [],
        }

    if locations_with_duplicate_attributes:
        logger.warning(
            f"{locations_with_duplicate_attributes} location(s) carry duplicate "
            "attributes (same type and value more than once). LEVEL has "
            "maxOccurs=1, so this is invalid data. Duplicates are collapsed for "
            "display; saving a location here normalises it to a single value."
        )

    roots = []
    for node in nodes.values():
        parent_uuid = node["parent_uuid"]
        if parent_uuid and parent_uuid in nodes:
            nodes[parent_uuid]["children"].append(node)
        else:
            roots.append(node)

    def sort_recursive(branch):
        branch.sort(key=lambda n: (n["name"] or "").lower())
        for node in branch:
            sort_recursive(node["children"])

    sort_recursive(roots)
    return roots


def mark_voided_only_branches(tree):
    """
    Flags each node with voided_only: True when it must disappear while
    "show voided" is off. Returns True if this branch contains anything live.

    A retired node is hidden only when it has no live descendant. One that
    still has a live child stays visible as a struck-through structural parent,
    so a live location never vanishes because its parent was retired.
    """
    branch_has_live = False
    for node in tree:
        child_has_live = mark_voided_only_branches(node["children"])
        keep = (not node["retired"]) or child_has_live
        node["voided_only"] = not keep
        branch_has_live = branch_has_live or keep
    return branch_has_live


def count_tree_nodes(tree):
    return sum(1 + count_tree_nodes(node["children"]) for node in tree)


# ---------------------------------------------------------------- writes


def _invalidate_location_cache():
    """
    Drops the hierarchy cached by create_location_hierarchy(). Every write must
    call this, or the patient-facing dropdowns keep showing pre-edit names.
    """
    try:
        metadata_cache.delete("locations")
    except Exception as e:  # a cache outage must not fail an otherwise good save
        logger.warning(f"Could not invalidate location cache: {e}")


def build_location_payload(form):
    """
    Maps the POSTed form to the OpenMRS location resource.

    Empty strings become None so clearing a field actually clears it; an empty
    parent means a root location.
    """

    def clean(field):
        return (form.get(field) or "").strip() or None

    return {
        "name": (form.get("name") or "").strip(),
        "description": clean("description"),
        "address1": clean("address1"),
        "address2": clean("address2"),
        "cityVillage": clean("city_village"),
        "stateProvince": clean("state_province"),
        "countyDistrict": clean("county_district"),
        "country": clean("country"),
        "parentLocation": clean("parent_location"),
        "tags": form.getlist("tags") if hasattr(form, "getlist") else form.get("tags", []),
    }


def save_location(req, uuid, payload, attribute_values):
    """Updates core fields and tags, then reconciles attributes."""
    _post(req, f"location/{uuid}", payload)
    _sync_attributes(req, uuid, attribute_values)
    _invalidate_location_cache()
    return uuid


def create_location(req, payload, attribute_values):
    """Creates the location, then attaches its attributes."""
    created = _post(req, "location", payload) or {}
    new_uuid = created.get("uuid")
    if new_uuid and attribute_values:
        _sync_attributes(req, new_uuid, attribute_values)
    _invalidate_location_cache()
    return new_uuid


def _sync_attributes(req, location_uuid, attribute_values):
    """
    Reconciles attributes against the submitted {type_uuid: str | list} values.

    Attributes are managed through the /attribute subresource rather than by
    posting the whole array, which OpenMRS does not reliably apply on update.
    Values are paired positionally against the existing attributes of that type:
    overlapping ones are updated in place, surplus existing ones deleted,
    surplus new ones added. That keeps a single-valued type (LEVEL) to exactly
    one attribute while still supporting a multi-valued type.
    """
    if not attribute_values:
        return
    current = get_location(req, location_uuid) or {}
    existing_by_type = {}
    for attribute in current.get("attributes") or []:
        if attribute.get("voided"):
            continue
        type_uuid = (attribute.get("attributeType") or {}).get("uuid")
        if type_uuid:
            existing_by_type.setdefault(type_uuid, []).append(attribute)

    for type_uuid, submitted in attribute_values.items():
        if isinstance(submitted, (list, tuple)):
            desired = [str(v).strip() for v in submitted if str(v).strip()]
        else:
            desired = [str(submitted).strip()] if str(submitted or "").strip() else []
        existing = existing_by_type.get(type_uuid, [])

        for index, attribute in enumerate(existing):
            if index < len(desired):
                if _attribute_display_value(attribute) != desired[index]:
                    _post(
                        req,
                        f"location/{location_uuid}/attribute/{attribute['uuid']}",
                        {"value": desired[index]},
                    )
            else:
                _delete(req, f"location/{location_uuid}/attribute/{attribute['uuid']}")

        for value in desired[len(existing):]:
            _post(
                req,
                f"location/{location_uuid}/attribute",
                {"attributeType": type_uuid, "value": value},
            )


def retire_location(req, uuid, reason):
    """DELETE without purge = retire (soft delete) in OpenMRS."""
    reason = (reason or "").strip() or "Retired from MDR-TB administration screen"
    _delete(req, f"location/{uuid}?reason={quote(reason)}")
    _invalidate_location_cache()


def unretire_location(req, uuid):
    _post(req, f"location/{uuid}", {"retired": False})
    _invalidate_location_cache()
