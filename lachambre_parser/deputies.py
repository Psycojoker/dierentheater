# -*- coding:Utf-8 -*-

#  Dieren Theater - lachambre.be to json sausage machine
#  Copyright (C) 2012  Laurent Peuch <cortex@worlddomination.be>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import logging
logger = logging.getLogger('')

from lachambre.models import Party,\
                            CommissionMembership,\
                            Commission,\
                            Question,\
                            Analysis,\
                            Deputy

from utils import retry_on_access_error,\
                  LACHAMBRE_PREFIX,\
                  get_or_create,\
                  table2dic,\
                  lame_url,\
                  read_or_dl_with_nl,\
                  read_or_dl


def clean_models():
    logger.debug("cleaning deputies models")
    map(lambda x: x.objects.all().delete(), (Deputy, Party, Analysis))


@retry_on_access_error
def deputies_list(reset=False):
    soup = read_or_dl("http://www.lachambre.be/kvvcr/showpage.cfm?section=/depute&language=fr&rightmenu=right_depute&cfm=/site/wwwcfm/depute/cvlist.cfm", "deputies", reset)

    for dep in soup('table')[4]('tr'):
        items = dep('td')
        full_name = re.sub('  +', ' ', items[0].a.text).strip()
        url = items[0].a['href']
        party = get_or_create(Party, name=items[1].a.text, url=dict(items[1].a.attrs)['href'])
        email = items[2].a.text
        website = items[3].a['href'] if items[3].a else None
        # yes, one deputies key contains a O instead of an 0, I'm not joking
        lachambre_id = re.search('key=([0-9O]+)', url).groups()[0]
        if not Deputy.objects.filter(lachambre_id=lachambre_id):
            deputy = Deputy.objects.create(full_name=full_name,
                                           party=party,
                                           url=url,
                                           websites=[website] if website else [],
                                           lachambre_id=lachambre_id,
                                           emails=[email])
            logger.debug('adding new deputy %s %s %s %s %s' % (lachambre_id.encode("Utf-8"), full_name.encode("Utf-8"), party, email.encode("Utf-8"), website.encode("Utf-8") if website else ''))
            logger.info("[NEW] deputy: %s" % deputy)


@retry_on_access_error
def check_for_new_deputies(reset=False):
    deputies_list(reset)

def scrape():
    for index, deputy in enumerate(list(Deputy.objects.all())):
        logger.debug("%s %s" % (index, deputy.full_name))
        _handle_deputy(deputy)


@retry_on_access_error
def _handle_deputy(deputy, reset=False):
    soup, suppe = read_or_dl_with_nl(LACHAMBRE_PREFIX + deputy.url, deputy.full_name, reset)
    deputy.language = soup.i.parent.text.split(":")[1] if soup.i else None
    deputy.cv["fr"] = re.sub('  +', ' ', soup('table')[5].p.text)
    deputy.cv["nl"] = re.sub('  +', ' ', suppe('table')[5].p.text)
    if deputy.cv["fr"].encode("Utf-8").startswith("Députée"):
        deputy.sex = "F"
    elif deputy.cv["fr"].encode("Utf-8").startswith("Député"):
        deputy.sex = "M"
    else:
        deputy.sex = None

    _split_deputy_full_name(deputy, soup)
    #_get_deputie_commissions(soup, deputy)
    #_deputy_documents(soup, deputy)
    deputy.save_with_history()


def _split_deputy_full_name(deputy, soup):
    # stupid special case
    if deputy.full_name == "Fernandez Fernandez Julie":
        deputy.first_name = "Julie"
        deputy.last_name = "Fernandez Fernandez"
    elif deputy.full_name == "Dedecker Jean Marie":
        deputy.first_name = "Jean Marie"
        deputy.last_name = "Dedecker"
    # here we guess the first and last name, for that we compare
    # deputy.full_name that is in the form of "de Donnea
    # François-Xavier" and the name of the deputy page which is in the
    # form of "François-Xavier de Donnea"
    elif len(deputy.full_name.split(" ")) > 2:
        it = 0
        while it < len(deputy.full_name.split(" ")):
            if soup.h2.text.split(" ")[it] != deputy.full_name.split(" ")[-(it + 1)]:
                break
            it += 1
            logger.debug("%s %s %s" % (it, soup.h2.text.split(" ")[it], deputy.full_name.split(" ")[-(it + 1)]))
        if not it:
            raise Exception
        deputy.first_name = " ".join(soup.h2.text.split(" ")[:it]).strip()
        deputy.last_name = " ".join(soup.h2.text.split(" ")[it:]).strip()
        logger.debug("%s %s" % ([deputy.first_name], [deputy.last_name]))
    else:
        # if there is only 2 words just split this in 2
        deputy.first_name = deputy.full_name.split(" ")[1].strip()
        deputy.last_name = deputy.full_name.split(" ")[0].strip()
        logger.debug("%s %s" % ([deputy.first_name], [deputy.last_name]))


def _get_deputie_commissions(soup, deputy):
    # here we will walk in a list of h4 .. h5 .. div+ .. h5 .. div+
    # look at the bottom of each deputies' page
    membership = soup.find('td', rowspan="1")
    item = membership.h4
    role = None
    deputy.commissions = []
    while item.nextSibling:
        if hasattr(item, 'tag'):
            if item.name == 'h5':
                role = item.text[6:-1]
            elif item.name == 'div':
                logger.debug("linking deputy to commission %s" % item.a.text)
                commission = get_or_create(Commission, url=item.a['href'], lachambre_id=int(re.search("com=(\d+)", item.a["href"]).groups()[0]))
                deputy.commissions.append(get_or_create(CommissionMembership, commission=commission, role=role))
        item = item.nextSibling


#@retry_on_access_error
#def _get_deputy_documents(url, deputy, role, type=None, reset=False):
    #logger.debug("working on %s %sdocuments" % (role, type + " " if type else '')  # , LACHAMBRE_PREFIX + lame_url(urls[index]))
    #soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s %s' % (deputy.full_name, type if type else '', role), reset)
    #setattr(deputy, "documents_%s%s_url" % (role, type + "_" if type else ''), url)
    #setattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else ''), [])
    #for i in soupsoup('table')[3]('tr', valign="top"):
        #logger.debug("add %s %s %s" % (type if type else '', role, i.tr('td')[1].text))
        #dico = table2dic(i.table('td'))
        #logger.debug("%s" % dico)
        #getattr(deputy, "documents_%s%s_list" % (role, type + "_" if type else '')).\
                #append(get_or_create(Document, _id="lachambre_id",
                                     #lachambre_id=re.search("dossierID=(\d+)", i.a["href"]).groups()[0],
                                     #url=i.a['href'],
                                     #title=dico["Titre :"],
                                     #status_chambre=dico.get("Chambre FR :"),
                                     #status_senat=dico.get("Sénat FR :"),
                                     #deposition_date=dico.get("Date :"),
                                     #eurovoc_main_descriptor=dico.get("Desc. Eurovoc principal :"),
                                     #eurovoc_descriptors=map(lambda x: x.strip(), dico.get("Descripteurs Eurovoc :", "").split('|')),
                                     #keywords=map(lambda x: x.strip(), dico.get("Mots-clés libres :", "").split('|'))))


#@retry_on_access_error
#def _get_deputy_written_questions(url, deputy, reset=False):
    #soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), deputy.full_name + " written questions", reset)
    #deputy.questions_written_url = url
    #deputy.questions_written_list = []
    #for i in soupsoup('table')[3]('tr', valign="top"):
        #logger.debug("add", type, i.tr('td')[1].text.strip())
        #dico = table2dic(i.table('td'))
        #logger.debug("%s" % dico)
        #deputy.questions_written_list.\
                #append(get_or_create(WrittenQuestion,
                                     #_id="lachambre_id",
                                     #title=dico["Titre"],
                                     #departement=dico.get(u"Département"),
                                     #lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                     #deposition_date=dico.get(u"Date de dépôt"),
                                     #delay_date=dico.get(u"Date de délai"),
                                     #eurovoc_descriptors=map(lambda x: x.strip(), dico.get("Descripteurs Eurovoc", "").split('|')),
                                     #keywords=map(lambda x: x.strip(), dico.get(u"Mots-clés libres", "").split("|")),
                                     #url=i.a['href']))


@retry_on_access_error
def _get_deputy_questions(url, deputy, type, reset=False):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type), reset)
    setattr(deputy, "questions_%s_url" % type, url)
    setattr(deputy, "questions_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        logger.debug("add", type, i.tr('td')[1].text.strip())
        dico = table2dic(i.table('td'))
        logger.debug("%s" % dico)
        getattr(deputy, "questions_%s_list" % type).\
                append(get_or_create(Question,
                                     _id="lachambre_id",
                                     title=dico["Titre"],
                                     lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                     reunion_type=dico.get(u"Réunion"),
                                     reunion_date=dico.get("Date discussion"),
                                     session_id=dico.get("Session"),
                                     pdf_url=dico.get(u"Compte rendu intégral", {"href": None})["href"],
                                     eurovoc_descriptors=map(lambda x: x.strip(), dico.get("Descripteurs Eurovoc", "").split('|')),
                                     keywords=map(lambda x: x.strip(), dico.get(u"Mots-clés libres", "").split("|")),
                                     url=i.a['href'],
                                     type=type))


@retry_on_access_error
def _get_deputy_analysis(url, deputy, type, reset=False):
    soupsoup = read_or_dl(LACHAMBRE_PREFIX + lame_url(url), '%s %s' % (deputy.full_name, type), reset)
    setattr(deputy, "analysis_%s_url" % type, url)
    setattr(deputy, "analysis_%s_list" % type, [])
    for i in soupsoup('table')[3]('tr', valign="top"):
        logger.debug("add", type, i.tr('td')[1].text.strip())
        dico = table2dic(i.table('td'))
        logger.debug("%s" % dico)
        getattr(deputy, "analysis_%s_list" % type).\
                append(get_or_create(Analysis,
                                     _id="lachambre_id",
                                     lachambre_id=re.search("dossierID=([0-9A-Za-z-]+)", i.a["href"]).groups()[0],
                                     title=dico["Titre"],
                                     descriptor=dico["Descripteurs"],
                                     url=i.a['href'],
                                     type=type))


def _deputy_documents(soup, deputy):
    # here we are in the grey black box
    urls = map(lambda x: x['href'], soup('div', **{'class': 'linklist_1'})[1]('a'))

    #_get_deputy_documents(urls[0], deputy, "author", "principal")
    #_get_deputy_documents(urls[1], deputy, "signator", "principal")
    #_get_deputy_documents(urls[2], deputy, "author", "next")
    #_get_deputy_documents(urls[3], deputy, "signator", "next")
    #_get_deputy_documents(urls[4], deputy, "rapporter")
    #_get_deputy_written_questions(urls[5], deputy)
    # no one seems to do any interpellations nor motions or maybe the website is just broken
    _get_deputy_questions(urls[8], deputy, "oral_plenary")
    _get_deputy_questions(urls[9], deputy, "oral_commission")
    _get_deputy_analysis(urls[10], deputy, "legislatif_work")
    _get_deputy_analysis(urls[11], deputy, "parlimentary_control")
    _get_deputy_analysis(urls[12], deputy, "divers")
