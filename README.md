# amendmerge

> [!NOTE]  
> Please note that this tool is still under active development and without proper documentation. The code is not stable and the API may change in the future. Feel free to use it but be aware of the risks and contribute to the development if you can.



## Description

This is a tool to parse sources of amendments in EU legislation and merge them into the consolidated version of the legislation.


## Installation and usage

You can install the package from GitHub using pip:

```
pip install git+https://github.com/ghxm/amendMerge.git
```

For now, the package can only be used as a Python library. You can import the package to your Python script and use the functions provided by the package. For example:

```
from amendmerge.ep_report.html import HtmlEpReport

# read in a report in HTML format
with open('<path to report HTML>', 'r') as f:
    report_html = f.read()

# read in a report in HTML format
report = HtmlEpReport.create(source=report_html)

# you can start investigating the report
## get the draft resolution
resolution = report.get_ep_draft_resolution()

## check the amendment type
resolution.amendment_type

## check the parsed amendments
amendments = resolution.get_amendments()

```

