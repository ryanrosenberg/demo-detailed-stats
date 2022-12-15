import docx
from simplify_docx import simplify

# read in a document 
my_doc = docx.Document("/path/to/my/favorite/file.docx")

# coerce to JSON using the standard options
my_doc_as_json = simplify(my_doc)

# or with non-standard options
my_doc_as_json = simplify(my_doc,{"remove-leading-white-space":False})