# EvilProf 😈

[English Version](#english-version)

Generatore di Verifiche Casuali da Excel a PDF - Versione Streamlit

Questa app è hostata su [evilprof.streamlit.app](https://evilprof.streamlit.app/)

## Descrizione

**EvilProf** è un'applicazione web realizzata con Streamlit che permette di generare rapidamente file PDF contenenti verifiche personalizzate. L'applicazione legge le domande (a scelta multipla e/o aperte) da un file Excel strutturato in modo specifico e crea un numero definito di verifiche, ciascuna contenente un mix casuale di domande scelte dall'utente.

Funzionalità chiave è la possibilità di generare test adiacenti completamente diversi (con nessuna domanda in comune 😈).

## Caratteristiche Principali

* **Input da Excel:** Carica facilmente le tue domande da un file `.xlsx` o `.xls`.
* **Tipi di Domande:** Supporta sia domande a scelta multipla (con risposte casualizzate) sia domande a risposta aperta.
* **Personalizzazione:** Scegli il numero di verifiche da generare, il numero di domande per tipo (multiple/aperte) per ciascuna verifica e il nome della materia.
* **Randomizzazione Avanzata:** Le domande in ogni verifica sono selezionate casualmente dal pool disponibile nel file Excel. L'ordine delle risposte multiple è casuale.
* **Diversità Migliorata:** L'applicazione utilizza una tecnica di **Campionamento Casuale Ponderato Senza Reinserimento (WRSwOR)** basata su una variante dell'algoritmo A di Efraimidis e Spirakis (descritto in [questo paper](https://ethz.ch/content/dam/ethz/special-interest/baug/ivt/ivt-dam/vpl/reports/1101-1200/ab1141.pdf)) per selezionare le domande. Questo metodo:
    * **Garantisce** che le domande usate in una verifica non vengano ripetute nella verifica *immediatamente successiva*.
    * **Favorisce statisticamente** la selezione di domande che non vengono utilizzate da più tempo, promuovendo una maggiore rotazione e diversità tra le verifiche nel lungo periodo, senza richiedere un numero eccessivo di domande nel file di partenza.
* **Output PDF:** Genera un singolo file PDF pronto per la stampa, con ogni verifica che inizia su una nuova pagina e un'intestazione per nome, data e classe.

## Struttura del File Excel

Perché l'applicazione funzioni correttamente, il file Excel deve rispettare la seguente struttura **senza intestazioni di colonna**:

* **Colonna A:** Contiene il testo completo della domanda.
* **Colonne B, C, D, ...:** Contengono le diverse opzioni di risposta *solo* per le domande a scelta multipla. Devono esserci almeno due opzioni di risposta perché la domanda sia considerata a scelta multipla.
* **Domande Aperte:** Per una domanda aperta, lasciare semplicemente vuote le celle nelle colonne B, C, D, ...

*Esempio:*

![Esempio struttura file Excel](excel_example.jpg)

## Esecuzione Locale

Per eseguire EvilProf sul tuo computer:

1.  **Prerequisiti:**
    * Assicurati di avere **Python** installato (versione 3.7 o superiore).
    * Potrebbe essere necessario installare le dipendenze di sistema per `WeasyPrint` (come GTK+). Consulta la [documentazione di WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/install.html) per le istruzioni specifiche per il tuo sistema operativo (Linux, macOS, Windows).
2.  **Clona Repository:** Scarica o clona questo repository GitHub:
    ```bash
    git clone [https://github.com/subnetdusk/evilprof.git](https://github.com/subnetdusk/evilprof.git)
    cd evilprof
    ```
3.  **Installa Dipendenze Python:** Crea un ambiente virtuale (consigliato) e installa le librerie necessarie dal file `requirements.txt`:
    ```bash
    python -m venv venv
    # Attiva l'ambiente virtuale (esempi)
    # Windows: .\venv\Scripts\activate
    # Linux/macOS: source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  **Avvia Streamlit:** Esegui il comando:
    ```bash
    streamlit run evilprof.py
    ```
    (Sostituisci `evilprof.py` con il nome effettivo del file Python se diverso).
5.  **Apri nel Browser:** Streamlit dovrebbe aprire automaticamente l'applicazione nel tuo browser web predefinito (solitamente all'indirizzo `http://localhost:8501`).

---

<a name="english-version"></a>
## English Version
This app is hosted at [evilprof.streamlit.app](https://evilprof.streamlit.app/)

### Description

**EvilProf** is a web application built with Streamlit that allows you to quickly generate PDF files containing customized tests. The application reads questions (multiple-choice and/or open-ended) from a specifically structured Excel file and creates a defined number of tests, each containing a random mix of user-selected questions.

A key feature is the ability to generate completely different adjacent tests (with no questions in common 😈).

### Main Features

* **Input from Excel:** Easily upload your questions from an `.xlsx` or `.xls` file.
* **Question Types:** Supports both multiple-choice questions (with randomized answers) and open-ended questions.
* **Customization:** Choose the number of tests to generate, the number of questions per type (multiple/open) for each test, and the subject name.
* **Advanced Randomization:** Questions in each test are randomly selected from the pool available in the Excel file. The order of multiple-choice answers is also randomized.
* **Enhanced Diversity:** The application uses a **Weighted Random Sampling Without Replacement (WRSwOR)** technique based on a variant of Algorithm A by Efraimidis and Spirakis (described in [this paper](https://ethz.ch/content/dam/ethz/special-interest/baug/ivt/ivt-dam/vpl/reports/1101-1200/ab1141.pdf)) to select questions. This method:
    * **Guarantees** that questions used in one test are not repeated in the *immediately following* test.
    * **Statistically favors** the selection of questions that haven't been used for a longer time, promoting greater rotation and diversity among tests over the long run, without requiring an excessive number of questions in the source file.
* **PDF Output:** Generates a single PDF file ready for printing, with each test starting on a new page and a header for name, date, and class.

### Excel File Structure

For the application to work correctly, the Excel file must adhere to the following structure **without column headers**:

* **Column A:** Contains the full text of the question.
* **Columns B, C, D, ...:** Contain the different answer options *only* for multiple-choice questions. There must be at least two answer options for the question to be considered multiple-choice.
* **Open-Ended Questions:** For an open-ended question, simply leave the cells in columns B, C, D, ... blank.

*Example:*

![Example Excel file structure](excel_example.jpg)

### Local Execution

To run EvilProf on your computer:

1.  **Prerequisites:**
    * Ensure you have **Python** installed (version 3.7 or higher recommended).
    * You might need to install system dependencies for `WeasyPrint` (like GTK+). Consult the [WeasyPrint documentation](https://doc.courtbouillon.org/weasyprint/stable/install.html) for specific instructions for your operating system (Linux, macOS, Windows).
2.  **Clone Repository:** Download or clone this GitHub repository:
    ```bash
    git clone [https://github.com/subnetdusk/evilprof.git](https://github.com/subnetdusk/evilprof.git)
    cd evilprof
    ```
3.  **Install Python Dependencies:** Create a virtual environment (recommended) and install the necessary libraries from the `requirements.txt` file:
    ```bash
    python -m venv venv
    # Activate the virtual environment (examples)
    # Windows: .\venv\Scripts\activate
    # Linux/macOS: source venv/bin/activate
    pip install -r requirements.txt
    ```
4.  **Start Streamlit:** Run the command:
    ```bash
    streamlit run evilprof_eng.py
    ```
    (Replace `evilprof_eng.py` with the actual Python file name if different).
5.  **Open in Browser:** Streamlit should automatically open the application in your default web browser (usually at `http://localhost:8501`).
