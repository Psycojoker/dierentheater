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

# Usage

To launch the scraping (this is *long*, do this in a screen):

    python manage.py runscript total_scraping

But aware that by default the parser store every page he has encountered in the
folder dump but re-download it (for a maximum number of 2 more times) if it has
problems with it. If you want to reset the cache simply run:

    rm dump/*

To launch the dev server:

    python manage.py runserver

# Public instance

Not official-but-still-in-the-readme demo: http://dieren.vnurpa.ethylix.be

# Licence

agplv3+ for code and ODbL for data
