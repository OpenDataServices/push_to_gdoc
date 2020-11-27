import os
import re
import json
from operator import attrgetter
import secrets

from googleapiclient.http import MediaFileUpload

try:
    from matplotlib.figure import Figure as MatplotlibFigure
except ImportError:
    MatplotlibFigure = None

from pandas import DataFrame


class NamedRange:
    def __init__(self, document, name, doc_name, start, end, new_value):
        self.document = document
        self.name = name
        self.doc_name = doc_name
        self.start = start
        self.end = end
        self.new_value = new_value
        self.new = not bool(doc_name)
        self.old_value = None
        self.old_element = None

        self.id_ = None

        if not self.new:
            _, self.id_ = json.loads(doc_name)

    def get_doc_name(self):
        if not self.doc_name:
            self.doc_name = f"{json.dumps([self.name, secrets.token_urlsafe(5)])}"
        return self.doc_name

    def get_old_value_from_paragraph(self, element):
        text_content = element.get("textRun", {}).get("content", "")
        inline_object_id = element.get("inlineObjectElement", {}).get(
            "inlineObjectId", ""
        )

        if element["startIndex"] <= self.start < element["endIndex"]:
            if text_content:
                start_in_content = self.start - element["startIndex"]
                end_in_content = start_in_content + (self.end - self.start)
                old_value = text_content.encode("utf-16-le")[
                    start_in_content * 2 : end_in_content * 2
                ].decode("utf-16-le")
                # take first value found
                if not self.old_value:
                    self.old_value = old_value
                    self.old_element = element
            if inline_object_id:
                if not self.old_value:
                    self.old_value = inline_object_id
                    self.old_element = element

    def cleanup(self):
        pass

    def new_named_range_request(self):
        return {
            "createNamedRange": {
                "name": self.get_doc_name(),
                "range": {"startIndex": self.start, "endIndex": self.end},
            }
        }


class TextRange(NamedRange):
    def create_requests(self):
        requests = []

        if self.new:
            requests.append(self.new_named_range_request())

        requests.append(
            {
                "replaceNamedRangeContent": {
                    "namedRangeName": self.doc_name,
                    "text": self.new_value,
                }
            }
        )

        return requests


class LinkRange(NamedRange):
    def create_requests(self):
        requests = []

        if self.new:
            requests.append(self.new_named_range_request())

        requests.append(
            {
                "replaceNamedRangeContent": {
                    "namedRangeName": self.doc_name,
                    "text": self.new_value["text"],
                }
            }
        )

        requests.append(
            {
                "updateTextStyle": {
                    "textStyle": {"link": {"url": self.new_value["url"]}},
                    "fields": "link",
                    "range": {
                        "startIndex": self.start,
                        "endIndex": self.start
                        + len(self.new_value["text"].encode("utf-16-le")) / 2,
                    },
                }
            }
        )

        return requests


class MatplotLibRange(NamedRange):
    def create_requests(self):
        random_filename = secrets.token_urlsafe()

        self.new_value.savefig(f"/tmp/{random_filename}.png", dpi=150)

        file_metadata = {"name": f"{random_filename}.png"}
        media = MediaFileUpload(f"/tmp/{random_filename}.png", mimetype="image/png")
        drive_service = self.document.drive_service

        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        os.remove(f"/tmp/{random_filename}.png")

        self.drive_file_id = file.get("id")

        drive_service.permissions().create(
            fileId=file.get("id"), body={"role": "reader", "type": "anyone"}
        ).execute()

        download_link = (
            f"https://drive.google.com/uc?export=download&id={self.drive_file_id}"
        )

        requests = []

        if not self.new and self.old_value:
            requests.append(
                {
                    "replaceImage": {
                        "uri": download_link,
                        "imageObjectId": self.old_value,
                        "imageReplaceMethod": "CENTER_CROP",
                    }
                }
            )

        else:
            requests.append(
                {
                    "deleteContentRange": {
                        "range": {"startIndex": self.start, "endIndex": self.end}
                    }
                }
            )

            requests.append(
                {
                    "insertInlineImage": {
                        "uri": download_link,
                        "location": {"index": self.start},
                    },
                }
            )

            self.end = self.start + 1

            requests.append(self.new_named_range_request())

        return requests

    def cleanup(self):

        drive_service = self.document.drive_service
        file = drive_service.files().delete(fileId=self.drive_file_id).execute()


class DataFrameRange(NamedRange):
    def create_requests(self):
        table = []
        headers = tuple(self.new_value.columns.to_list())
        table.append(headers)
        for row in self.new_value.to_records():
            table.append(row.tolist()[1:])

        requests = []

        rows = len(table)
        columns = len(headers)

        if self.new:
            requests.append(
                {
                    "deleteContentRange": {
                        "range": {"startIndex": self.start, "endIndex": self.end}
                    }
                }
            )
            requests.append(
                {
                    "insertTable": {
                        "rows": rows,
                        "columns": columns,
                        "location": {"index": self.start},
                    },
                }
            )

        # +3 to accunt for new line and table and end table
        self.end = self.start + 3 + rows + (2 * rows * columns)

        if self.new:
            requests.append(self.new_named_range_request())

        ## adding 1 is an anomoly as the last row does not contain new row
        position = self.end + 1

        for row_num, row in enumerate(reversed(table)):
            ## each row takes up a position
            position -= 1
            for col_num, rowcell in enumerate(reversed(row)):
                position -= 2
                cell_named_range = (
                    f'#{json.dumps(["table", self.name, row_num, col_num])}'
                )
                new_end_index = position + len(str(rowcell).encode("utf-16-le")) / 2
                if self.new:
                    requests.append(
                        {
                            "insertText": {
                                "text": str(rowcell),
                                "location": {"index": position},
                            },
                        }
                    )
                    if row_num == rows - 1:
                        requests.append(
                            {
                                "updateTextStyle": {
                                    "textStyle": {"bold": True},
                                    "fields": "bold",
                                    "range": {
                                        "startIndex": position,
                                        "endIndex": new_end_index,
                                    },
                                }
                            }
                        )

                    requests.append(
                        {
                            "createNamedRange": {
                                "name": cell_named_range,
                                "range": {
                                    "startIndex": position,
                                    "endIndex": new_end_index,
                                },
                            },
                        }
                    )
                else:
                    requests.append(
                        {
                            "replaceNamedRangeContent": {
                                "namedRangeName": cell_named_range,
                                "text": str(rowcell),
                            },
                        }
                    )

        return requests


class Document:
    def __init__(self, services, document_id, context):
        self.requests = []
        self.named_ranges = []
        self.context = context
        self.docs_service = services["docs"]
        self.drive_service = services["drive"]
        self.document_id = document_id

    def update(self):
        document = (
            self.docs_service.documents().get(documentId=self.document_id).execute()
        )

        for namedRanges in document.get("namedRanges", {}).values():
            for namedRange in namedRanges["namedRanges"]:
                try:
                    name, _ = json.loads(namedRange["name"])
                except ValueError:
                    continue

                self.add_named_range(
                    name,
                    namedRange["ranges"][0]["startIndex"],
                    namedRange["ranges"][0]["endIndex"],
                    namedRange["name"],
                )

        self.read_strucutural_elements(document.get("body").get("content"))

        self.named_ranges.sort(key=attrgetter("start"), reverse=True)

        for named_range in self.named_ranges:
            self.requests.extend(named_range.create_requests())

        if self.requests:
            try:
                self.docs_service.documents().batchUpdate(
                    documentId=self.document_id, body={"requests": self.requests}
                ).execute()
            finally:
                for named_range in self.named_ranges:
                    named_range.cleanup()

    def add_named_range(self, name, start, end, doc_name=None):

        if name not in self.context:
            return
        value = self.context[name]

        # string values just replace text and keep formating.
        if isinstance(value, str):
            self.named_ranges.append(TextRange(self, name, doc_name, start, end, value))
        if MatplotlibFigure and isinstance(value, MatplotlibFigure):
            self.named_ranges.append(
                MatplotLibRange(self, name, doc_name, start, end, value)
            )
        if isinstance(value, dict) and set(value.keys()) == {"text", "url"}:
            self.named_ranges.append(LinkRange(self, name, doc_name, start, end, value))
        if isinstance(value, DataFrame):
            self.named_ranges.append(
                DataFrameRange(self, name, doc_name, start, end, value)
            )

    def read_paragraph_element(self, element):
        """Returns the text in the given ParagrapprinthElement.

        Args:
            element: a ParagraphElement from a Google Doc.
        """
        text_content = element.get("textRun", {}).get("content", "")
        for named_range in self.named_ranges:
            named_range.get_old_value_from_paragraph(element)

        if text_content:
            for match in re.finditer(
                "{{".encode("utf-16-le") + b"(.*?)" + "}}".encode("utf-16-le"),
                text_content.encode("utf-16-le"),
            ):
                name = match.group().decode("utf-16-le")[2:-2].strip()
                start_pos = int(element["startIndex"] + match.span()[0] / 2)
                end_pos = start_pos + int(len(match.group()) / 2)
                self.add_named_range(name, start_pos, end_pos)

    def read_strucutural_elements(self, elements):
        """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
        """

        for value in elements:
            if "paragraph" in value:
                elements = value.get("paragraph").get("elements")
                for elem in elements:
                    self.read_paragraph_element(elem)
            elif "table" in value:
                # The text in table cells are in nested Structural Elements and tables may be
                # nested.
                table = value.get("table")
                for row in table.get("tableRows"):
                    cells = row.get("tableCells")
                    for cell in cells:
                        self.read_strucutural_elements(cell.get("content"))
            elif "tableOfContents" in value:
                # The text in the TOC is also in a Structural Element.
                toc = value.get("tableOfContents")
                self.read_strucutural_elements(toc.get("content"))
