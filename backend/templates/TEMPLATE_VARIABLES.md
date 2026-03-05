# Sankalpam template variables (Telugu / Panchang)

Use these **exact** placeholders in template files. Spelling and case must match.

## Panchang / calendar (ఋతౌ … యోగే etc.)

| Placeholder   | Meaning    | Example value (Telugu) |
|---------------|------------|-------------------------|
| `{{rithou}}`  | Season     | వసంతం, గ్రీష్మం, వర్షం, … |
| `{{mAsE}}`    | Month      | మాఘం, ఫాల్గుణం, …       |
| `{{pakshE}}`  | Paksha     | కృష్ణ, శుక్ల             |
| `{{thithou}}` | Tithi      | ఏకాదశి, ప్రథమ, …        |
| `{{vAsara}}`  | Weekday    | సోమవారం, మంగళవారం, …  |
| `{{nakshatra}}` | Nakshatra | మూల, ధనిష్ఠ, …         |
| `{{yoga}}`    | Yoga       | హర్షణ, విష్కుంభ, …      |
| `{{karaNa}}`  | Karana     | బవ, బాలవ, …             |
| `{{ayanam}}`  | Ayana      | ఉత్తరాయణే, దక్షిణాయణే  |

**Correct line in template:**

```
{{rithou}} ఋతౌ
{{mAsE}} మాసే
{{pakshE}} పక్షే
{{thithou}} తిథౌ
{{vAsara}} వారే
{{nakshatra}} నక్షత్రే
{{yoga}} యోగే
{{karaNa}} కరణే
{{ayanam}} ॥
```

**Important:** Use `{{vAsara}}` (capital A), `{{mAsE}}` (capital A and E), and `{{karaNa}}` (capital N). Other placeholders are lowercase.

## Other common variables

- `{{samvathsarE}}` – year  
- `{{geographical_reference}}`, `{{current_location}}`, `{{geographical_feature}}`  
- `{{user_name}}`, `{{gotram}}`, `{{birth_nakshatra}}`, `{{birth_rashi}}`, `{{birth_place}}`, `{{birth_time}}`, `{{birth_city}}`, `{{birth_state}}`, `{{birth_country}}`, `{{birth_date}}`  
- `{{family_members}}`, `{{pooja_name}}`
