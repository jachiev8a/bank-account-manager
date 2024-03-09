import glob
import os

def get_pdf_files(directory):
    # Expand the tilde in the directory path
    expanded_path = os.path.expanduser(directory)

    # Use glob to get all PDF files in the specified directory
    pdf_files = glob.glob(os.path.join(expanded_path, '*.pdf'))

    # Store absolute paths in a list
    absolute_paths = [os.path.abspath(file) for file in pdf_files]

    return absolute_paths
