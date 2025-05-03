# pdf_generator.py
import random
import streamlit as st # Per messaggi di errore specifici di WeasyPrint

# Import e controllo per WeasyPrint
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
except OSError as e:
     # Potrebbe mancare Pango/Cairo/GTK+ su alcuni sistemi
     st.error(f"Errore nell'import di WeasyPrint (probabili dipendenze mancanti come Pango/Cairo): {e}")
     WEASYPRINT_AVAILABLE = False


def generate_pdf_data(tests_data_lists, subject_name, status_callback):
    """
    Genera i dati binari del PDF usando WeasyPrint.

    Args:
        tests_data_lists: Lista di liste (una per test) di dizionari domande.
        subject_name: Nome della materia per l'intestazione.
        status_callback: Funzione per inviare messaggi di stato/errore.

    Returns:
        Bytes del PDF generato o None in caso di errore.
    """
    if not WEASYPRINT_AVAILABLE:
        status_callback("error", "Libreria WeasyPrint non trovata o non funzionante. Impossibile generare PDF.")
        return None

    status_callback("info", "⚙️ Inizio generazione PDF...")

    # CSS per la formattazione del PDF
    css_style = """
         @page {
             size: A4;
             margin: 2cm; /* Margini standard A4 */
         }
         body {
             font-family: Verdana, sans-serif; /* Font leggibile */
             font-size: 11pt;               /* Dimensione base */
             line-height: 1.4;              /* Interlinea per leggibilità */
         }
         .test-container {
             /* Contenitore per ogni singolo test */
         }
         .page-break {
             page-break-before: always; /* Ogni nuovo test inizia su una nuova pagina */
         }
         h2 {
             margin-bottom: 0.8em;
             font-size: 1.6em;
             color: #000; /* Nero semplice */
             font-weight: bold;
             text-align: center; /* Titolo centrato */
         }
         .pdf-header-info {
             margin-bottom: 2.5em; /* Spazio dopo l'intestazione */
             font-size: 1em;
             font-weight: normal;
             line-height: 1.6;
         }
         .header-line {
             display: flex;
             align-items: baseline; /* Allinea testo e linea */
             width: 100%;
             margin-bottom: 0.6em; /* Spazio tra le righe Nome/Data/Classe */
         }
         .header-label {
             white-space: nowrap; /* Evita che "Nome:", "Data:", "Classe:" vadano a capo */
             margin-right: 0.5em;
             flex-shrink: 0; /* Non ridurre l'etichetta */
         }
         .header-underline {
             flex-grow: 1; /* Occupa tutto lo spazio rimanente */
             border-bottom: 1px solid black; /* Linea per scrivere */
             position: relative;
             top: -2px; /* Allinea meglio la linea al testo */
             min-width: 40px; /* Larghezza minima per linee corte */
         }
         .class-label {
             margin-left: 2.5em; /* Spazio tra Data e Classe */
         }
         .question {
             margin-top: 1.8em;    /* Spazio sopra ogni domanda */
             margin-bottom: 0.4em; /* Spazio ridotto tra domanda e prima risposta */
             font-weight: bold;
         }
         .answer {
             display: flex;         /* Allinea checkbox e testo */
             align-items: baseline; /* Allinea la base del checkbox con il testo */
             margin-left: 2.5em;   /* Indentazione risposte */
             margin-top: 0.1em;    /* Spazio minimo sopra la risposta */
             margin-bottom: 0.3em; /* Spazio sotto la risposta */
             padding-left: 0;      /* Resetta padding default */
             text-indent: 0;       /* Resetta indentazione default */
         }
         .checkbox {
             flex-shrink: 0;      /* Non ridurre il checkbox */
             margin-right: 0.6em; /* Spazio tra checkbox e testo risposta */
             font-family: 'DejaVu Sans', sans-serif; /* Usa un font che sicuramente ha il quadrato vuoto */
         }
         .answer-text {
             /* Testo della risposta */
         }
         /* Lo spazio per risposte aperte è ora semplicemente lo spazio dopo la domanda .question */
    """

    status_callback("info", "⚙️ Costruzione documento HTML...")
    html_parts = []
    checkbox_char = "☐" # Carattere quadrato vuoto (meglio di un box unicode che potrebbe mancare)
    # Pulisce il nome materia per sicurezza HTML
    safe_subject_name = subject_name.replace('<', '&lt;').replace('>', '&gt;') if subject_name else "Materia Non Specificata"

    for index, single_test_data in enumerate(tests_data_lists):
        # Intestazione di ogni test
        test_html = f'<h2>Verifica di {safe_subject_name}</h2>\n'
        test_html += '<div class="pdf-header-info">\n'
        test_html += '  <div class="header-line">\n'
        test_html += '    <span class="header-label">Nome e Cognome:</span><span class="header-underline"></span>\n'
        test_html += '  </div>\n'
        test_html += '  <div class="header-line">\n'
        test_html += '    <span class="header-label">Data:</span><span class="header-underline date-line"></span>'
        test_html += '    <span class="header-label class-label">Classe:</span><span class="header-underline class-line"></span>\n'
        test_html += '  </div>\n'
        test_html += '</div>\n'

        q_counter = 1 # Contatore domande per test
        for question_data in single_test_data:
            # Pulisce il testo della domanda per HTML e rimuove \r
            q_text = question_data.get('question', 'DOMANDA MANCANTE').strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
            q_type = question_data.get('type', 'open_ended')
            nbsp = "&nbsp;" # Spazio non divisibile per separare numero e testo domanda

            test_html += f'<p class="question">{q_counter}.{nbsp}{q_text}</p>\n'

            if q_type == 'multiple_choice':
                answers = question_data.get('answers', []).copy()
                random.shuffle(answers) # Mischia le risposte
                if not answers:
                     test_html += '<p class="answer"><em>(Nessuna opzione di risposta fornita)</em></p>\n'
                else:
                    for answer in answers:
                        # Pulisce il testo della risposta
                        ans_text = str(answer).strip().replace('\r', '').replace('<', '&lt;').replace('>', '&gt;')
                        test_html += f'<p class="answer"><span class="checkbox">{checkbox_char}</span><span class="answer-text">{ans_text}</span></p>\n'
            # Per le domande aperte ('open_ended'), non aggiunge nulla dopo la domanda,
            # lasciando lo spazio naturale dato dai margini.

            q_counter += 1

        # Aggiunge un page break prima del prossimo test (tranne per il primo)
        page_break_class = " page-break" if index > 0 else ""
        html_parts.append(f'<div class="test-container{page_break_class}">\n{test_html}\n</div>')

    # Assembla l'HTML finale
    final_html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Verifiche Generate</title><style>{css_style}</style></head><body>{"".join(html_parts)}</body></html>'

    status_callback("info", "⚙️ Conversione HTML in PDF con WeasyPrint (potrebbe richiedere tempo)...")
    try:
        html_doc = HTML(string=final_html_content)
        pdf_bytes = html_doc.write_pdf()
        status_callback("info", "⚙️ Conversione PDF completata.")
        return pdf_bytes
    except FileNotFoundError as e:
        # Errore comune se mancano dipendenze C come Pango/Cairo/GTK+
        status_callback("error", f"ERRORE WeasyPrint: Dipendenze mancanti (GTK+/Pango/Cairo?). Dettagli: {e}")
        return None
    except Exception as e:
        # Cattura altri errori WeasyPrint
        status_callback("error", f"ERRORE durante la generazione PDF con WeasyPrint: {e}")
        return None
