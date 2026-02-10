#!/usr/bin/env -S custom_python_launcher science

###########################################################################################
# Custom Python script to convert a .bib (BibTex) file to a nice HTML list.
# For each BibTex entry, the output list item is formatted in two rows:
#
#   Author_1, Author_2 & Author_3 (Year).
#   Title with link to the paper [link_2] [link 3] *(Custom note)*. Journal, vol., etc...
#
# How it works:
#   -   If you want to display your own note after the title, you must write it in the
#       "note" field enclosed by parentheses ( e.g., note = {(Short note)} )
#   -   Url to the paper must be saved in the field "url", clearly
#   -   If you want to display additional links right after the title, you can add fields
#       named "url_2", "url_3", ... containing the urls, up to a total of 30. You can set
#       the link text by using the optional fields "url_note_2", "url_note_3", ...,
#       otherwise the links are displayed with a default text.
#       Note: these additional fields are not BibTex fields, but you can add them to
#       the entries normally. They don't affect how the .bib file is processed by Latex.
#
# Please set the variables SCRIPT_DIR, INPUT_BIB, and OUTPUT_HTML below.
###########################################################################################

import bibtexparser
from bibtexparser.customization import convert_to_unicode
from bibtexparser.bparser import BibTexParser

def get_author_string(entry):
    """
    Extracts and formats authors string.
    Outputs an empty string if there are no authors.
    """
    if 'author' in entry:
        # The library bibtexparser separa gli autori con 'and'
        authors = entry['author'].split(' and ')
        
        # Formats autors (we use last name only)
        formatted_authors = []
        for author in authors:
            author = author.strip()
            if "," in author:
                # Case: "Surname, Name Name2"
                parts = [p.strip() for p in author.split(",")]
                last = parts[0]
                # first = parts[1]
            else:
                # Case: "Name Name2 Surname"
                parts = author.split()
                last = parts[-1]
                # first = " ".join(parts[:-1])
            formatted_authors.append(f"{last}")

        # Merge authors with commas, and ' & ' for the last author
        if len(formatted_authors) > 1:
            return ", ".join(formatted_authors[:-1]) + f" & {formatted_authors[-1]}"
        elif formatted_authors:
            return formatted_authors[0]
    return ""

def format_bibtex_entry(entry):
    """
    Formats a single BibTeX entry into the desired HTML format.
    """
    # Extract key fields (we use .get to avoid errors in case a field is missing)
    title = entry.get('title', 'Unknown title')
    author_str = get_author_string(entry)
    year = entry.get('year', 'n.d.') # n.d. = not dated
    
    # Try to extract a URL/Link
    link = entry.get('url', entry.get('doi', '#')) # Prefers 'url', else 'doi', else a placeholder
    if link != '#' and not (link.startswith('http') or link.startswith('ftp')):
         # If we only have a DOI, we construct the standard url with that
         if 'doi' in entry:
            link = f"https://doi.org/{entry['doi']}"
         else:
            link = '#' # If we don't have a url, we place this placeholder
    
    # Field for the custom note
    # We only display the note if it's enclosed by parentheses in the 'note' field
    custom_note = ""
    if entry.get('note', '').startswith('(') and entry.get('note', '').endswith(')'):
        # We extract the note without parentheses (I will put them back later cause I like them, but this will allow easier script customization)
        custom_note = entry['note'].strip()
    
    # Journal/Booktitle/Proceedings
    container = ""
    volume = ""
    pages = ""
    
    if 'journal' in entry:
        container = f"<em>{entry['journal']}</em>"
    elif 'booktitle' in entry:
        container = f"<em>In {entry['booktitle']}</em>"
    elif 'publisher' in entry:
        container = f"<em>{entry['publisher']}</em>"
        
    if 'volume' in entry:
        volume = f", Vol. {entry['volume']}"
        
    if 'pages' in entry:
        pages_val = entry['pages'].replace('--', '–') # Replaces -- with en-dash
        pages = f", pp. {pages_val}"
        
    # Building the HTML string
    html = f"""
<li>
<p>{author_str} ({year}).
<br>
<a href="{link}" class="external">{title}</a>"""
    # Now we add all the other links, with their names
    for a in range(2,31):
        if 'url_'+str(a) not in entry:
            break
        if 'url_note_'+str(a) not in entry:
            url_note = 'link '+str(a) # Default link text
        else:
            url_note = entry['url_note_'+str(a)]
        html += f" <a href=\"{entry['url_'+str(a)]}\" class=\"external\">[{url_note}]</a>"

    # We add the custom note if present
    if custom_note:
        html += f" <strong>{custom_note}</strong>."
    else:
        html += "."
    if container or volume or pages:
    # Add container, volume and pages
        html += f" {container}{volume}{pages}."
    html += "</p>\n</li>"
    return html

def convert_bib_to_html(input_file, output_file):
    """
    Main conversion function from .bib to .html.
    """
    print(f"Reading the BibTeX file: {input_file}")
    
    try:
        # Configure the parser for better character management
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        
        with open(input_file, 'r', encoding='utf-8') as bibfile:
            bib_database = bibtexparser.load(bibfile, parser=parser)
            
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_file}")
        return
    except Exception as e:
        print(f"ERROR while trying to read the BibTeX file: {e}")
        return

    # 1. Sort entries by year and by first author's last name
    print("Sorting entries by year...")
    sorted_entries_1 = sorted(
        bib_database.entries, 
        key=lambda entry: entry.get('author', '').split(' and ')[0].split(',')[0].split()[-1].lower() # Sort by first author's last name
    )
    sorted_entries = sorted(
        sorted_entries_1, 
        key=lambda entry: entry.get('year', '') # Sort by year
    )

    # 2. Generate HTML content
    html_content = ""
    for entry in sorted_entries:
        html_content += format_bibtex_entry(entry)

    # 3. Writes the output in the HTML file
    full_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Converted bibliography</title>
    <style>
        /* Minimal styles */
        li {{
            margin-bottom: 1em;
        }}
        .external {{
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <h1>References</h1>
    <ul>
{html_content}
    </ul>
</body>
</html>"""

    try:
        with open(output_file, 'w', encoding='utf-8') as html_file:
            html_file.write(full_html)
        print(f"\n✅ Conversion complete! HTML file saved as: {output_file}")
    except Exception as e:
        print(f"ERROR in writing the HTML file: {e}")

# --- Execution ---
if __name__ == "__main__":
    # File names
    SCRIPT_DIR = ""
    INPUT_BIB = SCRIPT_DIR +'bibliography.bib'
    OUTPUT_HTML = SCRIPT_DIR + 'references.html'
    
    # Example of BibTex file
    example_bib_content = """
@inproceedings{krizhevsky2012imagenet,
  title={{ImageNet Classification with Deep Convolutional Neural Networks}},
  author={Krizhevsky, Alex and Sutskever, Ilya and Hinton, Geoffrey E.},
  booktitle={Proceedings of the 25th International Conference on Neural Information Processing Systems (NIPS)},
  volume={1},
  pages={1097--1105},
  year={2012},
  note={(AlexNet)},
  url={https://proceedings.neurips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf}
}

@article{lecun1998gradient,
  title={Gradient-based learning applied to document recognition},
  author={LeCun, Yann and Bottou, L{\'e}on and Bengio, Yoshua and Haffner, Patrick},
  journal={Proceedings of the IEEE},
  volume={86},
  number={11},
  pages={2278--2324},
  year={1998},
  doi={10.1109/5.726791}
}
"""
    # Creating example file if input does not exist
    import os
    if not os.path.exists(INPUT_BIB):
        with open(INPUT_BIB, 'w', encoding='utf-8') as f:
            f.write(example_bib_content.strip())
        print(f"Creato un file di esempio '{INPUT_BIB}' per il test.")

    convert_bib_to_html(INPUT_BIB, OUTPUT_HTML)
