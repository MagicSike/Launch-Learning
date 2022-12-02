from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, EmailField 
from wtforms.validators import DataRequired, Length, Email, EqualTo, email_validator
from flask_wtf.file import FileField, FileAllowed, FileRequired

# Profile Forms
class ProfileChangeName(FlaskForm):
    username = StringField('Change Username', 
                            render_kw={"placeholder": "Username", "autocomplete": "off"},
                            validators=[DataRequired(), Length(min=3, max=40)])
    submit_change = SubmitField('Update')                            

class ProfileChangePassword(FlaskForm):
    password = PasswordField('New Password',
                            render_kw={"placeholder": "Password"}, 
                            validators=[DataRequired(), Length(min=3, max=20)])

    change_password = PasswordField('Confirm Password', 
                            render_kw={"placeholder": "Repeat Password"},
                            validators=[DataRequired(), EqualTo('password')])
    submit_change = SubmitField('Update')

class ProfileChangeEmail(FlaskForm):
    change_email = StringField('Change Email',
                        render_kw={"placeholder": "New Email", "autocomplete": "off"},
                        validators=[DataRequired(), Email("Email does not exist")])
    submit_change = SubmitField('Update')

class ProfileChangDescription(FlaskForm):
    about = TextAreaField('Description',
                        render_kw={"placeholder": "Quick Introduction..."},
                        validators=[DataRequired(), Length(min=1, max=250)]
                        )
    submit_change = SubmitField('Update')

# Product Forms
class ProductComment(FlaskForm):
    comment = TextAreaField('Comment',
                        render_kw={"placeholder": "Your thoughts...."},
                        validators=[DataRequired(), Length(min=1, max=250)]
                        )
    submit = SubmitField('Submit')

# Login/Register Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', render_kw={"autocomplete": "off"}, validators=[DataRequired(), Length(min=5, max=20)])

    email = StringField('Email', validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, message=('Password is too short'))])

    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

class ForgotForm(FlaskForm):
    username = StringField('Username', render_kw={"autocomplete": "off"}, validators=[DataRequired(), Length(min=5, max=20)])

    email = EmailField('Please Enter Your Email Address', validators=[DataRequired(), Email()])

    submit = SubmitField('Confirm')

class ForgotCode(FlaskForm):
    password = PasswordField('Please Enter Your Passcode', validators=[DataRequired(), Email()])

    submit = SubmitField('Confirm')

class ResetForm(FlaskForm):
    username = StringField('Enter Username', 
                            render_kw={"autocomplete": "off"},
                            validators=[Length(min=3, message=('Name is too short'))])
    
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=3, message=('Password is too short'))])

    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Reset Password')

class LoginForm(FlaskForm):
    username = StringField('Username', render_kw={"autocomplete": "off"}, validators=[DataRequired(), Length(min=5, max=20)])

    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)])
    
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')    

# Search Database Form
class SearchForm(FlaskForm):
    search = StringField('Search', render_kw={"placeholder": "Search", "autocomplete": "off"}, validators=[DataRequired()])
    
    submit = SubmitField('')

# Community Forms
class CreatePost(FlaskForm):
    text = TextAreaField('CREATE POST',
                        render_kw={"placeholder": "WRITE YOUR THOUGHTS HERE..."},
                        validators=[DataRequired(), Length(min=1)]
                        )
            
    title = StringField('Post Title',
                        render_kw={"placeholder": "ENTER TITLE..."},
                        validators=[DataRequired(), Length(min=1)])

    post = SubmitField('POST')

class ReplyForm(FlaskForm):
    replyText = TextAreaField('CREATE POST',
                        render_kw={"placeholder": "WRITE YOUR REPLY HERE..."},
                        validators=[DataRequired(), Length(min=1)]
                        )

    reply = SubmitField('REPLY')

class UploadForm(FlaskForm):
    title = StringField('Post Title',
                    render_kw={"placeholder": "ENTER TITLE..."},
                    validators=[DataRequired(), Length(min=1)])

    file = FileField('Upload', 
                    validators=[FileRequired(), FileAllowed(['jpg', 'jpeg' , 'png', 'gif'], 'Images only!')])

    post = SubmitField('POST')