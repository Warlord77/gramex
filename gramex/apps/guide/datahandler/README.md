title: Gramex connects to data

`DataHandler` let's you fetch data from CSV files and databases, and returns the result as CSV, JSON or HTML tables. Here is a sample configuration that browses [gorilla genes](genome?format=html&limit=10):

    :::yaml
    url:
        genome-data:
            pattern: /genome
            handler: DataHandler
            kwargs:
                driver: sqlalchemy
                url: mysql+pymysql://anonymous@ensembldb.ensembl.org://gorilla_gorilla_core_84_31::gene

(This uses the public [ensemble gene database](http://ensembldb.ensembl.org/info/data/mysql.html).)

To start you off, there's a `database.sqlite3` in this application folder. (Gramex downloaded [flags data](https://gramener.com/flags/) on startup. See [fetch.data()](fetch.py) and the scheduler in [gramex.yaml](gramex.yaml).

The `DataHandler` below exposes the flags table in `database.sqlite3` at the URL [flags](flags).

    :::yaml
    flags:
      pattern: /$YAMLURL/flags                # The URL /datastore/flags
      handler: DataHandler                    # uses DataHandler
      kwargs:
        driver: blaze                         # with blaze or sqlalchemy driver
        url: sqlite:///$YAMLPATH/database.sqlite3     # to connect database at this path/url
        table: flags                          # on this table
        parameters: {encoding: utf8}          # with additional parameters provided
        default:
          format: html                        # Can also be json or csv

Once we have this setup, we can query the data with a combination of parameters like `select`, `where`, `groupby`, `agg`, `offset`, `limit`, `sort`

- `select` retrieves specific columns. E.g. [?select=Name&select=Continent](flags?select=Name&select=Continent)
- `where` filters the data. E.g. [?where=Stripes=Vertical](flags?where=Stripes==Vertical). You can use the operators `=` `&gt;=` `&lt;=` `&gt;` `&lt;` `!=`. Multiple conditions can be applied. E.g. [where=Continent=Asia&where=c1>50](flags?where=Continent=Asia&where=c1>50)
- `group` to group records on columns and aggregate them. E.g. [?groupby=Continent&agg=c1:sum(c1)](flags?groupby=Continent&agg=c1:sum(c1))
- `agg` - return a single value on grouped collection. Supported aggregations include `min`, `max`, `sum`, `count`, `mean` and `nunique`. E.g. [groupby=Continent&agg=nshapes:nunique(Shapes)](flags?groupby=Continent&agg=nshapes:nunique(Shapes))
- `limit` - limits the result to n number of records. By default, the first 100 rows are displayed. E.g. [?limit=5](flags?limit=5) shows the first 5 rows.
- `offset` - excludes the first n number of records. E.g. [?offset=5&limit=5](flags?offset=5&limit=5) shows the next 5 rows
- `sort` - sorts the records on a column in ascending order by default. You can change the order with the `:asc` / `:desc` suffixes. E.g. [?sort=Symbols:desc](flags?sort=Symbols:desc)
- `format` - determines the output format. Can be `html`, `json`, `csv`. E.g. [?format=json](flags?format=json)

Examples:

- [?groupby=Continent&agg=count:nunique(Name)&agg=shapes:count(Shapes)&sort=count:desc](flags?groupby=Continent&agg=count:nunique(Name)&agg=shapes:count(Shapes)&sort=count:desc): For every Continent, show the number of unique countries and the numbrr of countries with shapes


## DataHandler defaults

These parameters can be specified specified in the URL. But you can also set these as defaults. For example, adding this section under `kwargs:` ensures that the default format is HTML and the default limit is 10 -- but the URL can override it.

    :::yaml
    default:
        format: html
        limit: 10

You can make the parameters non-over-ridable using `query:` instead of `default:`. For example, this section forces the format to html, irrespective of what the `?format=` value is. However, `?limit=` will override the default of 10.

    :::yaml
    query:
        format: html
    default:
        limit: 10