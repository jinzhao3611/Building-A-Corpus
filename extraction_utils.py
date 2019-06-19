import re
import pickle
from geotext import GeoText
import json
import get_wikidata


class ExtractInfo(object):
    """
    this class process and clean the data loaded from the pickle file
    """
    def __init__(self, title, info_box, wikitext):
        self.title = title
        self.info_box = info_box
        self.wikitext = wikitext

    def _title_extract(self):
        """
        return the title as the film name
        :return: title
        """
        return self.title

    def _director_extract(self):
        """
        if the value of 'director' key is empty or the 'director' key doesn't exist at all, return an empty list
        replace all the <br /> <br> \n, *, [], {}, Plain List, plainlist, Plainlist with tab, then split the string when encountered tab
        in situations like [[Kamal (director)|Kamal]], the name on the left hand of the pipe tends to be a full name, therefore is kept
        to remove unrelated characters like ubl, assuming the length of real names are longer than 3, the strings that are shorted than 3 are removed
        :return: a list of director names of a movie.
        """
        if self.info_box.get('director') is None:
            return []
        re_pattern = re.compile(r'(<br\s?\/?>)|(\n)|(\*)|([\[\]{}])|([pP]lain\s?[lL]ist)')
        raw_lst = re.sub(re_pattern, '\t', self.info_box.get('director')).split('\t')

        lst = [ele.split('|')[0].strip() for ele in raw_lst if len(ele.split('|')[0].strip()) > 3]

        return lst

    def _star_extract(self):
        """
        if the value of 'starring' key is empty or the 'starring' key doesn't exist at all, return an empty list
        replace all the <br /> <br> \n, *, [], {}, Plain List, plainlist, Plainlist with tab, then split the string when encountered tab
        to remove unrelated characters like ubl, assuming the length of real names are longer than 3, the strings that are shorted than 3 are removed
        :return: a list of actor names.
        """
        if self.info_box.get('starring') is None:
            return []
        re_pattern = re.compile(r'(<br\s?\/?>)|(\n)|(\*)|([\[\]{}])|([pP]lain\s?[lL]ist)')
        raw_lst = re.sub(re_pattern, '\t', self.info_box.get('starring')).split('\t')
        lst = [ele.split('|')[0].strip() for ele in raw_lst if len(ele.split('|')[0].strip()) > 3]

        return lst

    def _rtime_extract(self):
        """
        if the value of 'runtime' key is empty or the 'runtime' key doesn't exist at all, return an empty list
        if there is only one number in the list, I assume it's in minutes;
        if the first number is greater than 10, I assume it's in minutes
        In example of 1 hour and 59 minutes, if the length of list is greater than 2, and the first number is smaller than 10,
        I assume the first number is hour, the second number is minute, the first number will multiply 60 and added to the second number
        :return: the time in minutes
        """
        if self.info_box.get('runtime') is None:
            return []
        digit_lst = [int(d) for d in re.findall(r'\d+', self.info_box['runtime'])]

        if len(digit_lst) < 2:
            return digit_lst
        elif digit_lst[0] > 10:
            return digit_lst[:1]
        else:
            return [digit_lst[0] * 60 + digit_lst[1]]

    def _country_extract(self):
        """
        see _director_extract
        :return: a list of the country name
        """
        if self.info_box.get('country') is None:
            return []
        re_pattern = re.compile(r'(<br\s?\/?>)|(\n)|(\*)|([\/\[\]{}])|([pP]lain\s?[lL]ist)')
        raw_lst = re.sub(re_pattern, '\t', self.info_box.get('country')).split('\t')
        lst = [ele.split('|')[0].strip() for ele in raw_lst
               if len(ele.split('|')[0].strip()) > 3 and ele.split('|')[0].strip().istitle()]

        return lst

    def _lang_extract(self):
        """
        see _director_extract
        :return: a list of language names
        """
        if self.info_box.get('language') is None:
            return []
        re_pattern = re.compile(r'(<br\s?\/?>)|(\n)|(\*)|([\/\[\]{}])|([pP]lain\s?[lL]ist)')
        raw_lst = re.sub(re_pattern, '\t', self.info_box.get('language')).split('\t')
        lst = [ele.split('|')[0].strip() for ele in raw_lst if len(ele.split('|')[0].strip()) > 3]
        return lst

    # -------------------------- IN WIKITEXT ------------------------
    def _plot_extract(self):
        """
        this method is used to extract time and location. I assume the time and location of the movie will appear in plot
        plot are surrounded by ==Plot== and ==, using re to find the plot and return it
        :return:
        """
        pattern = r'==\s?Plot\s?==.*?=='
        textList = re.findall(pattern, self.wikitext, flags=re.DOTALL)
        return textList

    def _time_extract(self):
        """
        if there is no plot, return an empty list
        otherwise, find all the four digit number in the plot and return the first number
        :return:
        """
        if not self._plot_extract():
            return ''
        # all four-digit number
        lst = re.findall(r'\b[12]\d{3}\b', self._plot_extract()[0])
        if not lst:
            return ''
        return lst[0]

    def _location_extract(self):
        """
        if there is no plot, return an empty list
        using GeoText to find all the cities mentioned in the plot along with the country name that they belong to
        I assume the country name that got mentioned most is the location of the film
        :return: a string of country name
        """
        if not self._plot_extract():
            return ''
        places = GeoText(self._plot_extract()[0]).country_mentions
        if not places:
            return ''
        # cities = places.cities
        return list(places.items())[0][0]

    def _category_extract(self):
        """
        split the wikitext by line, find all the lines that has "Category:"
        split the line by ":" into two halves, take the
        :return:
        """
        lst = list()

        # textList = re.split(r'==\s?External [lL]inks\s?==', self.wikitext)
        # if len(textList) == 1:
        #     return []
        # linksString = textList[1]
        lines = self.wikitext.split("\n")

        for line in lines:
            if "Category:" in line:
                # line is a string looks like this: [[Category:Films shot in multiple languages]]
                lineList = line.split(":")
                # take the second element excluding the last two characters: ]]
                category = lineList[1][:-2]
                lst.append(category)
        return lst


    def _text_extract(self):

        # remove <ref> <ref/> and everything in between
        re_pattern1 = re.compile(r'<ref.*?>.*?<\/ref>', flags=re.DOTALL)
        # remove individual tags such as <ref name="VF"> <br> # remove [[]] # remove {{cite web}}
        re_pattern2 = re.compile(r'(<[a-zA-Z\/][^>]*>)|([\[\]])|({{cite web.*?}})')
        str = re.sub(re_pattern1, ' ', self.wikitext)

        return re.sub(re_pattern2, '', str)

    def __call__(self, *args, **kwargs):
        if not isinstance(self.info_box, dict):
            self.info_box = dict()
        inner_dict = dict()
        inner_dict['Title'] = self._title_extract()
        inner_dict['Director'] = self._director_extract()
        inner_dict['Starring'] = self._star_extract()
        inner_dict['Running_time'] = self._rtime_extract()
        inner_dict['Country'] = self._country_extract()
        inner_dict['Language'] = self._lang_extract()
        inner_dict['Time'] = self._time_extract()
        inner_dict['Location'] = self._location_extract()
        inner_dict['Categories'] = self._category_extract()
        inner_dict['Text'] = self._text_extract()
        return inner_dict


if __name__ == "__main__":
    w2p = get_wikidata.Wiki2pkl('Category:2018 films')
    w2p('data/raw_movie.pkl')
    with open('data/raw_movies_with_title.pkl', 'rb') as f:
        p = pickle.load(f)

    json_dict = {}
    for i, d in enumerate(p):
        infobox = list(d.values())[0][1]
        title = list(d.keys())[0]
        wikitext = list(d.values())[0][0]
        ei = ExtractInfo(title, infobox, wikitext)
        json_dict[i] = ei()

    with open('data/films2018.json', 'w') as f:
        json.dump(json_dict, f)
        print("finish dumping!")


