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
CUSTOMERS = (
    "Northstar Outdoor",
    "Maple Retail",
    "Solstice Living",
    "Pacific Outfitters",
)
SUPPLIERS = ("Alpine Components", "Meridian Textiles", "Seabright Goods")
# Ongoing Demo Data buyers: the profile customers first, then additional buyers.
# Order matters: earlier customers receive more synthetic demand than later ones.
DEMO_DATA_CUSTOMERS = tuple(
    (f"C{index}", name) for index, name in enumerate(CUSTOMERS, 1)
) + (
    ("C5", "Brightwater Home"),
    ("C6", "Juniper Trading Co."),
    ("C7", "Lakeside Provisions"),
    ("C8", "Fjord Outfitters"),
    ("C9", "Harlow Interiors"),
    ("C10", "Tidewater Sports"),
    ("C11", "Evergreen Studio"),
    ("C12", "Copperline Goods"),
    ("C13", "Granite Peak Gear"),
    ("C14", "Willow & Finch"),
    ("C15", "Northbridge Office Supply"),
    ("C16", "Blue Heron Living"),
    ("C17", "Marlow Home Goods"),
    ("C18", "Silverbirch Design"),
    ("C19", "Cascade Trail Company"),
    ("C20", "Amber Coast Retail"),
)
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
