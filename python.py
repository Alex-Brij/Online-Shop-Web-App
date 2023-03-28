from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db = SQLAlchemy(app)
app.app_context().push()

# table to hold items
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True)
    description = db.Column(db.String)
    price = db.Column(db.Integer)
    environmental_impact = db.Column(db.Integer)
    image = db.Column(db.String)

# method to add an item to the table
    @staticmethod
    def add_item(name, description, price, image):
        item = Item(name=name, description=description, price=price, image=image)
        db.session.add(item)
        db.session.commit()
        return item
# method to display item as its name   
    def __repr__(self):
        return f'{self.name}'

# renders home page with all items from database
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html', items=Item.query.all())

# gets the item that has been clicked on and sends user to item page which is now showing the information specific to that item 
@app.route('/item', methods=['GET', 'POST'])
def item():
    selected_item = request.args.get('type')
    print(selected_item)
    return render_template('item.html', item=Item.query.filter_by(name=selected_item).first())


@app.route('/basket', methods=['GET', 'POST'])
def basket():
    return render_template('basket.html')


if __name__ == '__main__':
    db.create_all()
    if Item.query.filter_by(name='table').first() is None:
        Item.add_item('table', 'wooden thing to hold plates', 100, 'table.jpg')
    if Item.query.filter_by(name='chair').first() is None:
        Item.add_item('chair', 'wooden thing to sit on', 50, 'chair.jpg')
    app.run(debug=True)