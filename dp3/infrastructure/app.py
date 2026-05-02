import boto3
import requests
from chalice import Chalice
from boto3.dynamodb.conditions import Key

app = Chalice(app_name='infrastructure')

BUCKET_NAME = 'ds5220-iss-bella'

@app.route('/')
def index():
    return {
        "about": "Tracks the International Space Station coordinates and generates an orbital path plot.",
        "resources": ["current", "trend", "plot"]
    }

@app.route('/current')
def current():
    table = boto3.resource('dynamodb').Table('ISS_Tracker')
    res = table.query(KeyConditionExpression=Key('device').eq('iss'), ScanIndexForward=False, Limit=1)
    if not res.get('Items'):
        return {"response": "No data collected yet."}
    latest = res['Items'][0]
    return {"response": f"The ISS is currently over Lat: {latest['lat']}, Lon: {latest['lon']}"}

@app.route('/plot')
def plot():
    url = f"https://{BUCKET_NAME}.s3.amazonaws.com/latest_plot.png"
    return {"response": url}

@app.route('/trend')
def trend():
    return {"response": "The ISS maintains an orbital speed of ~17,100 mph."}

@app.schedule('rate(10 minutes)')
def run_ingestion(event):
    try:
        # 1. Fetch current ISS position
        r = requests.get("http://api.open-notify.org/iss-now.json")
        data = r.json()
        
        # 2. Setup AWS Resources
        db = boto3.resource('dynamodb')
        table = db.Table('ISS_Tracker')
        s3 = boto3.client('s3')
        
        # 3. Save to DynamoDB
        table.put_item(Item={
            'device': 'iss',
            'timestamp': int(data['timestamp']),
            'lat': data['iss_position']['latitude'],
            'lon': data['iss_position']['longitude']
        })

        # 4. Generate Plot Data (Pull last 10 points)
        res = table.query(KeyConditionExpression=Key('device').eq('iss'), Limit=10)
        # QuickChart needs strings or numbers for the URL
        lats = [float(i['lat']) for i in res['Items']]
        lons = [float(i['lon']) for i in res['Items']]

        # 5. Call QuickChart API to get an image
        # This creates a simple line chart of Latitude vs Longitude
        chart_config = {
            "type": "line",
            "data": {
                "labels": lons,
                "datasets": [{"label": "ISS Path", "data": lats, "borderColor": "blue"}]
            }
        }
        chart_url = f"https://quickchart.io/chart?c={chart_config}".replace(" ", "")
        
        # 6. Download image and upload to S3
        img_response = requests.get(chart_url)
        if img_response.status_code == 200:
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key='latest_plot.png',
                Body=img_response.content,
                ContentType='image/png',
                ACL='public-read'  # Makes it viewable on Discord
            )
            print("Plot successfully updated in S3.")

    except Exception as e:
        print(f"Error during ingestion/plotting: {e}")