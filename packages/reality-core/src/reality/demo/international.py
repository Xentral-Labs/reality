"""Versioned synthetic vocabulary and authored comparison inputs."""

PROFILE_VERSION = 1
ITEMS = (
    ("P01", "Summit Bottle", "pcs", "Outdoor"),
    ("P02", "Trail Lantern", "pcs", "Outdoor"),
    ("P03", "Ridge Backpack", "pcs", "Outdoor"),
    ("P04", "Cedar Desk Lamp", "pcs", "Home"),
    ("P05", "Coast Storage Box", "pcs", "Home"),
    ("P06", "Harbor Travel Mug", "pcs", "Outdoor"),
    ("P07", "Aurora Notebook", "pcs", "Office"),
    ("P08", "Vista Monitor Stand", "pcs", "Office"),
    ("P09", "Maple Serving Tray", "pcs", "Home"),
    ("P10", "Orbit Cable Kit", "pcs", "Office"),
    ("P11", "Meadow Picnic Set", "pcs", "Outdoor"),
    ("P12", "Beacon Desk Organizer", "pcs", "Office"),
    ("P13", "Drift Cushion", "pcs", "Home"),
    ("P14", "Cove Glass Set", "pcs", "Home"),
    ("P15", "Meridian Fabric", "m", "Materials"),
    ("P16", "Alpine Wax Pellets", "kg", "Materials"),
)
# The whole buyer pool. The profile seeds it and the ongoing Demo Data stream draws
# from it, so the seeded order book and the arriving one name the same customers.
# Order matters: earlier customers receive more synthetic demand than later ones.
CUSTOMERS = (
    "Northstar Outdoor",
    "Maple Retail",
    "Solstice Living",
    "Pacific Outfitters",
    "Brightwater Home",
    "Juniper Trading Co.",
    "Lakeside Provisions",
    "Fjord Outfitters",
    "Harlow Interiors",
    "Tidewater Sports",
    "Evergreen Studio",
    "Copperline Goods",
    "Granite Peak Gear",
    "Willow & Finch",
    "Northbridge Office Supply",
    "Blue Heron Living",
    "Marlow Home Goods",
    "Silverbirch Design",
    "Cascade Trail Company",
    "Amber Coast Retail",
)
SUPPLIERS = ("Alpine Components", "Meridian Textiles", "Seabright Goods")
DEMO_DATA_CUSTOMERS = tuple(
    (f"C{index}", name) for index, name in enumerate(CUSTOMERS, 1)
)
# Feature 200: the buyer each seeded order states. Operational cases carry their own
# key; a comparison family resolves once so its prior and current window compare the
# same customer. Three regulars hold repeat business, every other buyer appears once.
ORDER_CUSTOMERS = {
    "O01": "C1",
    "O02": "C2",
    "O03": "C3",
    "O04": "C1",
    "O05": "C4",
    "O06": "C5",
    "O07": "C2",
    "O08": "C6",
    "O09": "C7",
    "O10": "C8",
    "E01": "C1",
    "E02": "C1",
    "volume": "C9",
    "price": "C10",
    "decline": "C11",
    "credit": "C12",
    "outlier": "C13",
    "zero": "C14",
    "usd": "C15",
}
# The twelve weekly history orders, oldest first: the regulars keep recurring through
# the trend while the remaining buyers each appear once.
WEEKLY_CUSTOMERS = (
    "C1",
    "C16",
    "C2",
    "C17",
    "C3",
    "C18",
    "C1",
    "C19",
    "C2",
    "C20",
    "C3",
    "C16",
)
# The supplier that makes each purchased material, so the three purchase orders state
# three suppliers instead of naming the first one three times.
SUPPLIER_ITEMS = {"P11": "S3", "P15": "S2", "P16": "S1"}
LOCATIONS = ("Rotterdam Warehouse", "Singapore Warehouse")
MINIMAL_ITEMS = frozenset({"P01", "P02", "P11", "P12"})
# Quantity, unit price and total are independently stated synthetic source inputs.
HISTORY = (
    ("volume-prior", "P11", 60, "10", "20", "200", "EUR"),
    ("volume-current", "P11", 20, "20", "20", "400", "EUR"),
    ("price-prior", "P12", 60, "10", "20", "200", "EUR"),
    ("price-current", "P12", 20, "10", "25", "250", "EUR"),
    ("decline-prior", "P13", 60, "20", "15", "300", "EUR"),
    ("decline-current", "P13", 20, "5", "15", "75", "EUR"),
    ("credit-origin", "P14", 18, "10", "12", "120", "EUR"),
    ("outlier-prior", "P15", 61, "10", "5", "50", "EUR"),
    ("outlier-current", "P15", 19, "1000", "5", "5000", "EUR"),
    ("zero-current", "P16", 15, "8", "10", "80", "EUR"),
    ("usd-prior", "P11", 65, "4", "22", "88", "USD"),
    ("usd-current", "P11", 16, "6", "22", "132", "USD"),
)

# Feature 168: the payment term every synthetic invoice states, so discount
# explanations can fire on short payments. Created or matched on connect.
DEMO_DATA_PAYMENT_TERM = {
    "code": "DEMO-14-2",
    "name": "14 days net, 2 % within 7 days",
    "due_days": 14,
    "discount_percent": "2",
    "discount_days": 7,
}
