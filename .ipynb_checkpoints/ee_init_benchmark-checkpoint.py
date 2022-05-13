#!/usr/bin/python3
from pathlib import Path
import tempfile
from functools import partial
import multiprocessing
import requests
import shutil
import random
import time

import ee
from retry import retry

def getRequests(nb_item):
    """
    Generates a list of work items to be downloaded.

    Produces 1000 random points in each of the RESOLVE ecoregions in the ROI.
    """
  
    # Get our ROI from the GAUL regions
    gaul = ee.FeatureCollection('FAO/GAUL/2015/level1')
    roi = gaul.filter('ADM1_NAME == "Colorado"').first().geometry()

    # To stratify by RESOLVE ecoregion, paint the ECO_IDs into an image.
    resolve = ee.FeatureCollection('RESOLVE/ECOREGIONS/2017')
    ecoregions = (
        resolve.reduceToImage(['ECO_ID'], ee.Reducer.first())
        .clip(roi)
        .rename('ECO_ID')
    )
    points = ecoregions.stratifiedSample(
        numPoints=nb_item,
        classBand='ECO_ID',
        region=roi,
        scale=100,
        geometries=True
    )

    return points.aggregate_array('.geo').getInfo()

@retry(tries=10, delay=1, backoff=2)
def getResult(folder, index, point):
    """Handle the HTTP requests to download an image."""

    # Generate the desired image from the given point.
    point = ee.Geometry.Point(point['coordinates'])
    region = point.buffer(127).bounds()
    image = (
        ee.ImageCollection('USDA/NAIP/DOQQ')
        .filterBounds(region)
        .filterDate('2019', '2020')
        .mosaic()
        .clip(region)
        .select('R', 'G', 'B')
    )

    # Fetch the URL from which to download the image.
    url = image.getThumbURL({
        'region': region,
        'dimensions': '256x256',
        'format': 'png'
    })

    # Handle downloading the actual pixels.
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        r.raise_for_status()

    filename = Path(folder)/f'tile_{index}.png'
    with filename.open("wb") as out_file:
        shutil.copyfileobj(r.raw, out_file)
        
    return

if __name__ == '__main__':
    
    nb_items = random.randint(1, 5000)
    use_hv = random.getrandbits(1)
    
    if use_hv:
        ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
    else:
        ee.Initialize()
        
    # start the timer 
    start = time.time()
    with tempfile.TemporaryDirectory() as tmp_dir:
    
        items = getRequests(nb_items)
        with multiprocessing.Pool(25) as pool:
            pool.starmap(partial(getResult, tmp_dir), enumerate(items))
    
    # end it 
    end = time.time()
    
    # save information to a file 
    file = Path.cwd()/"ee_init_benchmark.csv"
    with file.open("a") as f:
        f.write(f"{use_hv},{nb_items},{end-start}\n")
    
    hv = "highvolume" if use_hv else "normal"
    print(f"run with {hv} ee.Initialize on {nb_items} in {end-start}s")