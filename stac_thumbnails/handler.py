"""Skeleton of a handler."""

import logging
import uuid
import json
import os

import rasterio
import numpy as np
import boto3


logger = logging.getLogger("lambda_thumbnails")
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

BAND_CONFIGURATION = os.getenv('BAND_CONFIGURATION')
VSI_PATH = os.getenv('VSI_PATH')

def handler(event, context):
    for record in event['Records']:
        stac_item = json.loads(record['body'])
        tempfile = f"/tmp/{uuid.uuid4()}.jpg"

        if BAND_CONFIGURATION:
            band_ids = BAND_CONFIGURATION.split('/')
            thumbnail = np.stack([
                build_thumbnail(stac_item['assets'][id]['href'])[0,:,:] for id in band_ids
            ], axis=0)
        else:
            thumbnail = build_thumbnail(stac_item['assets']['data']['href'])

        bands, new_height, new_width = thumbnail.shape

        with rasterio.open(tempfile, 'w', driver='JPEG', width=new_width, height=new_height,count=bands, dtype='uint8') as dst:
            dst.write(thumbnail)

        # Upload tempfile to S3
        out_bucket = stac_item['assets']['thumbnail']['href'].split('.')[0].split('/')[-1]
        out_key = '/'.join(stac_item['assets']['thumbnail']['href'].split('/')[3:])
        print(f"Uploading to s3://{out_bucket}/{out_key}.")

        s3.upload_file(tempfile, out_bucket, out_key)

def build_thumbnail(infile):
    if VSI_PATH:
        infile = VSI_PATH + infile
    print("Input image: {}".format(infile))
    with rasterio.open(infile) as src:
        # Downsample to 1/7th the original width/height
        new_height = int(src.height / 7)
        new_width = int(src.width / 7)
        downsampled = src.read(
            out_shape=(new_height, new_width)
        )

        # Min/max stretch
        if downsampled.dtype == 'uint16':
            print("Performing min/max stretch.")
            bands = []
            for band in downsampled:
                rescaled = (band - band.min()) * (1 / (band.max() - band.min()) * 255)
                bands.append(rescaled.astype('uint8'))
            downsampled = np.stack(bands, axis=0)

        return downsampled