# Resume Matcher & ATS Analyzer

This application analyzes your resume against a specific Job Description (JD) to identify missing skills and provide actionable recommendations to improve your ATS score.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env` file in this directory and add your OpenAI API Key:
    ```
    OPENAI_API_KEY=your_api_key_here
    ```
    Alternatively, you can enter the key directly in the application sidebar.

3.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```

## Usage

1.  Upload your Resume (PDF or DOCX).
2.  Paste the Job Description.
3.  Click "Analyze Resume".
4.  View the Match Score, Missing Skills, and download the report.
