#!/usr/bin/env python3
import logging
import os
from optparse import OptionParser

import gpxpy
import pandas
from adjustText import adjust_text
from haversine import haversine
from haversine import Unit
from matplotlib import pyplot


def generate_profile(options, files):
    waypoints = []
    tracks = []
    for file in files:
        waypoints.extend(file.waypoints)
        tracks.extend(file.tracks)

    for track in tracks:
        for segment in track.segments:
            # with pyplot.xkcd():
            generate_segment_profile(options, segment, waypoints, title=track.name)


def generate_segment_profile(
    options, segment, waypoints, title=None, axis_labels=False
):
    df = pandas.DataFrame(columns=["lon", "lat", "alt", "distance"])
    last_point = None
    distance = 0
    for point in segment.points:
        if last_point is not None:
            distance += haversine(
                (last_point.latitude, last_point.longitude),
                (point.latitude, point.longitude),
                unit=Unit.MILES,
            )
        df = df.append(
            {
                "lon": point.longitude,
                "lat": point.latitude,
                "alt": point.elevation * 3.281,
                "distance": distance,
            },
            ignore_index=True,
        )
        last_point = point

    fig, ax = pyplot.subplots(figsize=(8, 3), dpi=300)
    ax.plot(df["distance"], df["alt"], color="#666666", linewidth=0.8)
    ax.set_xlim(0, distance)
    if axis_labels:
        ax.set(xlabel="Miles", ylabel="Feet", title=title)
    elif title:
        ax.set(title=title)
    ax.grid(color="#dddddd")

    labels = []
    for waypoint in waypoints:
        x = None
        y = None
        closest_distance = None

        for row in df.itertuples(index=True):
            distance = haversine(
                (getattr(row, "lat"), getattr(row, "lon")),
                (waypoint.latitude, waypoint.longitude),
                unit=Unit.METERS,
            )
            if distance < 500 and (
                closest_distance is None or distance < closest_distance
            ):
                closest_distance = distance
                x = getattr(row, "distance")
                y = getattr(row, "alt")

        if x is not None and y is not None:
            labels.append(pyplot.text(x, y, waypoint.name, fontsize=6))

    if options.avoid_lines:
        adjust_text(
            labels,
            x=df["distance"],
            y=df["alt"],
            arrowprops=dict(arrowstyle="->", color="black", lw=0.3),
        )
    else:
        adjust_text(labels, arrowprops=dict(arrowstyle="->", color="black", lw=0.3))

    fig.savefig("test.png")
    # pyplot.show()


def _main():
    usage = "usage: %prog"
    parser = OptionParser(usage=usage, description="")
    parser.add_option(
        "-d", "--debug", action="store_true", dest="debug", help="Turn on debug logging"
    )
    parser.add_option(
        "-q", "--quiet", action="store_true", dest="quiet", help="turn off all logging"
    )
    parser.add_option(
        "-l",
        "--avoid-lines",
        action="store_true",
        dest="avoid_lines",
        help="Dont let labels overlap lines",
    )

    (options, args) = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG
        if options.debug
        else (logging.ERROR if options.quiet else logging.INFO)
    )

    files = []
    for path in args:
        with open(path, "r") as f:
            gpx = gpxpy.parse(f)
            files.append(gpx)

    generate_profile(options, files)


if __name__ == "__main__":
    _main()
