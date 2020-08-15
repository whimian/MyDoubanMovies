import re
import argparse
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import pandas as pd

__author__ = "Yu Hao"

HEADER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0)Gecko/20100101 Firefox/66.0"

class MovieCrawler(object):
    def __init__(self, domain='northshore', option='collect'):
        self.movie_list = None
        self.domain_name = domain
        self.initial_url = "https://movie.douban.com/people/{}/{}".format(
            domain, option)

        self.current_url = self.initial_url
        self.next_url = None

    def scrape(self):
        if self.movie_list is None:
            self.movie_list = []

        request = Request(self.current_url)
        request.add_header("User-Agent", HEADER)
        html = urlopen(request)

        bs = BeautifulSoup(html.read(), 'html.parser')

        grid_view = bs.find("div", {"class": "grid-view"})

        for item in grid_view.find_all("div", {"class": "item"}):
            temp_dict = {}
            temp_dict["image_url"] = item.find(
                "div", {"class": "pic"}).a.img['src']
            info_list = item.find("div", {"class": "info"}).ul
            title_block = info_list.find("li", {"class":"title"})
            temp_dict["title"] = title_block.find("a").em.text
            temp_dict["link"] = title_block.find("a")['href']
            intro_block = info_list.find("li", {"class":"intro"})
            temp_dict["intro"] = intro_block.string
            try:
                rating = info_list.find(
                    "span", {"class": re.compile("rating.-t")})['class'][0]
                temp_dict["rating"] = int(
                    re.search(re.compile("[1-5]"), rating)[0])
            except:
                temp_dict["rating"] = None
            temp_dict["date"] = info_list.find("span", {"class", "date"}).string

            self.movie_list.append(temp_dict)

        next_tag =bs.find("span", {"class": "next"}).a
        if next_tag is not None:
            self.next_url = "https://movie.douban.com" + next_tag["href"]
        else:
            self.next_url = None

    def crawl(self):
        self.scrape()
        while self.next_url is not None:
            self.current_url = self.next_url
            self.scrape()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Douban Movie Scraper")
    parser.add_argument('-n', '--name',
                        help='豆瓣域名',
                        type=str, default='northshore')
    parser.add_argument('-o', '--option',
                        help="选项（看过|想看|在看）",
                        type=str, default='看过')
    parser.add_argument('-f', '--file',
                        help="file name without extension name",
                        type=str, default='temp')
    args = parser.parse_args()

    option_dict = {
        '看过': 'collect',
        '想看': 'wish',
        '再看': 'do'
    }

    try:
        option_dict[args.option]
    except KeyError as identifier:
        print("No {} option".format(args.option))
    print(option_dict[args.option])
    mc = MovieCrawler(
        domain=args.name,
        option=option_dict[args.option])

    print(mc.current_url)
    mc.crawl()

    df_movie = pd.DataFrame(mc.movie_list)

    df_movie['image_url'] = df_movie['image_url'].apply(lambda x: "![]({})".format(x))

    df_movie['link'] = df_movie['link'].apply(lambda x: "[Douban]({})".format(x))

    with open("./{}.md".format(args.file), "w", encoding='utf-8') as fl:
        df_movie.to_markdown(fl)
