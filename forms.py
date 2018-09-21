from wtforms import Form, StringField, TextAreaField, PasswordField, validators

class Regform(Form):
    username = StringField('Username', [validators.Length(min=1,max=50), validators.DataRequired()])
    email = StringField('Email',[validators.DataRequired(),validators.Email()])
    password = PasswordField('Password',[validators.DataRequired(),validators.Length(min=4)])
    confirm = PasswordField('Confirm Password',[validators.EqualTo('password')])

class Loginform(Form):
    email = StringField('Email', [validators.DataRequired(),validators.Email])
    password = PasswordField('Password', [validators.DataRequired])

class Articleform(Form):
    title = StringField('Title', [validators.DataRequired(), validators.Length(min=4)])
    body = TextAreaField('Body', [validators.DataRequired(), validators.Length(min=30)])
