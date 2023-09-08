# amendmerge

## Description

This is a tool to parse sources of amendments in EU legislation and merge them into the consolidated version of the legislation.

## Classes and attributes

### `DataSource`

This class represents a data source, i.e. a source of amendments. It has the following attributes that are worth mentioning for extensibility purposes:

- `type_`: the type of the data source (e.g. EP report/resolution, Council position, etc.
- `subtype`: the subtype of the data source (e.g. Committee resolution, Plenary resolution, etc.)

- `format`: the format that the data source was parsed from
- `subformat`: the subformat that the data source was parsed from (e.g. specific version of HTML EP reports)