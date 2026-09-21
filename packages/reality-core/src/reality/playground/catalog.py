"""Synthetic trading-v1 references, deliberately without opening stock."""

PRESET_KEY = "trading"
PRESET_VERSION = 1
LESSON_KEY = "order-stock"
LESSON_VERSION = 1

# Only executable lessons belong here; planned learning goals are not capabilities.
PRESETS = (
    {
        "key": PRESET_KEY,
        "version": PRESET_VERSION,
        "lesson_key": LESSON_KEY,
        "lesson_version": LESSON_VERSION,
    },
    {
        "key": "partial-delivery",
        "version": 1,
        "lesson_key": "partial-delivery",
        "lesson_version": 1,
    },
)


def find_preset(key: str, version: int) -> dict | None:
    supported_company_profile = (
        key == "international-demo" and version in {1, 2, 3, 4, 5}
    ) or (key in {"company-empty", "atlas-execution"} and version == 1)
    if supported_company_profile:
        return {
            "key": key,
            "version": version,
            "lesson_key": LESSON_KEY,
            "lesson_version": LESSON_VERSION,
        }
    return next(
        (
            preset
            for preset in PRESETS
            if preset["key"] == key and preset["version"] == version
        ),
        None,
    )


PARTIES = (
    ("company", "Acme", "company"),
    ("customer_mueller", "Müller", "customer"),
    ("customer_huber", "Huber", "customer"),
    ("supplier", "LightWorks", "supplier"),
)
WAREHOUSE = "Augsburg"
ITEMS = (("BIKE-LIGHT", "Bike Light"), ("HELMET", "Helmet"), ("BIKE-BELL", "Bike Bell"))
