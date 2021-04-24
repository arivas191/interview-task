from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError


class AddProductForm(FlaskForm):
    product_name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    product_description = StringField('Description', validators=[DataRequired(), Length(min=5, max=100)])
    price = DecimalField('Price (in US dollars)', validators=[DataRequired()])
    category = SelectField('Category', validators=[DataRequired()])
    add = SubmitField('Add Product')