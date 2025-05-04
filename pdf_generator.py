# pdf_generator.py (Fixed type check for multiple choice)
import random
import streamlit as st

# Import e controllo per WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
except OSError as e:
     st.error(f"Errore nell'import di WeasyPrint (probabili dipendenze mancanti come Pango/Cairo): {e}")
     WEASYPRINT_AVAILABLE = False


def generate_pdf_data(tests_data_lists, subject_name, status_callback, pdf_strings):
    """
    Genera dati PDF. Chiama status_callback solo per errori WeasyPrint.
    """
    if not WEASYPRINT_AVAILABLE:
        status_callback("error", "PG_WEASYPRINT_UNAVAILABLE")
        return None

    # CSS (invariato)
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

    html_parts = []
    checkbox_char = "☐"
    safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;') if subject_name else "Materia Non Specificata"
    title_format = pdf_strings.get("title_format", "Test for {subject_name}")
    name_label = pdf_strings.get("name_label", "Name:")
    date_label = pdf_strings.get("date_label", "Date:")
    class_label = pdf_strings.get("class_label", "Class:")
    missing_question_text = pdf_strings.get("missing_question", "MISSING QUESTION")
    no_options_text = pdf_strings.get("no_options", "<em>(No answer options provided)</em>")

    for index, single_test_data in enumerate(tests_data_lists):
        test_title = title_format.format(subject_name=safe_subject_name)
        test_html = f'<h2>{test_title}</h2>\n<div class="pdf-header-info">\n'
        test_html += f'  <div class="header-line"><span class="header-label">{name_label}</span><span class="header-underline"></span></div>\n'
        test_html += f'  <div class="header-line"><span class="header-label">{date_label}</span><span class="header-underline date-line"></span><span class="header-label class-label">{class_label}</span><span class="header-underline class-line"></span></div>\n</div>\n'
        q_counter = 1
        for question_data in single_test_data:
            q_text = question_data.get('question', missing_question_text).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data.get('type', 'Aperte') # Default ad Aperte se manca tipo
            nbsp = "&nbsp;"
            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'

            # --- CORREZIONE QUI: Usa 'Scelta Multipla' ---
            # --- CORRECTION HERE: Use 'Scelta Multipla' ---
            if q_type == 'Scelta Multipla':
            # --- FINE CORREZIONE ---
                answers = question_data.get('answers', []).copy(); random.shuffle(answers)
                if not answers: test_html += f'<p class="answer">{no_options_text}</p>\n'
                else:
                    for answer in answers:
                        ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                        test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            # Nessun blocco else necessario, le domande aperte non hanno output extra
            # No else block needed, open-ended questions have no extra output
            q_counter += 1
        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')

    final_html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Verifiche Generate</title><style>{css_style}</style></head><body>{"".join(html_parts)}</body></html>'

    try:
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf()
        return pdf_bytes
    except FileNotFoundError as e:
        status_callback("error", "PG_WEASYPRINT_DEPENDENCY_ERROR", error=e)
        return None
    except Exception as e:
        status_callback("error", "PG_WEASYPRINT_OTHER_ERROR", error=e)
        return None
