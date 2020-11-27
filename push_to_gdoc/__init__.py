import push_to_gdoc.document as document
from push_to_gdoc.google_api_services import get_api_services


def update_google_doc(document_id, context):
    doc = document.Document(get_api_services(), document_id, context)
    doc.update()
