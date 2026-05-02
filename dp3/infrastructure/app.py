import json
import urllib.parse
import boto3
import requests
import logging
from chalice import Chalice
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Chalice(app_name='infrastructure')

BUCKET_NAME = 'ds5220-iss-bella2'
TABLE_NAME = 'ISS_Tracker'


@app.route('/')
def index():
    return {
        "about": "Tracks the International Space Station position every 10 minutes and plots its orbital path.",
        "resources": ["current", "trend", "plot"]
    }


@app.route('/current')
def current():
    try:
        table = boto3.resource('dynamodb', region_name='us-east-1').Table(TABLE_NAME)
        res = table.query(
            KeyConditionExpression=Key('device').eq('iss'),
            ScanIndexForward=False,
            Limit=1
        )
        if not res.get('Items'):
            return {"response": "No data collected yet."}
        latest = res['Items'][0]
        lat = float(latest['lat'])
        lon = float(latest['lon'])
        return {"response": f"ISS is currently at Lat: {lat:.2f}, Lon: {lon:.2f}"}
    except Exception as e:
        logger.error(f"Error in /current: {e}")
        return {"response": f"Error fetching current position: {str(e)}"}


@app.route('/trend')
def trend():
    try:
        table = boto3.resource('dynamodb', region_name='us-east-1').Table(TABLE_NAME)
        res = table.query(
            KeyConditionExpression=Key('device').eq('iss'),
            ScanIndexForward=False,
            Limit=20
        )
        items = res.get('Items', [])
        if len(items) < 2:
            return {"response": "Not enough data yet for trend analysis."}
        lats = [float(i['lat']) for i in items]
        lons = [float(i['lon']) for i in items]
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        return {"response": f"Over last {len(items)} samples, avg position: Lat {avg_lat:.2f}, Lon {avg_lon:.2f}"}
    except Exception as e:
        logger.error(f"Error in /trend: {e}")
        return {"response": f"Error computing trend: {str(e)}"}


@app.route('/plot')
def plot():
    try:
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/latest_plot.png"
        return {"response": url}
    except Exception as e:
        logger.error(f"Error in /plot: {e}")
        return {"response": f"Error: {str(e)}"}


@app.schedule('rate(10 minutes)')
def run_ingestion(event):
    try:
        logger.info("Starting ISS ingestion...")

        r = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
        r.raise_for_status()
        data = r.json()
        logger.info(f"Fetched ISS data: {data}")

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(TABLE_NAME)
        item = {
            'device': 'iss',
            'timestamp': int(data['timestamp']),
            'lat': data['iss_position']['latitude'],
            'lon': data['iss_position']['longitude']
        }
        table.put_item(Item=item)
        logger.info(f"Saved to DynamoDB: {item}")

        res = table.query(
            KeyConditionExpression=Key('device').eq('iss'),
            ScanIndexForward=False,
            Limit=20
        )
        items = res.get('Items', [])
        logger.info(f"Retrieved {len(items)} items for plot")

        if len(items) < 2:
            logger.info("Not enough data to plot yet, skipping chart generation")
            return

        lats = [float(i['lat']) for i in items]
        lons = [float(i['lon']) for i in items]

        chart_config = {
            "type": "line",
            "data": {
                "labels": [str(round(lo, 2)) for lo in lons],
                "datasets": [{
                    "label": "ISS Latitude",
                    "data": lats,
                    "borderColor": "rgb(255,99,132)",
                    "fill": False
                }]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": "ISS Path - Lat vs Lon"
                }
            }
        }

        chart_url = "https://quickchart.io/chart?c=" + urllib.parse.quote(json.dumps(chart_config))
        logger.info("QuickChart URL built, fetching image...")

        img_response = requests.get(chart_url, timeout=15)
        img_response.raise_for_status()
        logger.info("Chart image downloaded successfully")

        s3 = boto3.client('s3', region_name='us-east-1')
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key='latest_plot.png',
            Body=img_response.content,
            ContentType='image/png',

        )
        logger.info(f"Plot uploaded to S3: s3://{BUCKET_NAME}/latest_plot.png")

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in run_ingestion: {e}", exc_info=True)
