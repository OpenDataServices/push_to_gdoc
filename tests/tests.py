import json

import matplotlib.pyplot as plt
import pandas
import pytest

from push_to_gdoc.google_api_services import get_api_services
from push_to_gdoc import update_google_doc


@pytest.fixture
def doc_service():
    return get_api_services()["docs"]


@pytest.fixture
def drive_service():
    return get_api_services()["drive"]


@pytest.fixture
def new_document_id(doc_service, drive_service):
    doc = doc_service.documents().create(body={"title": "test_title"}).execute()
    document_id = doc["documentId"]

    insert_marker = {"text": "{{marker}} {{marker}}", "location": {"index": 1}}

    doc_service.documents().batchUpdate(
        documentId=document_id, body={"requests": [{"insertText": insert_marker}]}
    ).execute()

    yield document_id
    drive_service.files().delete(fileId=document_id).execute()


def test_text(new_document_id, doc_service):

    unique_string = "a_very_unique_string"
    update_google_doc(new_document_id, {"marker": unique_string})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    assert document_dump.count(unique_string) == 2

    # update doc with new string
    new_unique_string = "a_new_very_unique_string"
    update_google_doc(new_document_id, {"marker": new_unique_string})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    assert document_dump.count(new_unique_string) == 2
    assert document_dump.count(unique_string) == 0


def test_link(new_document_id, doc_service):

    unique_link = {"url": "https://very_unique_link", "text": "a_very_unique_link_text"}

    update_google_doc(new_document_id, {"marker": unique_link})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    assert document_dump.count(unique_link["url"]) == 2
    assert document_dump.count(unique_link["text"]) == 2

    # update doc with new link
    new_unique_link = {
        "url": "https://new_very_unique_link",
        "text": "a_new_very_unique_link_text",
    }
    update_google_doc(new_document_id, {"marker": new_unique_link})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    assert document_dump.count(new_unique_link["url"]) == 2
    assert document_dump.count(new_unique_link["text"]) == 2

    assert document_dump.count(unique_link["url"]) == 0
    assert document_dump.count(unique_link["text"]) == 0


def test_matplotlib(new_document_id, doc_service):

    my_graph = plt.figure()
    x = [4, 2, 4, 4, 5, 6, 7, 8, 9]
    y1 = [1, 3, 5, 3, 1, 3, 5, 3, 1]
    y2 = [2, 4, 6, 4, 2, 4, 6, 4, 2]
    plt.plot(x, y1, label="line L")
    plt.plot(x, y2, label="line H")
    plt.plot()

    plt.xlabel("x axis")
    plt.ylabel("y axis")
    plt.title("2")
    plt.legend()

    update_google_doc(new_document_id, {"marker": my_graph})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    assert document_dump.count("inlineObjectElement") == 2


def test_table(new_document_id, doc_service):

    my_table = pandas.DataFrame.from_records(
        [
            {"column_1": "data_1", "column_2": "data_2"},
            {"column_1": "data_3", "column_2": "data_4"},
        ]
    )

    update_google_doc(new_document_id, {"marker": my_table})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    for i in range(1, 5):
        assert document_dump.count(f"data_{i}") == 2

    assert document_dump.count(f"column_1") == 2
    assert document_dump.count(f"column_2") == 2

    my_table = pandas.DataFrame.from_records(
        [
            {"column_new_1": "data_new_1", "column_new_2": "data_new_2"},
            {"column_new_1": "data_new_3", "column_new_2": "data_new_4"},
        ]
    )

    update_google_doc(new_document_id, {"marker": my_table})

    document = doc_service.documents().get(documentId=new_document_id).execute()
    document_dump = json.dumps(document)

    for i in range(1, 5):
        assert document_dump.count(f"data_{i}") == 0

    assert document_dump.count(f"column_1") == 0
    assert document_dump.count(f"column_2") == 0

    for i in range(1, 5):
        assert document_dump.count(f"data_new_{i}") == 2

    assert document_dump.count(f"column_new_1") == 2
    assert document_dump.count(f"column_new_2") == 2
