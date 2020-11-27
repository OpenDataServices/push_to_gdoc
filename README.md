# Push To Google Docs

Push data from python to Google Docs. Primarily to use within a notebook.

## Installation

Installation can be done through `pip`.

```
pip install push_to_gdoc
```


## Authentication with Google OAuth.

The library needs access Google Docs. This is done through OAuth authentication.

There are different steps needed for each installation type:

### Colab Notebook

This should happen automatically when used for the first time by following inline instructions.  In order to do the authentation before invoking the libarary run:

```
from google.colab import auth
auth.authenticate_user()
```

Other authentiaction, such as API access to google drive, is achieved by running the above.


### Local jupyter notebook or local python script

You will need a Google Cloud Platform project with the Google Drive and Google Docs APIs enabled.  Then you will need to download the credentials.json file to the following location.

```
~/.config/push_to_gdoc/credentials.json
```

The `push_to_doc` directory may need to be made.

When the code is first run a browser window will pop up where you are guided through the normal Google OAuth authentication process.


## Usage

In order to get data into a Google Doc you need the document ID of the doc you want to update.
The easiest way to get this is through the URL of the doc.

So if the URL is `https://docs.google.com/document/d/1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls/edit` then the document ID is `1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls`

Within the docs themselves you need to give markers that show where you want the content to go. These look like `{{my_marker}}`.  The markers can be named anything you like and each should have their own unique name (unless you want the same data to pushed to both markers).

The main function to call is:

```python
from push_to_gdoc import update_google_doc
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", {"my_marker": "text to put into docs"})
```

The first argument is the document ID above. The second argument is a dictionary, with the keys being the names of the markers and the values being the data that you want to replace that marker with.  So this command will replace all occurrences of `{{my_marker}}` in the doc with the text `text to put into docs`.

If you want to then update the doc you can do:

```python
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", {"my_marker": "NEW text to put into docs"})
```

This will update the range where the old text was into the new text. So it will effecively replace 'text to put into docs' into 'NEW text to put into docs'.

You can use python [`locals`](https://docs.python.org/3/library/functions.html#locals) function to make it more ergonomic to use within a notebook context. So for example you can do.

```python
my_marker = "text to put into docs"
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

[`locals`](https://docs.python.org/3/library/functions.html#locals) expresses all the defined local variables as a dictionary.

The library detects the type of the value and replaces it with the relevent element.

There a several supported types of values that you can use:

## string

As above because the variable `my_title` is a string then it will replace it with just text:

```python
my_title = "My Doc Title"
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

It will also keep the formatting of the marker so if there is `{{my_title}}` in the document formatted as a title then this will be replaced with the text `My Doc Title`.

## link

A link can be expressed as a dictionary with 2 keys `url` and `text`:

```python
my_link = {"url": "https://google.com", "text": "A search engine"}
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

## Pandas DataFrame

A table can be added by reference to a pandas DataFrame:

```python
my_table = pandas.DataFrame.from_records(
    [
        {"column_1": "data_1", "column_2": "data_2"},
        {"column_1": "data_3", "column_2": "data_4"},
    ]
)
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

This will create a table in google sheets.  To update the same table with new values run:

```python
my_table = pandas.DataFrame.from_records(
    [
        {"column_1": "new_data_1", "column_2": "new_data_2"},
        {"column_1": "new_data_3", "column_2": "new_data_4"},
    ]
)
update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

It will also keep any formatting changes of the table since the last update.

**Warning**: if the DataFrame dimensions change then you will need to delete the table and add a new marker.  Otherwise you will get unexpected results.


## Matplotlib Graph

A Matplotlib figure can be rendered into the doc.

```python

my_graph = plt.figure()  ## Important: define figure first
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

update_google_doc("1QtvuBOB-mzzuC23mqVmR6c_RGk8dNkI1tO4bQy6TLls", locals())
```

All updates of the graph will keep the same image dimensions of the graph in the doc as this could have been changed since first inserted.

**Warning**: Make sure you define figure first before working on the graph.

