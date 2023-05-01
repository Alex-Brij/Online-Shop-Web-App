from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, HiddenField, StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'lily!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
# initialise main class of flask_login- LoginManager, stored in lm global variable
lm = LoginManager(app)
# needs to know where login page is. Sends login view to endpoint name of login route (name of function that handles that request)
# in this case function is called login
lm.login_view = 'login'
app.app_context().push()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(1, 16)])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    password_hash = db.Column(db.String(64))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def register(username, password):
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def __repr__(self):
        return '<User {0}>'.format(self.username)
    
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            return redirect(url_for('login', **request.args))
        login_user(user, form.remember_me.data)
        session['userid']=user.id
        return redirect(request.args.get('next') or url_for('home'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



# table to hold items
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
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


class Basket_item(db.Model):
    __tablename__ = 'basket'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# method to add item to basket
    def add_item_to_basket(item_id, quantity, current_user):
        exists = db.session.query(db.exists().where((Basket_item.item_id == item_id) & (Basket_item.user_id == current_user))).scalar()
        if exists:
            item = Basket_item.query.filter_by(item_id=item_id, user_id=current_user).first()
            old_quantity = item.quantity
            new_quantity = old_quantity + int(quantity)
            Basket_item.query.filter_by(item_id=item_id, user_id=current_user).delete()
            item = Basket_item(item_id=item_id, quantity=int(new_quantity), user_id = current_user)
            db.session.add(item) 
        else:
            item = Basket_item(item_id=item_id, quantity=int(quantity), user_id = current_user)
            db.session.add(item)

        db.session.commit()
        return item
    

# method to change quantity of items in basket 
    def change_quantity(item_id, quantity, current_user):
        if int(quantity) > 0:
            item = Basket_item.query.filter_by(item_id=item_id, user_id = current_user).first()
            item.quantity = int(quantity)
        else:
            Basket_item.query.filter_by(item_id=item_id, user_id=current_user).delete()

        db.session.commit()


# renders home page with all items from database
# if number entered in form for adding items to bsket it gets the number and prints it
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        quantity = request.form['quantity']
        item_id = request.form['item_id']
        print(f'{quantity} {item_id} added to basket')
        Basket_item.add_item_to_basket(item_id, quantity, session['userid'])
        return redirect(url_for('home')) 
    return render_template('home.html', items=Item.query.all())


# gets the item that has been clicked on and sends user to item page which is now showing the information specific to that item 
@app.route('/item', methods=['GET', 'POST'])
def item():
    selected_item = request.args.get('type')
    print(selected_item)
    return render_template('item.html', item=Item.query.filter_by(name=selected_item).first())


@app.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
    if request.method == 'POST':
        item_id = request.form['item_id']
        quantity = request.form['quantity']
        Basket_item.change_quantity(item_id, quantity, session['userid'])
        return redirect(url_for('basket'))
    return render_template('basket.html', basket=Basket_item.query.filter_by(user_id = session['userid']), Item=Item)



if __name__ == '__main__':
    db.create_all()
    if Item.query.filter_by(name='table').first() is None:
        Item.add_item('table', 'wooden thing to hold plates', 100, 'table.jpg')
    if Item.query.filter_by(name='chair').first() is None:
        Item.add_item('chair', 'wooden thing to sit on', 50, 'chair.jpg')

    if User.query.filter_by(username='lily').first() is None:
        User.register('lily', 'eye')
    if User.query.filter_by(username='al').first() is None:
        User.register('al', 'cat')
    app.run(debug=True)