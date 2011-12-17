# Dieren Theater

lachambre.be to json saucage machine.

# Installation

You need pip and virtualenv (or buildout).

Under debian based distributions:

    sudo apt-get install python-pip python-virtualenv

You also need mongodb:

    sudo apt-get install mongodb

Once this is done create a virtualenv, for example:

    virtualenv --distribute --no-site-packages ve

Then activate it:

    source ve/bin/activate

Now, install the dependacies (this can take a little bit of time):

    pip install -r requirements.txt

# Usage

To launch the scraping (this is *long*, do this in a screen):

    mkdir dump # only once
    python manange.py runscript scrapers

But aware that by default the parser store everypage he has encoutered in the
folder dump but redownload it (for a maximum number of 2 more times) if it has
problems with it. If you want to reset the cache simply run:

    rm dump/*

To launch the dev server:

    python manange.py runserver

# Licence

agplv3+
