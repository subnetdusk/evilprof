# pdf_generator.py (Modificato per i18n)
import random
import streamlit as st

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
except OSError as e:
     st.error(f"Errore nell'import di WeasyPrint (probabili dipendenze mancanti come Pango/Cairo): {e}")
     WEASYPRINT_AVAILABLE = False

# Funzione status_callback aspetta (msg_type, msg_key, **kwargs)
def generate_pdf_data(tests_data_lists, subject_name, status_callback, pdf_strings):
    """
    Genera i dati binari del PDF usando WeasyPrint.

    Args:
        tests_data_lists: Lista di liste (una per test) di dizionari domande.
        subject_name: Nome della materia per l'intestazione.
        status_callback: Funzione per inviare messaggi di stato/errore (aspetta chiave, kwargs).
        pdf_strings: Dizionario contenente i testi tradotti per il PDF
                     (es. title_format, name_label, date_label, class_label, ecc.).
    Returns:
        Bytes del PDF generato o None in caso di errore.
    """
    if not WEASYPRINT_AVAILABLE:
        # Invia chiave del messaggio
        status_callback("error", "PG_WEASYPRINT_UNAVAILABLE")
        return None

    status_callback("info", "PG_PDF_GENERATION_START")

    # CSS (rimane invariato)
    css_style = """
         @page { size: A4; margin: 2cm; }
         body { font-family: Verdana, sans-serif; font-size: 11pt; line-height: 1.4; }
         .test-container { }
         .page-break { page-break-before: always; }
         h2 { margin-bottom: 0.8em; font-size: 1.6em; color: #000; font-weight: bold; text-align: center; }
         .pdf-header-info { margin-bottom: 2.5em; font-size: 1em; font-weight: normal; line-height: 1.6; }
         .header-line { display: flex; align-items: baseline; width: 100%; margin-bottom: 0.6em; }
         .header-label { white-space: nowrap; margin-right: 0.5em; flex-shrink: 0; }
         .header-underline { flex-grow: 1; border-bottom: 1px solid black; position: relative; top: -2px; min-width: 40px; }
         .class-label { margin-left: 2.5em; }
         .question { margin-top: 1.8em; margin-bottom: 0.4em; font-weight: bold; }
         .answer { display: flex; align-items: baseline; margin-left: 2.5em; margin-top: 0.1em; margin-bottom: 0.3em; padding-left: 0; text-indent: 0; }
         .checkbox { flex-shrink: 0; margin-right: 0.6em; font-family: 'DejaVu Sans', sans-serif; }
         .answer-text { }
    """

    status_callback("info", "PG_HTML_BUILDING")
    html_parts = []
    checkbox_char = "☐"
    safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;') if subject_name else "Subject Not Specified"

    # Usa i testi tradotti passati tramite pdf_strings
    title_format = pdf_strings.get("title_format", "Test for {subject_name}") # Default generico
    name_label = pdf_strings.get("name_label", "Name:")
    date_label = pdf_strings.get("date_label", "Date:")
    class_label = pdf_strings.get("class_label", "Class:")
    missing_question_text = pdf_strings.get("missing_question", "MISSING QUESTION")
    no_options_text = pdf_strings.get("no_options", "<em>(No answer options provided)</em>")


    for index, single_test_data in enumerate(tests_data_lists):
        # Intestazione usa testi tradotti
        # Applica formattazione al titolo
        test_title = title_format.format(subject_name=safe_subject_name)
        test_html = f'<h2>{test_title}</h2>\n'
        test_html += '<div class="pdf-header-info">\n'
        test_html += '  <div class="header-line">\n'
        # Usa name_label (Nota: 'Nome e Cognome' era specifico IT)
        test_html += f'    <span class="header-label">{name_label}</span><span class="header-underline"></span>\n'
        test_html += '  </div>\n'
        test_html += '  <div class="header-line">\n'
        test_html += f'    <span class="header-label">{date_label}</span><span class="header-underline date-line"></span>'
        test_html += f'    <span class="header-label class-label">{class_label}</span><span class="header-underline class-line"></span>\n'
        test_html += '  </div>\n'
        test_html += '</div>\n'

        q_counter = 1
        for question_data in single_test_data:
            q_text = question_data.get('question', missing_question_text).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data.get('type', 'open_ended')
            nbsp = "&nbsp;"

            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'

            if q_type == 'multiple_choice':
                answers = question_data.get('answers', []).copy()
                random.shuffle(answers)
                if not answers:
                     test_html += f'<p class="answer">{no_options_text}</p>\n' # Usa testo tradotto
                else:
                    for answer in answers:
                        ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                        test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'

            q_counter += 1

        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')

    final_html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Generated Tests</title><style>{css_style}</style></head><body>{"".join(html_parts)}</body></html>'

    status_callback("info", "PG_PDF_CONVERTING")
    try:
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf()
        status_callback("info", "PG_PDF_CONVERSION_COMPLETE")
        return pdf_bytes
    except FileNotFoundError as e:
        status_callback("error", "PG_WEASYPRINT_DEPENDENCY_ERROR", error=e)
        return None
    except Exception as e:
        status_callback("error", "PG_WEASYPRINT_OTHER_ERROR", error=e)
        return None
