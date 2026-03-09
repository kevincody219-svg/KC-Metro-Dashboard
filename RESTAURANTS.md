# How to Add Restaurants

Edit `data/restaurants.json` to add your curated restaurant picks. The sidebar will show them when you click on an area.

## Format

```json
{
  "restaurants": {
    "clt-south-end": [
      { "name": "Seoul Food Meat Co.", "cuisine": "Korean BBQ", "rating": 4.5, "price": "$$" },
      { "name": "Superica", "cuisine": "Tex-Mex", "rating": 4.4, "price": "$$" }
    ],
    "clt-noda": [
      { "name": "Haberdish", "cuisine": "Southern", "rating": 4.6, "price": "$$" }
    ],
    "ral-downtown": [
      { "name": "Poole's Diner", "cuisine": "Southern", "rating": 4.6, "price": "$$" }
    ]
  }
}
```

## Fields

- **name** (required) — Restaurant name
- **cuisine** (required) — Cuisine type or short description
- **rating** (optional) — Google star rating like 4.5
- **price** (optional) — Price level like "$", "$$", "$$$", "$$$$"

## Area IDs

Use these as keys in the JSON:

**Charlotte neighborhoods:**
clt-uptown, clt-south-end, clt-noda, clt-plaza-midwood, clt-dilworth, clt-myers-park, clt-elizabeth, clt-montford, clt-wesley-heights, clt-eastway-shamrock, clt-university, clt-ballantyne

**Charlotte towns:**
clt-lake-norman, clt-north-iredell, clt-cabarrus, clt-matthews-mint-hill, clt-indian-trail-stallings, clt-gastonia

**Raleigh neighborhoods:**
ral-downtown, ral-north-hills, ral-five-points, ral-oakwood-mordecai, ral-cameron-village, ral-glenwood-south, ral-boylan-heights, ral-warehouse

**Raleigh towns:**
ral-cary, ral-apex, ral-holly-springs, ral-wake-forest, ral-garner, ral-knightdale-wendell, ral-clayton
