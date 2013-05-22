#!/usr/bin/env python

import os
from BeautifulSoup import BeautifulSoup
import urllib2
import config, smtplib, string, re
from datetime import datetime


imdb_movie_page = 'http://www.imdb.com/showtimes/cinemas/US/83651'
message = ''

def get_theater_shows(theater):
  movies = {}
  all_movies = theater.findAll('div', {'itemtype' : 'http://schema.org/Movie'})
  for movie in all_movies:
    info = movie.find('div', {'class': 'info'})
    anchor = '%s' % movie.find('a', {'itemprop': 'url'})
    if (anchor == 'None'):
      return
    url = anchor.split('href="')[1].split('"')[0]

    movie_id = url.split('title/')[1].split('/')[0]
    movies[movie_id] = '%s' % info
    movies[movie_id] = string.replace(movies[movie_id], url, 'http://www.imdb.com' + url)
  return movies

def send_message(message):
  server=smtplib.SMTP('smtp.gmail.com:587')
  server.starttls()
  server.login(config.mail_user, config.mail_password)
  senddate=datetime.strftime(datetime.now(), '%Y-%m-%d')
  subject="Movies Available in Chosen Theaters"
  m="Date: %s\r\nFrom: %s\r\nTo: %s\r\nSubject: %s\r\nX-Mailer: check_movies.py\r\nContent-Type: text/html\r\n\r\n" % (senddate, 'Movie notifications <james+movies@jrglasgow.com>', config.mail_recipient, subject)

  server.sendmail('james+movies@jrglasgow.com', config.mail_recipient, m+message)
  server.quit()

if __name__ == '__main__':
  shows = ''
  # first get a list of all the shows that are currently in the theaters
  page = urllib2.urlopen(imdb_movie_page).read()#.split('<script')

  # strip out all <script> tags from the page since we won't be needing them and
  # they have caused problems
  #new_page = '';
  #for segment in page:
  #  if '</script>' in segment:
  #    new_page += segment.split('</script>')[1]
  #  else:
  #    new_page += segment
  #  pass
  #page = new_page

  # remove all but the body of the HMTL
  page = page.split('<body')[1].split('</body>')[0]

  soup = BeautifulSoup(page)
  theater_list = soup.find('div', {'id': 'cinemas-at-list'})
  theaters = theater_list.findAll('div', {'itemtype' : 'http://schema.org/MovieTheater'})
  theater_shows = {}
  for theater in theaters:
    theater_name = "%s" % theater.find('h3', {'itemprop': 'name'})
    theater_name = theater_name.split('</a>')[0].split('>')[-1]
    theater_shows[theater_name] = get_theater_shows(theater)

  #now that we know what is showing in the area we check against our list
  for theater in config.theaters:
    if (theater in theater_shows):
      this_theaters_shows = ''
      for movie_id, movie_title in config.movies.iteritems():
        if (movie_id in theater_shows[theater]):
          this_theaters_shows += theater_shows[theater][movie_id]
          #shows += "\t%s - <a href=\"http://www.imdb.com/title/%s\">%s</a>\n" % (theater, movie_id, movie_title)
      if (this_theaters_shows != ''):
        shows += "<hr/>%s<br/>%s" % (theater, this_theaters_shows)

  if (shows):
    message =  "The following movies are currently available in your chosen theaters:\n\n"
    message += shows
    send_message(message)
