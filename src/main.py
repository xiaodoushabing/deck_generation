#%%
import os
import subprocess
import httpx
from openai import OpenAI
from utilities import FileIO

# %% Get user input
markdown_path = "./test_files/sample_reference_02.md"
user_prompt = "Create a presentation to summarize the key utilities described."
num_slides = 20
mermaid = True

slide_content_filename = "./test_files/slide_content_response_02.md"
final_content_filename = "./test_files/final_content_response_02.md"
output_pptx="./test_files/output_02.pptx"
final_output_pptx = "./test_files/final_output_02.pptx"

# %% 
# define helper functions
def get_response(system_prompt, user_prompt, max_tokens=10000, model="gpt-oss-120b"):
    """Get LLM response

    Args:
        system_prompt (str): system prompt
        user_prompt (str): user prompt
        max_tokens (int, optional): maximum number of tokens. Defaults to 10000.
        model (str, optional): model to use. Defaults to "gpt-oss-120b".
    """
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, stream=False)

    # get slide content response
    # extract message object
    message = response.choices[0].message

    # Get the content string (LLM's reply)
    llm_response = message.content
    print(f"Slide content response:\n{llm_response}")

    # get information about LLM usage
    llm_usage = response.usage
    print(f"Prompt tokens used: {llm_usage.prompt_tokens}")
    print(f"Completion tokens used: {llm_usage.completion_tokens}")
    print(f"Total tokens used: {llm_usage.total_tokens}")
    return llm_response, llm_usage

def convert_to_ppt(input_filename, output_filename):
    """Convert markdown to ppt using pandoc"""
    try:
        subprocess.run(["pandoc", "-o", output_filename, input_filename], check=True)
        print(f"Successfully converted '{input_filename}' to '{output_filename}'.")
    except FileNotFoundError:
        print("Error: Pandoc is not installed or not found in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Pandoc failed with error: {e}")

# %%
# define client
httpx_client = httpx.Client(verify=False)
openai_api_key = os.getenv("API_KEY")
open_api_url = "https://api.openai.com/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=open_api_url,
    http_client=httpx_client
)

# %%
# 1. Slide structure generation
# define required output format
structure_output_format = (
    'Return only the JSON object with the following sample structure:\n'
    '{\n'
    '  "title": "Title of the presentation",\n'
    '  "slides": [\n'
    '    {\n'
    '      "heading": "Slide title",\n'
    '      "key_message": "Key message of the slide"\n'
    '    },\n'
    '    ...\n'
    '  ]\n'
    '}\n'
)

# define system prompt
slide_structure_system_prompt = f"""
You are an expert presentation designer.
Your task is to create a logical slide outline (structure) for a presentation.
You will be given a user prompt describing the presentation topic and possibly a reference document in markdown format.
Analyze the markdown content to identify key sections and ideas relevant to the topic.
Generate a numbered list of slide titles that form a coherent flow for the presentation.
Do NOT generate detailed slide content yet, only the slide structure (titles and order).
Always include Introduction and Summary (or Key takeaway) slides.
Ensure the outline covers the main points from the markdown and aligns with the user prompt.
Validate your output to ensure you gave a coherent slide outline.
Output the final content strictly following this format:
{structure_output_format}
"""

if markdown_path:
    markdown_content = FileIO.fread(markdown_path)
else:
    markdown_content = ""

slide_structure_user_prompt = f"""
{user_prompt}.

Reference markdown content:
```markdown
{markdown_content}
```

Only generate {num_slides} slides.
Please generate the slide outline in the JSON format described above.
"""

# get slide structure response
slide_structure_response, slide_structure_usage = get_response(
    slide_structure_system_prompt,
    slide_structure_user_prompt,
)

# %%
# 2. Slide content generation
# define output format
expected_output_format = """
The output must be a markdown document structured for Pandoc conversion to PowerPoint.
Follow these formatting rules:

- Use the guidelines from Pandoc's manual: https://pandoc.org/MANUAL.html
- Use `#` for the Presentation Title (this maps to the **Title Slide** layout).
- Use `##` for each new slide title (this maps to the **Title and Content** layout unless otherwise specified).
- Use `---` to separate slides. Ensure newline above and below this.
Include speaker notes using the following syntax:
::: notes
This is my note.
- It can contain Markdown
- like this list
:::

- To add tables, use standard markdown syntax for tables. Example:
| Header 1 | Header 2 | Header 3 ...|
| --- | --- | --- |
| Content 1 | Content 2 | Content 3 |
| ... | ... | ... |

- Use fenced code blocks. These begin with a row of three or more backticks (`) and end with a row of backticks that must be at least as long as the starting row. Everything between these lines is treated as code. No indentation is necessary:

``````{#mycode .haskell .numberLines startFrom="100"}
if (a > 3) {
    moveShip(5 * gravity, DOWN);
}
``````

Like regular code blocks, fenced code blocks must be separated from surrounding text by blank lines.
If the code itself contains a row of tildes or backticks, just use a longer row of tildes or backticks at the start and end:

`````````````````
``````
code including tildes
``````
`````````````````

In the above code block example, mycode is an identifier, haskell and numberLines are classes, and startFrom is an attribute with value 100.
Powerpoint can use this information to do syntax highlighting.

- For slides with text followed by images or tables, Pandoc will use the **Content with Caption** layout.
- For slides with only speaker notes or blank content, Pandoc will use the **Blank** layout.
- Footnotes are supported:
    Regular: Here is a footnote reference,
    Inline: Inline note.^[This is an inline footnote.]
"""

# Define system prompt
slide_content_system_prompt = f"""
You are an expert assistant specialized in generating detailed yet concise slide content for presentations.
You will use the provided slide structure and the reference markdown content to generate slide content.
For each slide title in the structure, extract relevant sections from the markdown content.
Generate bullet points suitable for each slide, making sure to include key information or messages.
Do not have more than 5 bullet points in a slide.
If comparison is needed, use multiple columns to describe the point. These tables of columns should be concise and self-explanatory.
Keep it concise. Slides should be visual summaries, not dense text blocks.
Output the final content strictly following this format:
{expected_output_format}
"""

# Define user prompt for slide content generation
slide_content_user_prompt = f"""
Slide structure:
{slide_structure_response}.

Reference markdown content:
```markdown
{markdown_content}
```
Please generate a presentation in markdown format described above.
The markdown should be clean and ready for conversion into a PowerPoint presentation using Pandoc.
"""

# get slide content response
slide_content_response, slide_content_usage = get_response(slide_content_system_prompt, slide_content_user_prompt)

# %%
# save output into markdown
FileIO.fwrite(slide_content_filename, slide_content_response)
# convert md to ppt
convert_to_ppt(slide_content_filename, output_pptx)

# %%
# 3. OPTIONAL - Add mermaid diagrams
if mermaid:
    few_shot_examples = """
- Sequence diagram:

```mermaid
sequenceDiagram
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
    Alice-)John: See you later!
```

- Flow chart:

```mermaid
flowchart LR
    markdown["`This ** is ** _Markdown_`"]
    newLines["`Line1
    Line 2
    Line 3`"]
    markdown -- > newLines
```

or
```mermaid
flowchart LR
    markdown["`This **is** _Markdown_`"]
    newLines["`Line1
    Line 2
    Line 3`"]
    markdown -- > newLines
```

or

```mermaid
flowchart LR
    Logger["LogManager"] --> TaskA["logger.get_logger('data_preprocessing')"]
    Logger --> TaskB["logger.get_logger('model_training')"]
    TaskA -->|writes| FileA["preprocess.log"]
    TaskB -->|writes| FileB["training.log"]
```

Possible FlowChart orientations are:
TB: Top to bottom
TD: Top-down/ same as top to bottom
BT: Bottom to top
RL: Right to left
LR: Left to right

It is possible declare many links in the same line as per below:

```mermaid
flowchart LR
    A -- text -- > B -- text2 -- > C
```

It is also possible to declare multiple nodes links in the same line as per below:

```mermaid
flowchart LR
    a -- > b & c -- > d
```

You can then describe dependencies in a very expressive way. Like the one-liner below:

```mermaid
flowchart TB
    A & B -- > C & D
```

- Class diagram:

```mermaid
classDiagram
    note "From Duck till Zebra"
    Animal <|-- Duck
    note for Duck "can fly\ncan swim\ncan dive\ncan help in debugging"
    Animal <|-- Fish
    Animal <|-- Zebra
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Animal: +mate()
    class Duck{
        +String beakColor
        +swim()
        +quack()
    }
    class Fish{
        -int sizeInFeet
        -canEat()
    }

    class Zebra{
        +bool is_wild
        +run()
    }
```

- Pie chart:
Start with pie keyword to begin the diagram
showData to render the actual data values after the legend text. This is OPTIONAL.
Followed by title keyword and its value in string to give a title to the pie-chart. This is OPTIONAL
Followed by dataSet. Pie slices will be ordered clockwise in the same order as the labels.
label for a section in the pie diagram within " " quotes.
Followed by : colon as separator
Followed by positive numeric value (supported up to two decimal places)

```mermaid
pie showData
    title Key elements in Product X
    "Calcium" : 42.96
    "Potassium" : 50.05
    "Magnesium" : 10.01
    "Iron" : 5
```

- Quadrant chart:
Don't include parentheses or extra descriptions inside quadrant labels.
Always include a space after the comma in coordinate pairs, i.e., format them as [x, y], not [x,y].
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    Campaign A: [0.3, 0.6]
    Campaign B: [0.45, 0.23]
    Campaign C: [0.57, 0.69]
    Campaign D: [0.78, 0.34]
    Campaign E: [0.40, 0.34]
    Campaign F: [0.35, 0.78]
```

- Timeline:

```mermaid
timeline
    title History of Social Media Platform
    2002 : LinkedIn
    2004 : Facebook
        : Google
    2005 : YouTube
    2006 : Twitter
```

You can group time periods in sections/ages. This is done by adding a line with the keyword section followed by the section name.
All subsequent time periods will be placed in this section until a new section is defined.
If no section is defined, all time periods will be placed in the default section.

```mermaid
timeline
    title Timeline of Industrial Revolution
    section 17th-20th century
        Industry 1.0 : Machinery, Water power, Steam <br>power
        Industry 2.0 : Electricity, Internal combustion engine, Mass production
        Industry 3.0 : Electronics, Computers, Automation
    section 21st century
        Industry 4.0 : Internet, Robotics, Internet of Things
        Industry 5.0 : Artificial intelligence, Big data, 3D printing
```

- Radar chart:
```mermaid
radar-beta
    axis m["Math"], s["Science"], e["English"]
    axis h["History"], g["Geography"], a["Art"]
    curve a["Alice"]{85, 90, 80, 70, 75, 90}
    curve b["Bob"]{70, 75, 85, 80, 90, 85}


    max 100
    min 0
```
"""

# Define system prompt
mermaid_system_prompt = f"""
You are a specialized agent that enhances Markdown documents by inserting valid Mermaid diagrams.
Your responsibilities are:
- Do not modify any existing Markdown content.
- Only insert Mermaid diagrams in appropriate locations, such as after headers or bullet points where visual explanation is helpful.
- Always insert Mermaid diagrams **within** the 'notes' section. Rendering will be handled separately.
- If the Markdown already contains Mermaid diagrams, **do not duplicate or modify them**.
- If a section does not benefit from a diagram, **skip it**.
Insert diagrams **only where relevant** , and **do not exceed one diagram per slide** unless explicitly instructed.
Do not include any commentary, explanation, or formatting outside the Mermaid code block. The diagram should be self-explanatory as a visual aid to the
corresponding markdown content.

Mermaid Diagram Formatting Rules:

- All Mermaid diagrams **must** be enclosed in a properly formatted code block using triple backticks and the `mermaid` language tag.
- The opening line of the diagram must be exactly: ` ```mermaid ` (three backticks followed immediately by the word mermaid, no extra characters or spacing).
- The closing line must be exactly: ` ``` `(three backticks only).
- There must be a **newline before and after** the entire Mermaid code block.
- Do **not** nest or repeat triple backticks.
- Do **not** use any other language tag or omit the backticks.
- Do **not** concatenate the language tag with the diagram content (e.g., avoid ` ```mermaidgraph TD ...`).
- You **must** ensure that Mermaid syntax is correct and diagrams are renderable.
- Avoid using double quotes (") inside node labels, as this can cause parsing errors. Prefer single quotes (') or escape double quotes if absolutely necessary

Diagram Selection:
- If a diagram is useful for a particular slide, choose one of the following types:
Sequence diagram, Flow chart, Class diagram, Pie chart, Quadrant chart, Timeline, Radar chart.

Refer to the relevant diagram type using the few-shot examples below:
{few_shot_examples}
"""

# Define user prompt for slide content generation
mermaid_user_prompt = f"""
Please enhance the following Markdown document by **inserting** valid Mermaid diagrams where appropriate.
Do not modify any existing content.
Ensure all diagrams are syntactically correct and renderable.
Only insert diagrams where they add value, and limit to **one per slide** unless otherwise stated.

Reference markdown content:
{slide_content_response}

The resulting markdown should be clean and ready for conversion into a PowerPoint presentation using Pandoc.
Do not use multiple consecutive sets of triple backticks in your output.
"""
# get slide structure response
mermaid_content_response, mermaid_content_usage = get_response(mermaid_system_prompt, mermaid_user_prompt)
# %%
if not mermaid:
    # save final output into markdown
    FileIO.fwrite(final_content_filename, mermaid_content_response)
    # convert md to ppt
    convert_to_ppt(final_content_filename, final_output_pptx)
# %%
# 4. Check mermaid syntax
if mermaid:

    checker_system_prompt = """
    You are a specialized agent responsible for validating and correcting Mermaid diagrams embedded in Markdown documents.
    Your responsibilities are:

    1. **Scope of Modification**
    - Do **not** modify any non-Mermaid content in the Markdown.
    - Only process Mermaid code blocks that are malformed, incomplete, or contain syntax errors.
    - Do **not** insert new diagrams, only fix existing ones.

    2. **Code Block Structure**
    - Ensure each Mermaid diagram is enclosed in a properly formatted code block:
        - Starts with exactly: ```mermaid (three backticks followed immediately by the word 'mermaid', no extra characters or spacing).
        - Ends with exactly: ``` (three backticks only).
        - Has a newline before and after the block.
    - Do **not** concatenate the opening tag with diagram content (e.g., avoid mermaidgraph TD ... ).
    - Do **not** include multiple or nested sets of triple backticks inside the diagram.

    3. **Syntax Validation**
    - Ensure the diagram contains valid and renderable Mermaid syntax.
    - If a diagram is incomplete or contains unclosed backticks, fix the structure and ensure syntactic correctness.
    - Avoid using double quotes (") inside node labels. Prefer single quotes ( ') or escape double quotes if necessary to prevent parsing errors.
    - Do not use square brackets [] unnecessarily for labeling edges; use the correct Mermaid syntax with colon : for labels.
    4. **Correction Example 1**
    - Malformed:

    ```mermaid
    flowchart LR
        ...
    ```
    ```

    - Corrected:

    ```mermaid
    flowchart LR
        ...
    ```

    5. **Correction Example 2**
    - Malformed:
    ```mermaid
    classDiagram
        class CredentialConfig{
            +env
            +engine
        }
        CredentialConfig -- > Environment["PREPROD, UAT"]
        CredentialConfig -- > Engine["Hive, Trino, Impala, Spark, ... "]
    ```

    - corrected:
    mermaid
    classDiagram
        class CredentialConfig{
            +env
            +engine
        }
        CredentialConfig --> Environment: "PREPROD, UAT"
        CredentialConfig --> Engine: "Hive, Trino, ... "

    5. ** Strict Boundaries **
    - Do not interpret, rephrase, or alter any Markdown content outside the Mermaid blocks.
    """

    checker_user_prompt = f"""
    Please fix the Mermaid diagrams in the following Markdown document.
    Some diagrams may have:
    Unclosed or duplicated triple backticks
    Invalid Mermaid syntax
    Improper wrapping (e.g., missing ```mermaid at the beginning or ``` at the end)

    Your task is to:
    Correct the wrapping of each Mermaid diagram
    Ensure the syntax is valid and renderable
    Leave all other Markdown content untouched
    Check for unescaped quotes, unmatched brackets, or unsupported characters, and make corrections using valid Mermaid syntax.
    When rendering Mermaid diagrams, wrap node labels with double quotes only if the label itself does not contain quotes. Otherwise, use single quotes or escape
    characters appropriately.

    Markdown document to fix:
    {mermaid_content_response}
    """

    checker_content_response, checker_content_usage = get_response(checker_system_prompt, checker_user_prompt)
    # %%
    # save final output into markdown
    FileIO.fwrite(final_content_filename, checker_content_response)
    # convert md to ppt
    convert_to_ppt(final_content_filename, final_output_pptx)
# %%