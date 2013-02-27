#!/usr/bin/python

import sys
import os

from lxml import etree

import simplejson

def ns(val):
	return '{http://www.topografix.com/GPX/1/1}' + val

def quantize(flt):
	from decimal import Decimal, ROUND_HALF_DOWN
	# 0.00001 corresponds to roughly a meter
	return Decimal(flt).quantize(Decimal('0.00001'), rounding=ROUND_HALF_DOWN)

def extractSegments(root):
	gpxname = None
	segments = []
	for trk in root.iterdescendants(ns('trk')):
		points = []

		name = trk.find(ns('name'))
		if name is not None:
			gpxname = name.text

		for trkpt in trk.iterdescendants(ns('trkpt')):
			vals = trkpt.values()
			# lat, long --> long, lat
			long = quantize(float(vals[1]))
			lat = quantize(float(vals[0]))
			points.append([long, lat])

		segments.append(points)

	return (gpxname, segments)

def getBBox(segments):
	longs, lats = zip(*[(long, lat) for sublist in segments for long, lat in sublist])

	minlat = min(lats)
	maxlat = max(lats)
	minlong = min(longs)
	maxlong = max(longs)

	return [minlong, minlat, maxlong, maxlat]

def extractGeometry(gpxstream):
	root = etree.parse(gpxstream).getroot()

	gpxname, segments = extractSegments(root)

	bbox = getBBox(segments)

	points = None
	if len(segments) == 1:
		geometry_type = "Polygon"
		points = [segments[0]]
	elif len(segments) > 1:
		geometry_type = "MultiPolygon"
		points = [[seg] for seg in segments]

	return (
		gpxname,
		{
			'type' : geometry_type,
			'coordinates' : points
		},
		bbox
	)

def makeFeatureCollection(features):
	d = {}
	if len(features):
		d['bbox'] = [
				min(f['bbox'][0] for f in features),
				min(f['bbox'][1] for f in features),
				max(f['bbox'][2] for f in features),
				max(f['bbox'][3] for f in features),
			]

	d['type'] = 'FeatureCollection'
	d['features'] = features

	return d

if __name__ == '__main__':
	gpxdir = sys.argv[1]

	collection_name = sys.argv[2]

	# Ex: "Artilect.regions."
	if len(sys.argv) < 4:
		javascript_var_name = sys.argv[3]

	if not os.path.isdir(gpxdir):
		raise "provide path to gpxdir"

	gpxfiles = [gpxdir + '/' + f for f in os.listdir(gpxdir) if f.endswith('.gpx') ]

	features = []

	for gpxfile in gpxfiles:
		gpxstream = open(gpxfile)
		name, geometry, bbox = extractGeometry(gpxstream)

		if name == None:
			print "No name found in gpx " + gpxfile + ". Using filename"
			name = gpxfile
			#raise Exception("No <name> tag found in gpx " + gpxfile)

		features.append({
			'type':'Feature',
			'properties': {'name': name},
			'bbox': bbox,
			'geometry': geometry
		})

	print (javascript_var_name +
	collection_name + "=" +
	simplejson.dumps(makeFeatureCollection(features), sort_keys=True, indent=1) +
	";")
