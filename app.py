from flask import Flask, render_template, request, redirect
import webbrowser
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
from gtts import gTTS
import os
import platform



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
speech_lock = threading.Lock()
lang = 'en'

class Good(db.Model):
    item_number = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    datecreated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Good {self.item_number}>'
    
with app.app_context():
    db.create_all()



@app.route('/', methods=['POST', 'GET'])
def index():
    goods = Good.query.order_by(Good.item).all() 

    if request.method == 'POST':
        try:
            item = request.form['item']
            quantity = int(request.form['quantity'])
            price = float(request.form['price'])

            new_good = Good(item=item, quantity=quantity, price=price)
            db.session.add(new_good)
            db.session.commit()
            return redirect('/')  
        
        except Exception as e:
            return render_template('index.html', goods=goods, error=f"Error adding good: {e}") 

    return render_template('index.html', goods=goods) 

@app.route('/delete/<int:item_number>')
def delete(item_number):
    deleted_good = Good.query.get_or_404(item_number)

    try:
        db.session.delete(deleted_good)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f'Error deleting good: {e}'

@app.route('/budget', methods=['POST', 'GET'])
def budget():
    if request.method == 'POST':
        try:
            budget = request.form['budget']
            budget = float(budget)
            goods = Good.query.order_by(Good.item).all()
            total = 0
            for good in goods:
                total += (good.price * good.quantity)
            if total > budget:
                return render_template('budgeted.html', total=total, budget=budget)
            else:
                return render_template('budgeted.html', total=total, budget=budget)
        except Exception as e:
            return render_template('index.html', error=f"Error calculating budget: {e}")
    return render_template('budget.html')

@app.route('/update/<int:item_number>', methods=['GET', 'POST'])
def update(item_number):

    good = Good.query.get_or_404(item_number) 

    if request.method == 'POST':
        try:
            good.item = request.form['item']
            good.quantity = int(request.form['quantity']) 
            good.price = float(request.form['price'])  
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f"Error updating good: {e}" 

    return render_template('update.html', good=good)  

@app.route('/speak/<int:item_number>')
def speak(item_number):

    spoken_good = Good.query.get_or_404(item_number)

    try:
        tts = gTTS(f"Item: {spoken_good.item}, Quantity: {spoken_good.quantity}, Price: ${spoken_good.price * spoken_good.quantity}", lang=lang)
        tts.save("speech.mp3")

        if platform.system() == "Darwin":
            os.system("afplay speech.mp3")
        elif platform.system() == "Linux":
            os.system("mpg321 speech.mp3")
        elif platform.system() == "Windows":
            os.system("start speech.mp3")
        else:
            print("Unsupported operating system for speech.")
            return "Unsupported operating system for speech."

    except Exception as e:
        return f"Error speaking good: {e}"

    return redirect('/')

@app.route('/language', methods=['POST', 'GET'])
def language():
    global lang
    if request.method == 'POST':
        lang = request.form['language']
        return redirect('/')

    return redirect('/')

    
if __name__ == "__main__":
    app.run(debug=True)