from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

start_date = datetime(2000, 1, 12, 0, 0, 0)  # Укажи свою дату здесь

@app.route('/')
def valentine():
    return render_template('valentine.html', start_date=start_date.strftime("%Y-%m-%dT%H:%M:%S"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)