"""Skeleton of a handler."""

import logging
import uuid
import json

import rasterio
import numpy as np
import boto3


logger = logging.getLogger("lambda_thumbnails")
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def build_thumbnail(event, context):

    for record in event['Records']:
        stac_item = json.loads(record['body'])
        tempfile = f"/tmp/{uuid.uuid4()}.jpg"

        with rasterio.open(stac_item['assets']['data']['href']) as src:
            # Downsample to 1/7th the original width/height
            new_height = int(src.height / 7)
            new_width = int(src.width / 7)
            downsampled = src.read(
                out_shape=(new_height, new_width)
            )

            # Min/max stretch
            if downsampled.dtype == 'uint16':
                bands = []
                for band in downsampled:
                    rescaled = (band - band.min()) * (1 / (band.max() - band.min()) * 255)
                    bands.append(rescaled.astype('uint8'))
                downsampled = np.stack(bands, axis=0)

            print("Thumbnail size: {}".format(downsampled.shape))
            with rasterio.open(tempfile, 'w', driver='JPEG', width=new_width, height=new_height,count=src.count, dtype='uint8') as dst:
                dst.write(downsampled)

        # Upload tempfile to S3
        out_bucket = stac_item['assets']['thumbnail']['href'].split('.')[0].split('/')[-1]
        out_key = '/'.join(stac_item['assets']['thumbnail']['href'].split('/')[3:])
        print(f"Uploading to s3://{out_bucket}/{out_key}.")

        s3.upload_file(tempfile, out_bucket, out_key)