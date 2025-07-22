# Adobe India Hackathon: Connecting the Dots (Round 1A)

**Team Name:** Exemplary

**Participant:** Brijesh Patolia , Om ramanuj , Krish Jain

---

### 1. Our Approach

Our solution is built around an intelligent, multi-stage pipeline designed to adapt to the diverse nature of PDF documents. We recognized that a one-size-fits-all approach would fail, as a visually-rich flyer requires a different analysis than a standard, text-heavy report.

Our methodology is as follows:

1.  **Rich Data Extraction (`PDFExtractor`)**: We start by using the `PyMuPDF` library to extract not just text, but a comprehensive set of metadata for every text span on a page. This includes font size, font name, color, and precise bounding box coordinates. A key feature is our custom logic to accurately determine the **background color** of text spans by sampling pixels, which is crucial for our visual analysis.

2.  **Baseline Style Analysis (`StyleAnalyzer`)**: Before we can find what's special (a heading), we must first understand what's normal. This component analyzes all text spans to determine the most common font size and style, establishing a "body text" profile. This baseline is the reference against which all potential headings are compared.

3.  **Intelligent Classifier Selection**: This is the core of our adaptive strategy. A dedicated function (`is_document_visually_driven`) analyzes the document's color palette.
    * If the document is primarily **monochrome**, it is passed to our `HeadingClassifier`.
    * If the document contains a significant amount of **color**, it is passed to our `VisualClassifier`.

4.  **Dual Classification Logic**:
    * **`HeadingClassifier`**: Optimized for traditional documents, this classifier identifies headings by looking for text that stands out stylistically from the body text baseline (e.g., larger font size, bold weight).
    * **`VisualClassifier`**: Designed for flyers, invitations, and other visually complex documents. This classifier gives more weight to visual cues like distinct text colors and background colors to identify headings, as font size alone is often not a reliable indicator in these layouts.

5.  **JSON Formatting (`JSONFormatter`)**: The final stage takes the classified outline and formats it into the precise JSON structure required by the hackathon, ensuring compliance with the submission standards.

### 2. Models and Libraries Used

* **Libraries**:
    * **`PyMuPDF` (fitz)**: This is the sole external library used. It was chosen for its high performance and its powerful, low-level access to PDF content, which was essential for our detailed style and color analysis.

* **Models**:
    * **No external or pre-trained models are used.** Our solution's intelligence comes from a custom-built, lightweight system of heuristics and rule-based logic. This ensures the Docker image is small, fast, and fully compliant with the offline execution and size constraints.

### 3. How to Build and Run the Solution

This section provides a complete step-by-step guide for cloning the repository and running the solution in its intended Docker environment.

**Prerequisites:**
* [Git](https://git-scm.com/downloads) must be installed.
* [Docker](https://www.docker.com/get-started) must be installed and running.

**Step 1: Clone the Repository**

First, clone the project repository to your local machine using the following command:

```bash
git clone <your-repository-url>
```
*(Note: Replace `<your-repository-url>` with the actual URL of the Git repository.)*

**Step 2: Navigate to the Project Directory**

Change your current directory to the newly cloned project folder:

```bash
cd <repository-folder-name>
```

**Step 3: Prepare Input and Output Directories**

The container requires an `input` folder containing the PDFs to be processed and an `output` folder where the JSON results will be saved.

Create these two folders in the project's root directory:
```bash
mkdir input
mkdir output
```
Now, place all the PDF files you want to process inside the newly created `input` folder.

**Step 4: Build the Docker Image**

From the root directory of the project, run the following command to build the Docker image. This command reads the `Dockerfile` and packages the application and its dependencies into a self-contained image.

```bash
docker build -t adobe-hackathon-solution .
```

**Step 5: Run the Solution**

Finally, run the container using the exact command specified for the hackathon evaluation. This command mounts your local `input` and `output` folders and runs the container in an isolated environment with no network access.

```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none adobe-hackathon-solution
```
*(Note: The command above works directly on **Linux**, **macOS**, and **Windows PowerShell**. For the legacy **Windows Command Prompt (CMD)**, you must replace `${PWD}` with `%cd%`.)*

After the command finishes, the `output` folder on your local machine will contain the generated `.json` files, one for each PDF that was in the `input` folder.
