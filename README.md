# Dieren Theater

lachambre.be to json sausage machine.

# Installation

You need pip and virtualenv (or buildout).

Under debian based distributions:

    sudo apt-get install python-pip python-virtualenv

You also need mongodb:

    sudo apt-get install mongodb

And pdftotext:

    sudo apt-get install xpdf-utils

And libxml2 and libxslt for lxml:

    sudo apt-get install libxml2-dev libxslt-dev

Once this is done create a virtualenv, for example:

    virtualenv --distribute --no-site-packages ve

Then activate it:

    source ve/bin/activate

Now, install the dependencies (this can take a little bit of time):

    pip install -r requirements.txt

And install the indices:

    python manage.py syncdb

# Usage

## Scraping

To launch the scraping:

    python manage.py scrape

By default this launch all the parser, if you want to only launch some parser
you can specify them on the CLI:

    python manage.py scrape --deputies

Available options are:

    --commissions         Parse commissions
    --documents           Parse documents
    --written_questions   Parse written_questions
    --reports             Parse reports
    --deputies            Parse deputies

If you have exception, remember that you need to passe the option
<code>--traceback</code> to a django command to have the traceback (yes ...).

## Debugging

If you want to end up in [ipdb](https://github.com/gotcha/ipdb) (a python
interactive debugger) on exception, you can use the <code>--ipdb</code> option.

    python manage.py scrape --ipdb

## Dump

But aware that by default the parser store every page he has encountered in the
folder dump but re-download it (for a maximum number of 2 more times) if it has
problems with it. If you want to reset the cache simply run:

    rm dump/*

## Server

To launch the dev server:

    python manage.py runserver

# Public instance

http://www.dierentheater.be

# Licence

agplv3+ for code and ODbL for data
