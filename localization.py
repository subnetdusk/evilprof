# localization.py (Aggiunte chiavi per download Excel statistico)

TEXTS = {
    "it": {
        # ... [tutte le chiavi precedenti, incluse quelle per STAT_TEST_*] ...

        # Nuove chiavi per download Excel
        "STAT_TEST_EXCEL_CREATED": "✅ File Excel con risultati statistici '{filename}' creato.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Errore durante il salvataggio del file Excel '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ Nessun dato dettagliato raccolto per creare il file Excel.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Scarica Risultati Statistici (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Scarica il file Excel con l'analisi di similarità Jaccard per distanza e k.",

    },
    "en": {
        # ... [all previous keys, including STAT_TEST_*] ...

        # New keys for Excel download
        "STAT_TEST_EXCEL_CREATED": "✅ Excel file with statistical results '{filename}' created.",
        "STAT_TEST_EXCEL_SAVE_ERROR": "❌ Error saving Excel file '{filename}': {error}",
        "STAT_TEST_NO_DATA_FOR_EXCEL": "⚠️ No detailed data collected to create the Excel file.",
        "DOWNLOAD_STATS_EXCEL_LABEL": "📊 Download Statistical Results (.xlsx)",
        "DOWNLOAD_STATS_EXCEL_HELP": "Download the Excel file with the Jaccard similarity analysis by distance and k.",
    }
}

# Funzioni get_text e format_text (invariate)
# ... (codice delle funzioni helper come prima) ...
def get_text(lang_code, key):
    """Recupera il testo per una data chiave nella lingua specificata."""
    lang_dict = TEXTS.get(lang_code, TEXTS.get("en", {}))
    return lang_dict.get(key, f"MISSING_TEXT[{key}]")

def format_text(lang_code, key, **kwargs):
     """Recupera testo e lo formatta con i parametri forniti."""
     raw_text = get_text(lang_code, key)
     if raw_text == f"MISSING_TEXT[{key}]": return raw_text
     try: return raw_text.format(**kwargs)
     except KeyError as e: print(f"WARN: Missing placeholder key {e} in text key '{key}' for lang '{lang_code}' when formatting with {kwargs}"); return raw_text
     except Exception as e: print(f"WARN: Generic formatting error for text key '{key}' with args {kwargs} for lang '{lang_code}': {e}"); return raw_text

