# Adobe India Hackathon: Connecting the Dots (Round 1A)

**Team Name:** Exemplary

**Participants:** Brijesh Patolia, Om Ramanuj, Krish Jain

---

## 1. Our Approach

Our solution is built around an intelligent, multi-stage pipeline designed to adapt to the diverse nature of PDF documents. We recognized that a one-size-fits-all approach would fail, as a visually-rich flyer requires a different analysis than a standard, text-heavy report.

Our methodology is as follows:

* **Rich Data Extraction (`PDFExtractor`)**: We start by using the `PyMuPDF` library to extract not just text, but a comprehensive set of metadata for every text span on a page. This includes font size, font name, color, and precise bounding box coordinates. A key feature is our custom logic to accurately determine the **background color** of text spans by sampling pixels, which is crucial for our visual analysis.

* **Baseline Style Analysis (`StyleAnalyzer`)**: Before we can find what's special (a heading), we must first understand what's normal. This component analyzes all text spans to determine the most common font size and style, establishing a "body text" profile. This baseline is the reference against which all potential headings are compared.

* **Intelligent Classifier Selection**: This is the core of our adaptive strategy. A dedicated function (`is_document_visually_driven`) analyzes the document's color palette.
    * If the document is primarily **monochrome**, it is passed to our `HeadingClassifier`.
    * If the document contains a significant amount of **color**, it is passed to our `VisualClassifier`.

* **Dual Classification Logic**:
    * **`HeadingClassifier`**: Optimized for traditional documents, this classifier identifies headings by looking for text that stands out stylistically from the body text baseline (e.g., larger font size, bold weight).
    * **`VisualClassifier`**: Designed for flyers, invitations, and other visually complex documents. This classifier gives more weight to visual cues like distinct text colors and background colors to identify headings, as font size alone is often not a reliable indicator in these layouts.

* **JSON Formatting (`JSONFormatter`)**: The final stage takes the classified outline and formats it into the precise JSON structure required by the hackathon, ensuring compliance with the submission standards.

---

## 2. Models and Libraries Used

### Libraries:

* **PyMuPDF (fitz)**: This is the sole external library used. It was chosen for its high performance and its powerful, low-level access to PDF content, which was essential for our detailed style and color analysis.

### Models:

No external or pre-trained models are used. Our solution's intelligence comes from a custom-built, lightweight system of heuristics and rule-based logic. This ensures the Docker image is small, fast, and fully compliant with the offline execution and size constraints for Round 1A.

---

## 3. How to Build and Run This Solution

This section provides the specific instructions for running the Round 1A solution. All commands should be executed relative to the `Round_1A` directory.

**Prerequisites:**
* Docker must be installed and running.

**Step 1: Navigate to the Round 1A Directory**

After cloning the repository, first navigate into the `Round_1A` folder.

```bash
cd path/to/repository/Round_1A
```

**Step 2: Prepare Input and Output Directories**

This folder should already contain an `input/` directory with the sample PDFs. If not, create `input/` and `output/` folders here.

**Step 3: Build the Docker Image**

From within the `Round_1A` directory, run the following command to build the Docker image for this specific task.

```bash
docker build -t adobe-hackathon-1a .
```

**Step 4: Run the Solution**

Finally, run the container using the command below. This command mounts the input and output folders from the current (`Round_1A`) directory and runs the container in an isolated environment.

```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none adobe-hackathon-1a
```
*(Note: The command above works directly on **Linux**, **macOS**, and **Windows PowerShell**. For the legacy **Windows Command Prompt (CMD)**, you must replace `${PWD}` with `%cd%`.)*

After the command finishes, the `output` folder inside `Round_1A` will contain the generated `.json` files.
