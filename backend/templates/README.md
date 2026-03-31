# Sankalpam templates by language

Templates are organized by **Indian language** in subfolders. Each language folder can contain:

- **Pooja-specific:** `{Pooja_Name}_template_{language}.txt`  
  Example: `Ganesh_Pooja_template_telugu.txt` for Ganesh Pooja in Telugu.
- **Generic fallback:** `sankalpam_template_{language}.txt`  
  Example: `sankalpam_template_telugu.txt` used when no pooja-specific file exists.

The **Telugu** generic file (`telugu/sankalpam_template_telugu.txt`) is a copy of the **Sanskrit** generic (`sanskrit/sankalpam_template_sanskrit.txt`): the same Devanagari sankalpam text and `{{variables}}` so one template can serve Telugu language selection (e.g. TTS language) while keeping identical wording. The canonical source also lives at `backend/sample_sankalpam_template.txt`.

## Folder names (match language codes)

| Code | Folder   |
|------|----------|
| te   | telugu   |
| hi   | hindi    |
| sa   | sanskrit |
| ta   | tamil   |
| kn   | kannada  |
| ml   | malayalam |
| en   | english  |
| mr   | marathi  |
| gu   | gujarati |
| bn   | bengali  |
| or   | oriya    |
| pa   | punjabi  |

## Naming

- Pooja name from the app (e.g. "Ganesh Pooja") is normalized to filename: spaces → underscores, then `_template_{folder}.txt`.
- Use UTF-8 encoding for all template files.
