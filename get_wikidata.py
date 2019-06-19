import pickle
import wptools
import wikipediaapi
import codecs
import os


class Wiki2pkl(object):
    """
    extract the data from the wikipedia pages and dump a list of one-element dictionary into pickle file, title as key, a list of infobox and wikitext as value
    """
    def __init__(self, category):
        wiki = wikipediaapi.Wikipedia('en')
        cat = wiki.page(category)
        # the last 8 elements are not actually titles, they are sliced off.
        # they are 'Category:Lists of 2018 films by country or language',
        # 'Category:2018 3D films',
        # 'Category:2018 animated films',
        # 'Category:2018 direct-to-video films',
        # 'Category:2018 horror films',
        # 'Category:2018 martial arts films',
        # 'Category:2018 short films',
        # 'Category:2018 television films'
        self.titles = [wiki.page(p).title for p in cat.categorymembers][:-8]

    def _get_data(self, title):
        """
        :param title: wiki title (film name)
        :return: a list of (infobox [dict], wikitext [string])
        """
        page = wptools.page(title)
        page.get_parse(show=False)
        wikitext = page.data['wikitext']  # freetext of film 101
        infobox = page.data['infobox']  # infobox of film 101
        return [wikitext, infobox]

    def __call__(self, filename):
        """
        :return: a pickle file of movie data
        """
        if os.path.exists(filename):
            print('{} already exist!'.format(filename))
            return
        movie_lst = [{title: self._get_data(title)} for title in self.titles]
        with codecs.open(filename, 'wb') as f:
            pickle.dump(movie_lst, f)
        print("Finished dumping into pickle")

