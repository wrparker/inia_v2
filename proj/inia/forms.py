from django import forms
from captcha.fields import ReCaptchaField


class ContactForm(forms.Form):
    name = forms.CharField(label='Your Name', max_length=100)
    email = forms.EmailField(label='Your Email')
    comment = forms.CharField(widget=forms.Textarea(), label="Question/Comment:")
    captcha = ReCaptchaField()
