import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import tempfile
import time
import multiprocessing as mp
import cv2

filename = "Resources/textbook.pdf"

def get_text(page, page_number):
    print('Extracting text from page: ' + str(page_number))
    text = str(pytesseract.image_to_string(page))

    # In many PDFs, at line ending, if a word can't
    # be written fully, a 'hyphen' is added.
    # The rest of the word is written in the next line
    # Eg: This is a sample text this word here GeeksF-
    # orGeeks is half on first line, remaining on next.
    # To remove this, we replace every '-\n' to ''.
    text = text.replace('-\n', '')
    return text


# First, convert PDF to images.
with tempfile.TemporaryDirectory() as path:
    page_count = pdfinfo_from_path(filename)["Pages"]
    print(page_count)
    print('Ingesting ' + filename)
    start = time.time()
    pages = []
    page = 1
    all_texts = []
    # Convert the pdf in batches of 10 pages to avoid large memory usage.
    for page_num in range(1, page_count, 10):
        # Convert the pdf pages to jpeg images.
        block = convert_from_path(filename, dpi=200, first_page=page_num, last_page=min(page_num + 10 - 1, page_count),
                                  output_folder=path, thread_count=4, fmt='jpeg')
        print('Converting Pages ' + str(page_num) + "-" + str(page_num + 9))
        batch_page_numbers = []
        batch_pages = []
        for file in block:
            print('Ingesting page ' + str(page) + ' of ' + str(page_count))
            batch_pages.append(file)
            batch_page_numbers.append(page)
            page += 1
        # Extract the text from the jpeg images.
        with mp.Pool(mp.cpu_count()) as pool:
            texts = pool.starmap(get_text, zip(batch_pages, batch_page_numbers))
            all_texts.extend(texts)

    end = time.time()
    print('Finished ingesting pdf in ' + str(end - start) + ' seconds.')

    # Open the file in append mode so that
    # All contents of all images are added to the same file
    # Creating a text file to write the output
    outfile = "out_text2.txt"
    f = open(outfile, "a")
    for text in all_texts:
        f.write(text)
    # Close the file after writing all the text.
    f.close()
