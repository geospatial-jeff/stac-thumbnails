# lambda_thumbnails

Simple SQS/lambda event to generate thumbnails from STAC Items.  The function uses the `assets` field to determine what image to read and where to save the thumbnail.  For example, the following incomplete STAC Item creates a thumbnail of **`https://data.tif`** and saves it to **`s3://thumbnail-bucket/data_thumbnail.jpg`**.

```json
{
  "assets": {
    "data": {
      "href": "https://data.tif"
    },
    "thumbnail": {
      "href": "https://thumbnail-bucket.s3.amazonaws.com/data_thumbnail.jpg"
    }
  }
}
```

Many STAC Items store each unique band as an individual asset.  You can specify which asset to use when generating the thumbnail by configuring the BAND_CONFIGURATION environment variable.  The function expects R/G/B band ordering.

```
functions:
  buildThumbnail:
    environment:
      BAND_CONFIGURATION: "B3/B2/B1"
```

### Deployment
```
git clone https://github.com/geospatial-jeff/stac-thumbnails.git
cd stac-thumbnails
make build
sls deploy -v
```

### Notes
Created with [lambda-pyskel](https://github.com/vincentsarago/lambda-pyskel).