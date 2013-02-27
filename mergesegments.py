#!/usr/bin/python

# Merges multiple segments from trk-style gpx file
# outputs single trk-segment without xml header and footer
#

import sys
from lxml import etree

def getSegList(gpxstream):
	x = etree.parse(gpxstream)

	#print [elem for elem in x.iter('{http://www.topografix.com/GPX/1/1}trkseg')]

	ns = '{http://www.topografix.com/GPX/1/1}'

	segments = []

	for trkseg in x.iter(ns + 'trkseg'):
		nodelist = []
		for trkpt in trkseg.iter(ns + 'trkpt'):
			values = trkpt.values()
			lat = values[0]
			lon = values[1]
			nodelist.append((lat, lon))

		segments.append(tuple(nodelist))

	return segments

def combine(seglist):

	segset = set(seglist)

	fullseg = []
	while len(segset) > 0:
		if len(fullseg) == 0:
			fullseg += segset.pop()
			continue

		fullseg_endnode = fullseg[-1]

		# connect next
		prevsize = len(segset)
		for seg in segset:
			startnode = seg[0]
			endnode = seg[len(seg)-1]

			if startnode == fullseg_endnode:
				fullseg += seg[1:]
				segset.remove(seg)
				break
			elif endnode == fullseg_endnode:
				fullseg += reversed(seg[:-1])
				segset.remove(seg)
				break

		if prevsize == len(segset):
			print fullseg_endnode
			print >> sys.stderr, 'None found, epsilon to small?'
			sys.exit(1)

	return fullseg

if __name__ == '__main__':
	if not len(sys.argv) == 2:
		print 'Give filename as arg'
		exit()

	filename = sys.argv[1]
	#print 'Processing file', filename

	segList = getSegList(filename)
	fullSeg = combine(segList)

	for lat, lon in fullSeg:
		print '<trkpt lat="%s" lon="%s">' % (lat, lon)
